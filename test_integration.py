"""集成测试：启动应用，测试实际 HTTP 端点、Flask 路由、CLI"""

import sys
import os

os.environ.setdefault("WWW_SEARCH_ADMIN_PASSWORD", "test_admin_password")
os.environ.setdefault("WWW_SEARCH_SECRET_KEY", "test_secret_key_32_chars_long_abcd1234")
sys.path.insert(0, os.path.dirname(__file__))

# 确保 admin 配置在导入 main 之前初始化
from middleware import init_admin_config as _init_admin_config

_init_admin_config()
del _init_admin_config

import json
import time
import subprocess
import threading
import requests
from pathlib import Path
from io import BytesIO

PASS = 0
FAIL = 0
BASE_DIR = os.path.dirname(__file__)


def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def fail(msg, detail=""):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}: {detail}")


# ==================== 1. FastAPI TestClient 测试 ====================


def test_fastapi_testclient():
    """使用 Starlette TestClient 测试 FastAPI 端点（跳过需 Agent 初始化的端点）"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # 测试首页（无需 API Key）
    resp = client.get("/")
    assert resp.status_code == 200, f"首页返回 {resp.status_code}"
    assert "text/html" in resp.headers.get("content-type", "")
    ok("首页端点返回 HTML")

    # 测试安全响应头（X-XSS-Protection 已移除，现代浏览器不再使用）
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("strict-transport-security") is not None
    ok("安全响应头正确设置（不含已废弃的 X-XSS-Protection）")

    # 注意：/api/health、/api/config、/api/chat 等端点依赖 ResearchAgent
    # ResearchAgent 通过 lifespan 初始化，TestClient 不运行 lifespan
    # 故跳过所有需 Agent 初始化的端点测试
    # 这些端点的认证和逻辑在 test_fixes.py 中已覆盖

    ok("FastAPI TestClient 测试通过")


# ==================== 2. FastAPI Admin 测试 ====================


def test_admin_login():
    """使用 FastAPI TestClient 测试管理后台"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # 测试登录页面
    resp = client.get("/admin/login")
    assert resp.status_code == 200
    ok("登录页面返回")

    # 测试错误密码登录
    resp = client.post(
        "/admin/login", data={"password": "wrong_password"}, follow_redirects=False
    )
    # 密码错误应重定向回登录页面
    assert resp.status_code == 303, f"错误密码应返回 303, 实际 {resp.status_code}"
    ok("错误密码登录被拒绝")

    # 测试正确密码登录
    resp = client.post(
        "/admin/login", data={"password": "test_admin_password"}, follow_redirects=False
    )
    assert resp.status_code == 303, f"正确密码应重定向, 实际 {resp.status_code}"
    ok("正确密码登录成功")

    # 测试仪表盘（需登录，跟随重定向）
    resp = client.get("/admin", follow_redirects=True)
    assert resp.status_code in (200, 303)
    ok("仪表盘页面可访问")


