"""搜索引擎工厂 - 自动选择可用的搜索后端"""

import logging
import os
import yaml
import concurrent.futures
from .base import BaseSearchEngine, SearchResult
from .searxng import SearXNGSearch
from .duckduckgo import DuckDuckGoSearch
from utils import retry_with_backoff, normalize_url
from config.constants import SEARCH_PARALLEL_TIMEOUT, DEFAULT_MAX_RESULTS

logger = logging.getLogger("www_search.search")


# 模块级引擎缓存：避免每次 search_all() 都重新加载配置
_engines_cache: list[BaseSearchEngine] | None = None
_config_mtime: float = 0.0


def _load_and_cache_engines(config_path: str) -> list[BaseSearchEngine]:
    """加载搜索引擎并缓存，配置文件变化时自动刷新"""
    global _engines_cache, _config_mtime
    try:
        current_mtime = os.path.getmtime(config_path)
    except OSError:
        current_mtime = 0

    if _engines_cache is not None and current_mtime == _config_mtime:
        return _engines_cache

    _engines_cache = load_search_engines(config_path)
    _config_mtime = current_mtime
    return _engines_cache


def load_search_engines(config_path: str = "config.yaml") -> list[BaseSearchEngine]:
    """从配置文件加载搜索引擎"""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    engines = []
    search_cfg = cfg.get("search", {})

    # 优先 SearXNG
    searxng_url = search_cfg.get("searxng_url", "")
    if searxng_url:
        engines.append(
            SearXNGSearch(
                base_url=searxng_url,
                engines=search_cfg.get(
                    "searxng_engines", ["google", "bing", "duckduckgo"]
                ),
            )
        )

    # DuckDuckGo 作为备选
    if search_cfg.get("use_ddgs", True):
        engines.append(DuckDuckGoSearch())

    return engines


def search_all(
    query: str, max_results: int = DEFAULT_MAX_RESULTS, config_path: str = "config.yaml"
) -> list[SearchResult]:
    """并行搜索所有可用引擎，合并去重"""
    engines = _load_and_cache_engines(config_path)
    if not engines:
        # 默认 DuckDuckGo
        engines = [DuckDuckGoSearch()]

    logger.info(
        f"[search] 搜索 query='{query}', max_results={max_results}, engines={[e.name for e in engines]}"
    )

    # 并行搜索（带超时）- 使用 utils.retry_with_backoff 统一重试逻辑
    all_results = []
    failed_engines = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(engines)) as executor:
        ft_map = {
            executor.submit(
                retry_with_backoff(max_retries=2, base_delay=0.5, logger=logger)(
                    engine.search
                ),
                query,
                max_results,
            ): engine
            for engine in engines
        }
        done, not_done = concurrent.futures.wait(
            ft_map,
            timeout=SEARCH_PARALLEL_TIMEOUT,
            return_when=concurrent.futures.ALL_COMPLETED,
        )
        for f in not_done:
            logger.warning(f"[search] 引擎搜索超时已取消")
            f.cancel()
        for future in done:
            engine = ft_map[future]
            try:
                results = future.result()
                all_results.append(results)
                logger.info(f"[search] {engine.name} 返回 {len(results)} 条结果")
            except Exception as e:
                logger.warning(f"引擎 {engine.name} 搜索失败: {e}")
                failed_engines.append(engine.name)

    if failed_engines:
        logger.warning(f"以下引擎搜索失败: {', '.join(failed_engines)}，使用剩余结果")

    # 合并去重（按 URL）- 规范化 URL 处理大小写和尾部斜杠
    seen = set()
    merged = []
    for results in all_results:
        for r in results:
            if r.url and normalize_url(r.url) not in seen:
                seen.add(normalize_url(r.url))
                merged.append(r)
            if len(merged) >= max_results:
                break
        if len(merged) >= max_results:
            break

    result = merged[:max_results]

    # 所有引擎都失败时告警
    if not result and failed_engines:
        logger.error(f"[search] 所有搜索引擎均失败: {', '.join(failed_engines)}")
    elif not result:
        logger.warning(f"[search] 搜索 query='{query}' 未找到任何结果")
    else:
        logger.info(f"[search] 最终返回 {len(result)} 条去重结果")

    return result
