"""Research Agent - 编排搜索、抓取、LLM 综合"""

import logging
from dataclasses import dataclass, field
from typing import Generator

import yaml

from config.constants import (
    DEFAULT_FETCH_TIMEOUT,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_SCRAPE,
    MAX_CONTENT_LENGTH,
    SOURCE_SNIPPET_LENGTH,
)
from fetcher.web import ExtractedContent, extract_multiple
from llm.client import LLMClient
from search import search_all
from search.base import SearchResult
from utils import validate_url

logger = logging.getLogger("www_search.research")


@dataclass
class ResearchResult:
    """研究结果"""

    answer: str
    sources: list[dict] = field(default_factory=list)  # [{"title", "url", "snippet"}]
    search_results: list[SearchResult] = field(default_factory=list)
    scraped_content: list[ExtractedContent] = field(default_factory=list)


class ResearchAgent:
    """
    Perplexica 风格的研究代理:
    1. 分类问题
    2. 搜索
    3. 抓取 Top 结果
    4. LLM 综合生成回答 + 引用
    """

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.config_path = config_path
        self.llm = LLMClient(config_path)
        self.search_cfg = self.config.get("search", {})
        self.fetcher_cfg = self.config.get("fetcher", {})

    def _build_context_and_prompt(
        self,
        query: str,
        search_results: list[SearchResult],
        scraped: list[ExtractedContent],
    ) -> list[dict]:
        """构建搜索上下文和 prompt（消除 _synthesize 和 _synthesize_stream 的代码重复）"""
        context_parts = []
        scraped_urls = {sc.url for sc in scraped}

        # 先添加成功抓取的页面内容
        for i, sc in enumerate(scraped):
            context_parts.append(
                f"[来源 {i + 1}] {sc.title}\nURL: {sc.url}\n{sc.content}"
            )

        # 对于抓取失败的搜索结果，用摘要作为 fallback
        fallback_idx = len(scraped) + 1
        for r in search_results:
            if r.url not in scraped_urls and r.snippet:
                context_parts.append(
                    f"[来源 {fallback_idx}] {r.title}\nURL: {r.url}\n{r.snippet}"
                )
                fallback_idx += 1

        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""你是一个智能研究助手。根据以下搜索结果，回答用户的问题。

用户问题: {query}

搜索结果:
{context}

要求:
1. 用中文回答（用户用英文问就用英文）
2. **回答要全面、详尽，不要遗漏搜索结果中提到的关键信息：**
   - 如果用户要求列举/查找多个项目（如模型、工具、产品），列出搜索结果中提到的**所有**符合条件的项，不要只挑几个
   - 使用表格或列表形式清晰展示，包含关键参数（如参数量、发布时间、厂商等）
   - 如果搜索结果中某些项信息不完整（如参数未知），也要列出并标注"未知"
3. 在回答中使用 [1], [2] 等标记引用来源
4. 只引用实际提供的搜索结果
5. 如果搜索结果不足以回答问题，诚实地说明
6. 回答末尾附上完整的来源列表

格式:
## 回答
（你的回答，使用 Markdown 格式，包含引用标记。如果是列举类问题，优先使用表格展示）

