"""中间件模块 - API Key 认证、CSRF 保护、安全响应头"""

import asyncio
import hmac
import logging
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable

import itsdangerous

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse as StarletteJSONResponse
from starlette.datastructures import URL

from db import verify_api_key, record_usage
from config.constants import (
    SESSION_MAX_AGE as _SESSION_MAX_AGE_CONST,
    MAX_LOGIN_ATTEMPTS,
    LOGIN_WINDOW_SECONDS,
    MAX_LOGIN_TRACKED_IPS,
    CONTENT_SECURITY_POLICY,
    X_FRAME_OPTIONS,
    HSTS_MAX_AGE,
    REFERRER_POLICY,
    MAX_REQUEST_BODY_SIZE,
)

logger = logging.getLogger("www_search.middleware")


# ==================== 全局状态 ====================

# 线程池：用于在 async 中间件/路由中执行同步 DB 操作
_db_executor = None  # 在 main.py 中初始化


def get_db_executor() -> "ThreadPoolExecutor":
    """获取 DB 线程池"""
    if _db_executor is None:
        raise RuntimeError("DB executor not initialized")
    return _db_executor


def set_db_executor(executor: "ThreadPoolExecutor") -> None:
    """设置 DB 线程池"""
    global _db_executor
    _db_executor = executor


# ==================== Admin 配置 ====================

ADMIN_PASSWORD = None
SECRET_KEY = None
session_serializer = None
_SESSION_MAX_AGE = _SESSION_MAX_AGE_CONST

# 登录速率限制
_login_attempts: dict[str, list[float]] = {}
_login_lock = threading.Lock()


def init_admin_config():
    """初始化 admin 配置（必须在启动时调用）"""
    global ADMIN_PASSWORD, SECRET_KEY, session_serializer

    ADMIN_PASSWORD = os.environ.get("WWW_SEARCH_ADMIN_PASSWORD")
    if not ADMIN_PASSWORD:
        raise RuntimeError(
            "必须设置环境变量 WWW_SEARCH_ADMIN_PASSWORD 指定管理后台密码\n"
            "   export WWW_SEARCH_ADMIN_PASSWORD='your-strong-password-here'"
        )

    SECRET_KEY = os.environ.get("WWW_SEARCH_SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "必须设置环境变量 WWW_SEARCH_SECRET_KEY 指定 session 签名密钥\n"
            "   生成: python3 -c 'import secrets; print(secrets.token_hex(32))'"
        )

    session_serializer = itsdangerous.URLSafeTimedSerializer(
        SECRET_KEY, salt="www_search-session"
    )


# ==================== Admin Session 工具 ====================


def generate_csrf_token() -> str:
    """生成 CSRF token"""
    return os.urandom(32).hex()


def validate_csrf_token(session_token: str, form_token: str) -> bool:
    """验证 CSRF token"""
    if not session_token or not form_token:
        return False
    return hmac.compare_digest(session_token, form_token)


def get_admin_session(request: Request) -> dict | None:
    """从签名 cookie 中获取 admin session"""
    session_cookie = request.cookies.get("admin_session")
    if not session_cookie:
        return None
    try:
        return session_serializer.loads(session_cookie, max_age=_SESSION_MAX_AGE)
    except (itsdangerous.BadSignature, itsdangerous.SignatureExpired, ValueError):
        return None


def login_required(endpoint: Callable[..., Any]) -> Callable[..., Any]:
    """装饰器：要求已登录 admin"""

    @wraps(endpoint)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request") or args[0]
        session = get_admin_session(request)
        if not session or not session.get("logged_in"):
            return RedirectResponse(url="/admin/login", status_code=303)
        return await endpoint(*args, **kwargs)

    return wrapper


