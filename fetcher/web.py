"""网页内容抓取和文本提取 - 带重试 + 连接池 + URL 验证"""

import concurrent.futures
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config.constants import (
    FETCH_MAX_WORKERS,
    FETCH_PARALLEL_TIMEOUT,
    MAX_REDIRECTS,
    MIN_PARAGRAPH_LENGTH,
)
from utils import retry_with_backoff, validate_url

logger = logging.getLogger("www_search.fetcher")


@dataclass
class ExtractedContent:
    """提取的网页内容"""

    url: str
    title: str
    content: str  # 纯文本正文
    html: str  # 原始 HTML（可选）


# 全局 Session 池，复用连接
_session = requests.Session()
# 连接池配置：maxsize=最大连接数，block=是否阻塞等待空闲连接
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=0,  # 重试由 retry_with_backoff 装饰器处理
)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)
_session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
)


@retry_with_backoff(max_retries=2, base_delay=1.0, logger=logger)
def _fetch_url(url: str, timeout: float) -> str:
    """带重试的 URL 抓取，每次重定向前校验目标地址防 SSRF"""
    # SEC-C02: 请求前重新验证 URL，防止 DNS rebinding 攻击
    if not validate_url(url):
        raise requests.exceptions.HTTPError(f"URL 验证失败 (可能 DNS rebinding): {url}")
    resp = _session.get(url, timeout=timeout, allow_redirects=False)
    # 处理重定向链，每一步都校验 SSRF（最多 MAX_REDIRECTS 次重定向）
    for _ in range(MAX_REDIRECTS):
        if resp.status_code not in (301, 302, 303, 307, 308):
            break
        location = resp.headers.get("Location", "")
        if not location:
            break
        if not validate_url(location):
            raise requests.exceptions.HTTPError(f"重定向到不安全地址: {location}")
        resp = _session.get(location, timeout=timeout, allow_redirects=False)
    else:
        raise requests.exceptions.HTTPError(f"重定向过多 (>{MAX_REDIRECTS})")
    resp.raise_for_status()
    return resp.text


def extract_url(
    url: str, timeout: float = 15.0, max_length: int = 8000
) -> Optional[ExtractedContent]:
    """
    抓取网页并提取正文内容。
    使用 requests + BeautifulSoup 提取，去除导航/广告等噪音。
    """
    # URL 协议验证
    if not validate_url(url):
        return None

    try:
        html = _fetch_url(url, timeout)

        # Try multiple parsers for compatibility
        try:
            soup = BeautifulSoup(html, "lxml-html-clean")
        except Exception:
            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception:
                soup = BeautifulSoup(html, "html.parser")

        # 移除噪音元素
        for tag in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "noscript",
                "iframe",
            ]
        ):
            tag.decompose()

        # 提取标题
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        # 尝试用 Open Graph 信息补充
        if not title_text:
            og_title = soup.find("meta", property="og:title")
            if og_title:
                content_val = og_title.get("content", "")
                title_text = str(content_val) if content_val else ""

        # 提取正文 - 尝试多种策略
        content = ""

        # 策略1: 找 article/main 标签
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="article-content")
        )
        if article:
            content = article.get_text(separator="\n", strip=True)
        else:
            # 策略2: 取 body 文本，按段落分割
            body = soup.find("body")
            if body:
                paragraphs = body.find_all(
                    ["p", "h1", "h2", "h3", "h4", "li", "blockquote"]
                )
                text_parts = []
                for p in paragraphs:
                    t = p.get_text(strip=True)
                    if t and len(t) > MIN_PARAGRAPH_LENGTH:  # 过滤太短的片段
                        text_parts.append(t)
                content = "\n\n".join(text_parts)

        # 截断到最大长度
        if len(content) > max_length:
            content = content[:max_length] + "\n\n... (内容截断)"

        return ExtractedContent(
            url=url,
            title=title_text,
            content=content,
            html=html,
        )

    except Exception as e:
        logger.error(f"[fetcher] 抓取失败 {url}: {e}")
        return None


def extract_multiple(
    urls: list[str], timeout: float = 15.0, max_length: int = 8000
) -> list[ExtractedContent]:
    """并行抓取多个 URL（带超时）"""
    if not urls:
        return []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(len(urls), FETCH_MAX_WORKERS)
    ) as executor:
        ft_list = [
            (executor.submit(extract_url, url, timeout, max_length), url)
            for url in urls
        ]
        done, not_done = concurrent.futures.wait(
            [f for f, _ in ft_list],
            timeout=FETCH_PARALLEL_TIMEOUT,
            return_when=concurrent.futures.ALL_COMPLETED,
        )
        for f in not_done:
            logger.warning("[fetcher] 抓取超时已取消")
            f.cancel()
        results = []
        for future in done:
            try:
                r = future.result()
                if r is not None:
                    results.append(r)
            except concurrent.futures.CancelledError:
                # 超时取消的任务，静默跳过
                pass
            except Exception as e:
                logger.warning(f"[fetcher] 并行抓取任务异常: {e}")
    return results
