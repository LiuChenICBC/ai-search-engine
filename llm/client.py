"""OpenAI 兼容 LLM 客户端 - 使用同步 requests 避免 async 兼容问题"""

import json
import logging
import os
import re
from typing import Generator

import requests
import yaml

from config.constants import CLASSIFY_MAX_TOKENS, CLASSIFY_TIMEOUT, DEFAULT_LLM_TIMEOUT
from utils import retry_with_backoff

logger = logging.getLogger("www_search.llm")


class LLMClient:
    """OpenAI 兼容的 LLM 客户端，支持 Ollama / LM Studio / OpenAI
    使用同步 requests 库，避免 httpx async 与同步 HTTP 服务器的兼容问题。
    """

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        llm_cfg = cfg.get("llm", {})
        self.api_base = llm_cfg.get("api_base", "http://localhost:11434/v1")
        # API Key 优先级：环境变量 > 配置文件
        self.api_key = os.environ.get("WWW_SEARCH_LLM_API_KEY") or llm_cfg.get(
            "api_key", "ollama"
        )
        self.model = llm_cfg.get("model", "qwen3:8b")
        self.classify_model = llm_cfg.get("classify_model", self.model)
        self.temperature = llm_cfg.get("temperature", 0.3)
        self.max_tokens = llm_cfg.get("max_tokens", 4096)
        self.session = requests.Session()
        # 连接池配置：maxsize=最大连接数，block=是否阻塞等待空闲连接
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0,  # 重试由 retry_with_backoff 装饰器处理
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
        )

    def _extract_content(self, message: dict) -> str:
        """从消息中提取内容，优先 content，其次 reasoning_content"""
        content = message.get("content", "")
        if content:
            return content
        # 推理模型（如 Qwen3.6）的回答在 reasoning_content 里
        reasoning = message.get("reasoning_content", "")
        if reasoning:
            return reasoning
        return ""

    def _safe_extract(self, data: dict) -> dict:
        """安全提取 LLM 响应中的 message，处理空 choices 的情况"""
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("LLM 响应为空，无 choices 字段")
        return choices[0].get("message", {})

    @retry_with_backoff(max_retries=3, base_delay=1.0, logger=logger)
    def chat(
        self, messages: list[dict], model: str | None = None, stream: bool = False
    ) -> str:
        """发送聊天请求，返回完整文本"""
        resp = self.session.post(
            f"{self.api_base}/chat/completions",
            json={
                "model": model or self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": stream,
            },
            timeout=DEFAULT_LLM_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        message = self._safe_extract(data)
        return self._extract_content(message)

    def chat_stream(
        self, messages: list[dict], model: str | None = None
    ) -> Generator[str, None, None]:
        """流式聊天，yield 每个 chunk 的文本"""
        resp = self.session.post(
            f"{self.api_base}/chat/completions",
            json={
                "model": model or self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": True,
            },
            timeout=DEFAULT_LLM_TIMEOUT,
            stream=True,
        )
        resp.raise_for_status()
        try:
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        # 只取 content，不显示 reasoning_content（思考过程）
                        text = delta.get("content") or ""
                        if text:
                            yield text
                    except json.JSONDecodeError as e:
                        logger.warning(f"[llm] SSE JSON 解析失败: {e}")
        finally:
            resp.close()  # 确保 HTTP 连接释放

    @retry_with_backoff(max_retries=3, base_delay=1.0, logger=logger)
    def classify(self, query: str) -> dict:
        """分类问题，决定搜索策略"""
        prompt = f"""你是一个搜索策略分类器。分析用户的问题，决定如何搜索。

用户问题: {query}

请严格按以下 JSON 格式回答，不要输出其他内容:
{{
  "needs_research": true/false,
  "query_rewrite": "优化后的搜索查询词",
  "sources": ["web", "wikipedia"],
  "reason": "简短理由"
}}

规则:
- 事实性、新闻、技术、比较类问题: needs_research=true
- 简单问候、闲聊: needs_research=false
- **query_rewrite 必须用英文！** 即使用户用中文提问，也要翻译成英文搜索，因为搜索引擎对英文支持更好、结果更准确。
- **搜索查询要宽泛、简洁，不要过于具体：**
  - 搜索"2026年开源大模型"时，用 "2026 open source LLM models" 而不是 "2026 open source LLM under 140B parameters"
  - 把筛选条件（如参数量级、具体版本）留给 LLM 后续综合时过滤，搜索阶段先尽可能获取全面的信息
  - 查询词控制在 5-8 个单词以内，确保搜索引擎返回覆盖面广的结果
- sources 从以下选择: web, wikipedia, news, academic"""

        resp = self.session.post(
            f"{self.api_base}/chat/completions",
            json={
                "model": self.classify_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": CLASSIFY_MAX_TOKENS,
            },
            timeout=CLASSIFY_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        message = self._safe_extract(data)
        text = self._extract_content(message).strip()
        # 多层 fallback 提取 JSON：
        # 1. 直接解析
        # 2. 提取 markdown 代码块 ```json ... ```
        # 3. 找包含所有目标字段的 JSON 对象
        # 4. 非贪婪 regex
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 策略1: 提取 ```json ... ``` 或 ``` ... ``` 代码块
            bt3 = chr(96) * 3  # 三个反引号
            for match in re.finditer(
                re.escape(bt3) + r"(?:json)?\s*\n?([\s\S]*?)\n?" + re.escape(bt3), text
            ):
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue
            # 策略2: 从后往前找包含目标字段的最外层 JSON
            last_brace = text.rfind("}")
            if last_brace != -1:
                for start in range(last_brace, -1, -1):
                    if text[start] == "{":
                        candidate = text[start : last_brace + 1]
                        if '"needs_research"' in candidate:
                            try:
                                return json.loads(candidate.strip())
                            except json.JSONDecodeError:
                                break
            # 策略3: 非贪婪 regex — 提取包含 needs_research 的最外层 JSON
            match_result = re.search(
                r'(\{[\s\S]*?"needs_research"[\s\S]*?\})', text
            )
            if match_result:
                try:
                    return json.loads(match_result.group())
                except json.JSONDecodeError:
                    pass
            logger.warning(
                f"[llm] classify JSON 解析失败，使用默认值. raw={text[:300]}"
            )
            return {
                "needs_research": True,
                "query_rewrite": query,
                "sources": ["web"],
                "reason": "json_parse_failed",
            }
