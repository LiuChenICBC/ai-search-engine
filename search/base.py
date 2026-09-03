"""搜索基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """搜索结果"""

    title: str
    url: str
    snippet: str
    score: float = 0.0  # 相关性分数


class BaseSearchEngine(ABC):
    """搜索引擎基类"""

    @abstractmethod
    def search(self, query: str, max_results: int = 8) -> list[SearchResult]:
        """执行搜索"""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        ...
