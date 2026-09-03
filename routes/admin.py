"""Admin 路由 - /admin/*"""

import asyncio
import hmac
import logging
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from db import (
    create_user, get_all_users, toggle_user, regenerate_key,
    get_usage_stats, get_global_stats, get_user,
)
from middleware import (
    login_required, get_admin_session, generate_csrf_token,
    _check_login_rate, _login_lock,
    _login_attempts, get_db_executor,
)
# 通过模块引用动态配置值，避免导入时拿到 None 的快照
import middleware as _middleware
from config.constants import MAX_USERNAME_LENGTH, MAX_USAGE_LIMIT, SESSION_COOKIE_MAX_AGE, SECURE_COOKIES

logger = logging.getLogger("www_search.routes.admin")


async def _run_db(func: Callable[..., Any], *args: Any) -> Any:
    """在 DB 线程池中执行同步数据库操作"""
    loop = asyncio.get_event_loop()
    executor = get_db_executor()
    return await loop.run_in_executor(executor, func, *args)


def _parse_flash_messages(request: Request) -> list[tuple[str, str]]:
    """从 URL ?flash=type:message 参数解析 flash message"""
    flash = request.query_params.get("flash", "")
    if not flash:
        return []
    parts = flash.split(":", 1)
    if len(parts) == 2:
        return [(parts[0], parts[1])]
    return []