## 来源
1. [标题](URL)
2. ..."""

        return [
            {
                "role": "system",
                "content": "你是一个专业的研究助手，擅长综合多源信息给出准确回答。",
            },
            {"role": "user", "content": prompt},
        ]

    def _build_sources(
        self, search_results: list[SearchResult], scraped: list[ExtractedContent]
    ) -> list[dict]:
        """构建 sources 列表"""
        sources = []
        for r in search_results[: len(scraped)]:
            sources.append(
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet[:SOURCE_SNIPPET_LENGTH],
                }
            )
        return sources

    def research(self, query: str) -> ResearchResult:
        """执行完整的研究流程"""
        # 1. 分类（失败则使用原始查询）
        try:
            classification = self.llm.classify(query)
            logger.info(f"[research] 分类结果: {classification}")
        except Exception as e:
            logger.warning(f"问题分类失败，使用原始查询: {e}")
            classification = {}

        # 2. 搜索
        search_query = classification.get("query_rewrite", query) or query
        if search_query != query:
            logger.info(f"[research] 原始查询: '{query}' → 改写后: '{search_query}'")
        search_results = search_all(
            search_query,
            max_results=self.search_cfg.get("max_results", DEFAULT_MAX_RESULTS),
            config_path=self.config_path,
        )

        # 3. 并行抓取 Top 结果（SEC-C04: 过滤不安全 URL）
        urls_to_scrape = [
            r.url
            for r in search_results[
                : self.search_cfg.get("max_scrape", DEFAULT_MAX_SCRAPE)
            ]
            if validate_url(r.url)
        ]
        scraped = extract_multiple(
            urls_to_scrape,
            timeout=self.fetcher_cfg.get("timeout", DEFAULT_FETCH_TIMEOUT),
            max_length=self.fetcher_cfg.get("max_content_length", MAX_CONTENT_LENGTH),
        )

        # 4. 综合生成回答
        answer = self._synthesize(query, search_results, scraped)

        return ResearchResult(
            answer=answer,
            sources=self._build_sources(search_results, scraped),
            search_results=search_results,
            scraped_content=scraped,
        )

    def research_stream(self, query: str) -> Generator[dict, None, None]:
        """流式研究 - 先 yield 搜索状态，最后 yield 回答和 sources"""
        # 1. 分类（失败则使用原始查询）
        yield {"type": "status", "text": "🔍 分析问题..."}

        try:
            classification = self.llm.classify(query)
            logger.info(f"[research_stream] 分类结果: {classification}")
        except Exception as e:
            logger.warning(f"问题分类失败，使用原始查询: {e}")
            classification = {}

        # 2. 搜索
        search_query = classification.get("query_rewrite", query) or query
        if search_query != query:
            logger.info(
                f"[research_stream] 原始查询: '{query}' → 改写后: '{search_query}'"
            )
        yield {"type": "status", "text": f"🌐 搜索: {search_query}"}

        search_results = search_all(
            search_query,
            max_results=self.search_cfg.get("max_results", DEFAULT_MAX_RESULTS),
            config_path=self.config_path,
        )

        yield {"type": "status", "text": f"✅ 找到 {len(search_results)} 个结果"}

        # 3. 并行抓取（SEC-C04: 过滤不安全 URL）
        urls_to_scrape = [
            r.url
            for r in search_results[
                : self.search_cfg.get("max_scrape", DEFAULT_MAX_SCRAPE)
            ]
            if validate_url(r.url)
        ]
        yield {"type": "status", "text": f"📄 抓取 {len(urls_to_scrape)} 个页面..."}

        scraped = extract_multiple(
            urls_to_scrape,
            timeout=self.fetcher_cfg.get("timeout", DEFAULT_FETCH_TIMEOUT),
            max_length=self.fetcher_cfg.get("max_content_length", MAX_CONTENT_LENGTH),
        )

        yield {"type": "status", "text": "✍️ 综合信息中..."}

        # 4. 流式生成回答
        try:
            for chunk in self._synthesize_stream(query, search_results, scraped):
                yield {"type": "answer_chunk", "text": chunk}
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            yield {"type": "status", "text": f"❌ 生成失败: {e}"}
        finally:
            # 5. 无论成功失败都返回 sources 和 done
            sources = self._build_sources(search_results, scraped)
            yield {"type": "sources", "sources": sources}
            yield {"type": "done"}

    def _synthesize(
        self,
        query: str,
        search_results: list[SearchResult],
        scraped: list[ExtractedContent],
    ) -> str:
        """综合搜索结果生成回答"""
        messages = self._build_context_and_prompt(query, search_results, scraped)
        return self.llm.chat(messages)

    def _synthesize_stream(
        self,
        query: str,
        search_results: list[SearchResult],
        scraped: list[ExtractedContent],
    ) -> Generator[str, None, None]:
        """流式综合生成回答"""
        messages = self._build_context_and_prompt(query, search_results, scraped)
        for chunk in self.llm.chat_stream(messages):
            yield chunk
