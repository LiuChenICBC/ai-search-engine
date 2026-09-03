"""DuckDuckGo 搜索引擎（备选）"""

import logging
from ddgs import DDGS
from .base import BaseSearchEngine, SearchResult

logger = logging.getLogger("www_search.ddgs")


class DuckDuckGoSearch(BaseSearchEngine):
    """DuckDuckGo 搜索（无需 API key）"""

    @property
    def name(self) -> str:
        return "duckduckgo"

    def search(self, query: str, max_results: int = 8) -> list[SearchResult]:
        """通过 ddgs 库搜索（带超时保护）"""
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results, timeout=30):
                    results.append(
                        SearchResult(
                            title=r.get("title", ""),
                            url=r.get("href", ""),
                            snippet=r.get("body", ""),
                            score=0.0,
                        )
                    )
        except Exception as e:
            logger.error(f"[ddgs] 搜索失败: {e}")
        return results
