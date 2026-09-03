"""公共工具模块 - 重试装饰器 + URL 校验 + 其他通用工具"""

import concurrent.futures
import functools
import ipaddress
import socket
import time
import logging
from urllib.parse import urlparse
from config.constants import DNS_RESOLVE_TIMEOUT


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, logger: logging.Logger | None = None):
    """带指数退避的重试装饰器工厂

    Args:
        max_retries: 最大重试次数（不包含首次尝试）
        base_delay: 基础延迟秒数
        logger: 日志记录器，默认为模块级 logger
    """
    log = logger or logging.getLogger(__name__)

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        log.warning(f"请求失败 (尝试 {attempt+1}/{max_retries+1}): {e}，{delay}s 后重试...")
                        time.sleep(delay)
                    else:
                        log.error(f"请求失败 (已重试 {max_retries} 次): {e}")
            raise last_exc
        return wrapper
    return decorator


def is_private_ip(ip_str: str) -> bool:
    """检查 IP 是否为内网/本地/保留地址"""
    try:
        ip = ipaddress.ip_address(ip_str)
        return not ip.is_global
    except ValueError:
        return True  # 无法解析视为不安全


def validate_url(url: str) -> bool:
    """验证 URL 协议安全 + SSRF 防护（禁止内网/localhost/保留地址）"""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    # 禁止本地回环
    if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        return False
    # DNS 解析后检查 IP 是否为内网地址（带超时保护，防止阻塞）
    try:
        _resolve_with_timeout(hostname)
    except socket.gaierror:
        return False
    except TimeoutError:
        return False
    return True


# REL-L02: 模块级单例线程池，避免每次调用都创建销毁
_dns_executor = None


def _get_dns_executor():
    """获取或创建 DNS 解析线程池（单例）"""
    global _dns_executor
    if _dns_executor is None:
        _dns_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="dns-resolve"
        )
    return _dns_executor


def _resolve_with_timeout(hostname: str, timeout: float = DNS_RESOLVE_TIMEOUT):
    """带超时的 DNS 解析，防止 getaddrinfo 无限阻塞"""
    executor = _get_dns_executor()
    future = executor.submit(socket.getaddrinfo, hostname, None)
    try:
        addr_info = future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        raise TimeoutError(f"DNS 解析超时: {hostname}")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        if is_private_ip(ip_str):
            raise socket.gaierror(f"内网地址: {ip_str}")


def normalize_url(url: str) -> str:
    """规范化 URL：小写 + 去除尾部斜杠，用于去重比较"""
    from urllib.parse import urlparse, urlunparse
    
    parsed = urlparse(url)
    # 域名小写，路径保留原样（URL 路径通常区分大小写）
    normalized = parsed._replace(netloc=parsed.netloc.lower())
    # 去除尾部斜杠（根路径除外）
    path = normalized.path.rstrip("/") if normalized.path != "/" else "/"
    normalized = normalized._replace(path=path)
    
    return urlunparse(normalized)