def create_admin_routes(app: FastAPI, templates: Jinja2Templates) -> None:

    @app.get("/admin/login", response_class=HTMLResponse)
    async def admin_login(request: Request):
        """Admin 登录页面"""
        # 如果已登录，重定向到 dashboard
        session = get_admin_session(request)
        if session and session.get("logged_in"):
            return RedirectResponse(url="/admin", status_code=303)
        
        flash_messages = _parse_flash_messages(request)
        
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"flash_messages": flash_messages},
        )

    @app.post("/admin/login")
    async def admin_login_post(request: Request):
        """Admin 登录处理"""
        form = getattr(request.state, "parsed_form", None) or await request.form()
        password = form.get("password", "")
        
        # 检查登录速率限制
        client_ip = request.client.host if request.client else "127.0.0.1"
        if _check_login_rate(client_ip):
            logger.warning(f"登录尝试过多被限制: {client_ip}")
            return RedirectResponse(
                url=f"/admin/login?flash=error:登录尝试过多，请 5 分钟后再试",
                status_code=303,
            )
        
        if hmac.compare_digest(password, _middleware.ADMIN_PASSWORD):
            # 登录成功，清除尝试记录（加锁保证线程安全）
            with _login_lock:
                _login_attempts.pop(client_ip, None)
            
            # 创建 session（带过期时间）
            session_data = {"logged_in": True}
            session_cookie = _middleware.session_serializer.dumps(session_data)
            
            # 生成 CSRF token
            csrf_token = generate_csrf_token()
            
            response = RedirectResponse(url="/admin", status_code=303)
            response.set_cookie(
                key="admin_session",
                value=session_cookie,
                max_age=SESSION_COOKIE_MAX_AGE,
                httponly=True,
                samesite="lax",
                secure=SECURE_COOKIES,
            )
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                max_age=SESSION_COOKIE_MAX_AGE,
                httponly=True,
                samesite="lax",
                secure=SECURE_COOKIES,
            )
            logger.info("管理后台登录成功")
            return response
        else:
            logger.warning("管理后台登录失败：密码错误")
            return RedirectResponse(
                url="/admin/login?flash=error:密码错误，请重试",
                status_code=303,
            )

    @app.get("/admin/logout")
    async def admin_logout(request: Request):
        """Admin 登出"""
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie("admin_session")
        response.delete_cookie("csrf_token")
        return response

    @app.get("/admin", response_class=HTMLResponse)
    @login_required
    async def admin_dashboard(request: Request):
        """Admin 仪表盘"""
        stats = await _run_db(get_global_stats)
        users = await _run_db(get_all_users)
        csrf_token = request.cookies.get("csrf_token", "")

        flash_messages = _parse_flash_messages(request)

        return templates.TemplateResponse(
            request,
            "admin/dashboard.html",
            {"stats": stats, "users": users, "csrf_token": csrf_token, "flash_messages": flash_messages},
        )

    @app.get("/admin/users/create", response_class=HTMLResponse)
    @login_required
    async def admin_user_create_get(request: Request):
        """创建用户页面"""
        csrf_token = request.cookies.get("csrf_token", "")
        return templates.TemplateResponse(
            request,
            "admin/create_user.html",
            {"csrf_token": csrf_token, "new_key": None, "created": False},
        )

    @app.post("/admin/users/create", response_class=HTMLResponse)
    @login_required
    async def admin_user_create_post(request: Request):
        """创建用户处理"""
        form = getattr(request.state, "parsed_form", None) or await request.form()
        username = form.get("username", "").strip()

        if not username:
            return RedirectResponse(
                url="/admin/users/create?flash=error:用户名不能为空",
                status_code=303,
            )
        if len(username) > MAX_USERNAME_LENGTH:
            return RedirectResponse(
                url="/admin/users/create?flash=error:用户名不能超过 64 个字符",
                status_code=303,
            )
        if not all(c.isalnum() or c in ("_", "-") for c in username):
            return RedirectResponse(
                url="/admin/users/create?flash=error:用户名只能包含字母、数字、下划线和连字符",
                status_code=303,
            )

        try:
            user = await _run_db(create_user, username)
            csrf_token = request.cookies.get("csrf_token", "")
            return templates.TemplateResponse(
                request,
                "admin/create_user.html",
                {"csrf_token": csrf_token, "new_key": user, "created": True},
            )
        except ValueError as e:
            # 用户名已存在等已知错误
            logger.warning(f"创建用户失败 (ValueError): {e}")
            return RedirectResponse(
                url=f"/admin/users/create?flash=error:{e}",
                status_code=303,
            )
        except Exception as e:
            logger.error(f"创建用户失败: {e}", exc_info=True)
            return RedirectResponse(
                url="/admin/users/create?flash=error:创建失败，请重试",
                status_code=303,
            )

    @app.post("/admin/users/{user_id}/toggle")
    @login_required
    async def admin_user_toggle(request: Request, user_id: int):
        """启用/禁用用户"""
        try:
            user = await _run_db(toggle_user, user_id)
            status = "禁用" if not user["enabled"] else "启用"
            logger.info(f"用户 {user['username']}({user_id}) 已{status}")
        except ValueError as e:
            logger.error(f"切换用户状态失败: {e}")
            return RedirectResponse(url="/admin?flash=error:操作失败，用户不存在", status_code=303)

        return RedirectResponse(url="/admin", status_code=303)

    @app.post("/admin/users/{user_id}/regenerate", response_class=HTMLResponse)
    @login_required
    async def admin_user_regenerate(request: Request, user_id: int):
        """重新生成 API Key"""
        try:
            user = await _run_db(regenerate_key, user_id)
            logger.info(f"用户 {user['username']}({user_id}) 已重新生成 API Key")
            return templates.TemplateResponse(
                request,
                "admin/regenerate_key.html",
                {"user": user},
            )
        except ValueError as e:
            logger.error(f"重新生成 Key 失败: {e}")
            return RedirectResponse(
                url="/admin?flash=error:操作失败，请重试",
                status_code=303,
            )

    @app.get("/admin/users/{user_id}/usage", response_class=HTMLResponse)
    @login_required
    async def admin_user_usage(request: Request, user_id: int):
        """查看用户使用记录"""
        user = await _run_db(get_user, user_id)
        if not user:
            return RedirectResponse(
                url="/admin?flash=error:用户不存在",
                status_code=303,
            )

        records = await _run_db(get_usage_stats, user_id, MAX_USAGE_LIMIT)
        return templates.TemplateResponse(
            request,
            "admin/user_usage.html",
            {"user": user, "records": records},
        )

    @app.get("/admin/api/users")
    @login_required
    async def admin_api_users(request: Request):
        """API: 获取所有用户"""
        users = await _run_db(get_all_users)
        return {"users": users}

    @app.get("/admin/api/stats")
    @login_required
    async def admin_api_stats(request: Request):
        """API: 获取全局统计"""
        stats = await _run_db(get_global_stats)
        return stats