def _check_login_rate(ip: str) -> bool:
    """检查 IP 是否超过登录尝试限制，返回 True 表示被限制"""
    now = time.time()
    with _login_lock:
        # 清理过期条目（如果太多则淘汰最老的）
        while len(_login_attempts) > MAX_LOGIN_TRACKED_IPS:
            oldest_ip = next(iter(_login_attempts))
            del _login_attempts[oldest_ip]

        # 过滤当前时间窗口内的尝试记录
        attempts = [
            t for t in _login_attempts.get(ip, []) if now - t < LOGIN_WINDOW_SECONDS
        ]

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            _login_attempts[ip] = attempts
            return True

        attempts.append(now)
        if attempts:
            _login_attempts[ip] = attempts
    return False


# ==================== API Key 中间件 ====================


async def _record_usage_async(user_id: int, query: str, tokens_used: int):
    """异步记录使用量（fire-and-forget）"""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            get_db_executor(), record_usage, user_id, query, tokens_used
        )
    except Exception as e:
        logger.warning(f"[middleware] 记录使用量失败: {e}")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 跳过认证的路由（Web UI + 健康检查 + 静态资源）
        if path == "/" or path == "/api/health":
            return await call_next(request)
        if path.startswith("/static/") or path == "/static":
            return await call_next(request)
        if path.startswith("/admin"):
            return await call_next(request)

        # 需要认证的路由
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning(f"401 {request.method} {request.url.path} - 缺少 API Key")
            return StarletteJSONResponse(
                status_code=401,
                content={
                    "error": "Missing API Key",
                    "message": "请在请求头中添加 X-API-Key",
                },
            )

        # 验证 API Key
        loop = asyncio.get_event_loop()
        user = await loop.run_in_executor(get_db_executor(), verify_api_key, api_key)
        if not user:
            logger.warning(f"401 {request.method} {request.url.path} - 无效 API Key")
            return StarletteJSONResponse(
                status_code=401,
                content={"error": "Invalid or disabled API Key"},
            )

        request.state.user = user
        response = await call_next(request)

        # 记录使用量（fire-and-forget）
        tokens_used = int(response.headers.get("X-Tokens-Used", 0))
        if tokens_used > 0:
            asyncio.create_task(_record_usage_async(user["id"], "", tokens_used))

        return response


# ==================== CSRF 中间件 ====================


class AdminCSRFMiddleware(BaseHTTPMiddleware):
    """Admin POST 请求的 CSRF 验证"""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/admin") and request.method == "POST":
            if request.url.path == "/admin/login":
                return await call_next(request)

            session_token = request.cookies.get("csrf_token", "")
            try:
                form = await request.form()
            except Exception:
                logger.warning(
                    f"CSRF 验证失败 - 无法解析表单: {request.method} {request.url.path}"
                )
                return RedirectResponse(
                    url="/admin?flash=error:请求格式错误", status_code=303
                )

            form_token = form.get("csrf_token", "")

            if not validate_csrf_token(session_token, form_token):
                logger.warning(f"CSRF 验证失败: {request.method} {request.url.path}")
                response = RedirectResponse(url="/admin", status_code=303)
                response.url = str(
                    URL("/admin?flash=error:安全验证失败，请刷新页面重试")
                )
                return response

            # 将已解析的 form 存到 request.state，避免路由 handler 重复消费 body
            request.state.parsed_form = form

        response = await call_next(request)
        return response


# ==================== 安全响应头中间件 ====================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = X_FRAME_OPTIONS
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        response.headers["Referrer-Policy"] = REFERRER_POLICY
        # HSTS: 强制 HTTPS（生产环境启用，max-age=30天）
        response.headers["Strict-Transport-Security"] = HSTS_MAX_AGE
        return response


# ==================== 请求大小限制中间件 ====================


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """限制请求体大小，防止超大 body 攻击"""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
            logger.warning(
                f"请求体过大被拒绝: {request.method} {request.url.path} "
                f"(size={content_length}, max={MAX_REQUEST_BODY_SIZE})"
            )
            return StarletteJSONResponse(
                status_code=413,
                content={
                    "error": "Payload Too Large",
                    "message": "请求体过大，最大 1MB",
                },
            )

        response = await call_next(request)
        return response


# 注意：init_admin_config() 不再在模块加载时自动调用。
# 由 main.py lifespan 或测试代码显式调用，避免 import 时崩溃。
