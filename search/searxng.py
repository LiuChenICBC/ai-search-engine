"""SearXNG 搜索引擎 - 带重试 + 连接池 + SSRF 防护"""

import logging
import time
import requests
from .base import BaseSearchEngine, SearchResult

from utils import retry_with_backoff, validate_url

logger = logging.getLogger("www_search.searxng")


class SearXNGSearch(BaseSearchEngine):
    """SearXNG 元搜索引擎"""

    def __init__(self, base_url: str, engines: list[str] | None = None, timeout: float = 10.0):
        if not validate_url(base_url):
            raise ValueError(f"SearXNG base_url 不安全或无效: {base_url}")
        self.base_url = base_url.rstrip("/")
        self.engines = engines or ["google", "bing", "duckduckgo", "wikipedia"]
        self.timeout = timeout
        # 复用 Session
        self.session = requests.Session()
        # 连接池配置：maxsize=最大连接数，block=是否阻塞等待空闲连接
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0,  # 重试由 retry_with_backoff 装饰器处理
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @property
    def name(self) -> str:
        return "searxng"

    @retry_with_backoff(max_retries=2, base_delay=0.5, logger=logger)
    def search(self, query: str, max_results: int = 8) -> list[SearchResult]:
        """通过 SearXNG JSON API 搜索"""
        url = f"{self.base_url}/search"
        params = {
            "format": "json",
            "query": query,
            "engines": ",".join(self.engines),
            "categories": "general",
            "language": "all",
            "safesearch": 0,
            "pageno": 1,
        }

        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("results", [])[:max_results]:
            url = item.get("url", "")
            # COR-L03: 防御性校验 SearXNG 返回的 URL，防止恶意搜索结果绕过 SSRF
            if not validate_url(url):
                logger.warning(f"[searxng] 跳过不安全 URL: {url}")
                continue
            results.append(SearchResult(
                title=item.get("title", ""),
                url=url,
                snippet=item.get("content", ""),
                score=item.get("score", 0.0),
            ))

        return results