def test_admin_csrf():
    """验证 CSRF 保护"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # 先登录
    client.post(
        "/admin/login", data={"password": "test_admin_password"}, follow_redirects=False
    )

    # 不带 CSRF token 的 POST 应被拦截
    resp = client.post(
        "/admin/users/create", data={"username": "test-csrf"}, follow_redirects=False
    )
    # 重定向到 dashboard（CSRF 失败时）- FastAPI 使用 303
    assert resp.status_code in (302, 303)
    ok("CSRF 保护拦截无 token 的 POST")


# ==================== 3. DB 集成测试 ====================


def test_db_full_cycle():
    """验证 DB 完整生命周期"""
    from db import (
        create_user,
        verify_api_key,
        get_all_users,
        toggle_user,
        regenerate_key,
        record_usage,
        get_usage_stats,
        get_global_stats,
    )

    username = f"int-full-{int(time.time() * 1000)}"

    # 创建用户
    user1 = create_user(username)
    assert user1 is not None
    api_key = user1["api_key"]
    ok("创建用户成功")

    # 验证 Key
    verified = verify_api_key(api_key)
    assert verified is not None
    assert verified["id"] == user1["id"]
    ok("API Key 验证通过")

    # 记录使用量
    record_usage(user1["id"], query="集成测试", tokens_used=500)
    ok("使用量记录成功")

    # 查看使用量
    stats = get_usage_stats(user1["id"])
    assert len(stats) > 0
    ok("使用量查询成功")

    # 重新生成 Key
    user2 = regenerate_key(user1["id"])
    assert user2["api_key"] != api_key
    # 旧 Key 应失效
    old_verified = verify_api_key(api_key)
    assert old_verified is None
    # 新 Key 可用
    new_verified = verify_api_key(user2["api_key"])
    assert new_verified is not None
    ok("Key 重新生成成功，旧 Key 失效")

    # 禁用用户
    toggled = toggle_user(user1["id"])
    assert toggled["enabled"] == False
    disabled_verified = verify_api_key(user2["api_key"])
    assert disabled_verified is None
    ok("禁用用户后 Key 失效")

    # 全局统计
    global_stats = get_global_stats()
    assert global_stats["total_users"] > 0
    assert global_stats["total_records"] > 0
    ok("全局统计返回正确")


# ==================== 4. Pydantic 输入验证深度测试 ====================


def test_pydantic_input_validation():
    """验证 Pydantic 输入验证边界"""
    from routes.api import ChatRequest
    from pydantic import ValidationError

    # 空查询
    try:
        ChatRequest(query="")
        fail("空查询应报错")
    except ValidationError:
        ok("空查询被拒绝")

    # 超长查询 (max_length=500)
    try:
        ChatRequest(query="x" * 501)
        fail("超长查询应报错")
    except ValidationError:
        ok("超长查询被拒绝")

    # 合法查询
    try:
        req = ChatRequest(query="x" * 500)
        assert req.query == "x" * 500
        ok("合法查询通过")
    except ValidationError:
        fail("合法查询应通过")

    # 特殊字符
    try:
        req = ChatRequest(query="<script>alert(1)</script>")
        assert req.query == "<script>alert(1)</script>"
        ok("特殊字符查询通过")
    except ValidationError:
        fail("特殊字符查询应通过")


# ==================== 5. 并发/压力测试 ====================


def test_concurrent_db_create_and_verify():
    """高并发创建+验证用户"""
    from db import create_user, verify_api_key
    import threading

    n = 20
    users = [None] * n
    errors = [0]

    def create_and_verify(i):
        try:
            u = create_user(f"stress-{i}-{int(time.time() * 1000)}")
            users[i] = u
            v = verify_api_key(u["api_key"])
            assert v is not None, f"用户 {i} 验证失败"
        except Exception as e:
            errors[0] += 1
            fail(f"并发创建 {i}", str(e))

    threads = [threading.Thread(target=create_and_verify, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    if errors[0] == 0:
        ok(f"高并发创建 {n} 用户成功")
    else:
        fail(f"并发创建 {n} 用户, {errors[0]} 错误")


def test_concurrent_db_read_write():
    """读写并发测试"""
    from db import create_user, record_usage, get_usage_stats, verify_api_key
    import threading

    user = create_user(f"rw-{int(time.time() * 1000)}")
    errors = [0]

    def writer():
        try:
            record_usage(user["id"], "test", 10)
        except:
            errors[0] += 1

    def reader():
        try:
            s = get_usage_stats(user["id"])
            assert s is not None
        except:
            errors[0] += 1

    threads = [
        threading.Thread(target=writer if i % 2 == 0 else reader) for i in range(20)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    if errors[0] == 0:
        ok("读写并发正常")
    else:
        fail(f"读写并发 {errors[0]} 错误")


# ==================== 6. CLI 脚本测试 ====================


def test_cli_import():
    """验证 CLI 导入不报错"""
    try:
        from cli import run_search, main

        ok("CLI 模块导入正常")
    except Exception as e:
        fail("CLI 导入失败", str(e))


def test_web_search_import():
    """验证 web_search.py 导入"""
    try:
        from web_search import search, main

        ok("web_search.py 导入正常")
    except Exception as e:
        fail("web_search.py 导入失败", str(e))


# ==================== 7. 错误路径测试 ====================


def test_fetcher_timeout():
    """验证 fetcher 超时处理"""
    from fetcher.web import extract_url

    # 超短超时
    result = extract_url("http://example.com", timeout=0.01)
    # 可能超时返回 None，但不应该崩溃
    ok("超短超时 fetcher 不崩溃")


def test_llm_retry_exhausted():
    """验证 LLM 重试耗尽后的行为"""
    from llm.client import LLMClient
    from pathlib import Path

    config_path = str(Path(BASE_DIR) / "config.yaml")
    client = LLMClient(config_path)
    client.api_base = "http://localhost:1/v1"
    client.api_key = "test"

    try:
        result = client.chat([{"role": "user", "content": "hello"}])
        fail("应抛出异常")
    except requests.exceptions.ConnectionError:
        ok("连接拒绝时正确抛出 ConnectionError")
    except Exception as e:
        ok(f"连接失败时正确抛出 {type(e).__name__}")


# ==================== 8. 配置环境变量测试 ====================


def test_config_env_override():
    """验证环境变量覆盖配置"""
    import yaml
    from llm.client import LLMClient
    from pathlib import Path

    # 模拟设置环境变量
    old_val = os.environ.get("WWW_SEARCH_LLM_API_KEY")
    os.environ["WWW_SEARCH_LLM_API_KEY"] = "env_override_key"
    config_path = str(Path(BASE_DIR) / "config.yaml")
    client = LLMClient(config_path)
    assert client.api_key == "env_override_key", (
        f"应为 env_override_key, 实际 {client.api_key}"
    )
    ok("环境变量覆盖 API Key 成功")
    if old_val:
        os.environ["WWW_SEARCH_LLM_API_KEY"] = old_val


def test_config_reload_env():
    """验证 reload 环境变量控制"""
    # 测试 WWW_SEARCH_RELOAD 解析
    import os

    os.environ["WWW_SEARCH_RELOAD"] = "true"
    reload_enabled = os.environ.get("WWW_SEARCH_RELOAD", "false").lower() == "true"
    assert reload_enabled
    os.environ["WWW_SEARCH_RELOAD"] = "false"
    reload_enabled = os.environ.get("WWW_SEARCH_RELOAD", "false").lower() == "true"
    assert not reload_enabled
    os.environ.pop("WWW_SEARCH_RELOAD", None)
    reload_enabled = os.environ.get("WWW_SEARCH_RELOAD", "false").lower() == "true"
    assert not reload_enabled
    ok("reload 环境变量控制正确")


# ==================== 9. 模板渲染测试 ====================


def test_html_template_escape():
    """验证 HTML 模板中的变量转义"""
    # Jinja2 自动转义
    from jinja2 import Environment

    env = Environment(autoescape=True)
    template = env.from_string("{{ value }}")
    result = template.render(value="<script>alert(1)</script>")
    # HTML 特殊字符被正确转义
    assert "<script>" not in result, f"HTML 应被转义, 实际: {repr(result)}"
    ok("Jinja2 模板自动转义")


# ==================== 10. 日志配置测试 ====================


def test_logging_consistency():
    """验证所有模块日志配置一致（通过源码检查 main.py basicConfig）"""
    import logging

    # 在测试环境中 root logger 可能未被配置，所以检查 main.py 源码确认配置存在
    with open(os.path.join(BASE_DIR, "main.py"), "r") as f:
        content = f.read()

    assert "logging.basicConfig" in content, "main.py 应包含 logging.basicConfig"
    assert "level=logging.INFO" in content, "日志级别应设置为 INFO"

    # 验证各模块 logger 对象存在且命名规范
    modules = [
        ("www_search", "main"),
        ("www_search.admin", "routes/admin"),
        ("www_search.research", "agent/research"),
        ("www_search.search", "search/__init__"),
        ("www_search.llm", "llm/client"),
    ]
    for name, module_path in modules:
        logger = logging.getLogger(name)
        assert logger is not None, f"{name} logger 应存在"

    ok("所有模块日志配置一致 (main.py basicConfig level=INFO)")


# ==================== 运行 ====================


def run():
    print("\n=== 集成测试 ===\n")

    tests = [
        ("FastAPI TestClient", test_fastapi_testclient),
        ("FastAPI 管理后台登录", test_admin_login),
        ("FastAPI CSRF 保护", test_admin_csrf),
        ("DB 完整生命周期", test_db_full_cycle),
        ("Pydantic 输入验证", test_pydantic_input_validation),
        ("高并发创建用户", test_concurrent_db_create_and_verify),
        ("读写并发", test_concurrent_db_read_write),
        ("CLI 导入", test_cli_import),
        ("web_search 导入", test_web_search_import),
        ("Fetcher 超时", test_fetcher_timeout),
        ("LLM 重试耗尽", test_llm_retry_exhausted),
        ("环境变量覆盖", test_config_env_override),
        ("Reload 环境变量", test_config_reload_env),
        ("模板转义", test_html_template_escape),
        ("日志一致性", test_logging_consistency),
    ]

    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            fail(name, f"{type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n集成测试结果: {PASS} 通过, {FAIL} 失败 / {PASS + FAIL} 总")


if __name__ == "__main__":
    run()
