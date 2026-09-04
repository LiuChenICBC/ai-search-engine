"""AI Search Engine - FastAPI 入口

模块化架构:
- middleware.py: 中间件 (API Key 认证, CSRF, 安全响应头)
- routes/api.py: API 路由 (/api/chat, /api/config, /api/health)
- routes/admin.py: Admin 路由 (/admin/*)
- db.py: SQLite 数据库层
- agent/research.py: 研究代理
- fetcher/web.py: 网页抓取
- llm/client.py: LLM 客户端
- search/: 搜索引擎
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from agent.research import ResearchAgent
from middleware import (
    AdminCSRFMiddleware,
    APIKeyMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    init_admin_config,
    set_db_executor,
)
from routes.admin import create_admin_routes
from routes.api import create_api_routes

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("www_search")

# 线程池：用于在 async 中间件/路由中执行同步 DB 操作
_db_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="db-worker")
set_db_executor(_db_executor)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_path = str(Path(__file__).parent / "config.yaml")

    # 启动时加载配置和 agent
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            raise ValueError("config.yaml 根节点必须是 YAML 映射 (dict)")
    except FileNotFoundError:
        logger.error(f"[main] 配置文件不存在: {config_path}")
        raise RuntimeError(f"配置文件不存在: {config_path}") from None
    except yaml.YAMLError as e:
        logger.error(f"[main] 配置文件格式错误: {e}")
        raise RuntimeError(f"配置文件格式错误: {e}") from None
    except ValueError as e:
        logger.error(f"[main] 配置文件内容无效: {e}")
        raise RuntimeError(f"配置文件内容无效: {e}") from None

    # 初始化 admin 配置（session serializer, CSRF 等）
    try:
        init_admin_config()
    except RuntimeError as e:
        logger.error(f"[main] Admin 配置初始化失败: {e}")
        raise

    # 检查明文 API Key 警告
    if config.get("llm", {}).get("api_key") and not os.environ.get(
        "WWW_SEARCH_LLM_API_KEY"
    ):
        logger.warning(
            "[main] 检测到 LLM API Key 明文存储在 config.yaml 中，建议使用环境变量 WWW_SEARCH_LLM_API_KEY"
        )

    try:
        agent = ResearchAgent(config_path)
    except Exception as e:
        logger.error(f"[main] Agent 初始化失败: {e}")
        raise RuntimeError(f"Agent 初始化失败: {e}") from None

    # 将状态挂载到 app.state（通过 Depends 注入到路由）
    app.state.config = config
    app.state.agent = agent

    logger.info("[main] 应用启动，agent 已初始化")
    yield

    # 优雅关闭：清理资源
    logger.info("[main] 应用关闭，正在清理资源...")
    app.state.agent = None
    app.state.config = None
    _db_executor.shutdown(wait=False)
    # REL-L01: 关闭 fetcher 全局 Session，释放连接池
    try:
        from fetcher.web import _session as fetcher_session

        fetcher_session.close()
    except Exception:
        pass
    logger.info("[main] 资源已清理，应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="ai-search-engine",
    description="Perplexica-like AI Search Engine - 基于多源搜索和 LLM 的智能问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 模板
templates = Jinja2Templates(directory=str(Path(__file__).parent / "ui" / "templates"))

# 速率限制器
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
)
app.state.limiter = limiter

# ==================== 中间件 ====================

# API Key 认证中间件
app.add_middleware(APIKeyMiddleware)

# 速率限制中间件
app.add_middleware(SlowAPIMiddleware)

# CORS 中间件 - 限制允许的头部，不使用通配符 *
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8700", "http://127.0.0.1:8700"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Accept",
        "X-API-Key",
        "Authorization",
        "Origin",
        "Cache-Control",
    ],
    allow_credentials=True,
)

# 安全响应头中间件
app.add_middleware(SecurityHeadersMiddleware)

# CSRF 中间件
app.add_middleware(AdminCSRFMiddleware)

# 请求大小限制中间件（放在最外层，尽早拒绝超大请求）
app.add_middleware(RequestSizeLimitMiddleware)


# ==================== 速率限制异常处理 ====================


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"429 {request.method} {request.url.path} - 请求过于频繁")
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "message": "请求过于频繁，请稍后再试"},
    )


# ==================== 首页路由 ====================

# 挂载静态文件 (JS, CSS)
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "ui" / "static")),
    name="static",
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Web UI"""
    return templates.TemplateResponse(request, "index.html", {"request": request})


# ==================== 注册路由 ====================

# 注册 API 路由 — 使用 Depends 依赖注入获取 agent/config
create_api_routes(app)

# 注册 Admin 路由
create_admin_routes(app, templates)


# ==================== 优雅关闭 ====================

# uvicorn 自带完善的信号处理，lifespan 上下文管理器已经处理了资源清理。
# 手动注册信号处理器并重新发送信号可能导致死循环，因此移除。
# 如需自定义关闭逻辑，在 lifespan() 的 yield 后部分添加即可。


# ==================== 入口 ====================

if __name__ == "__main__":
    import uvicorn

    with open(Path(__file__).parent / "config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    server_cfg = cfg.get("server", {})
    reload_enabled = os.environ.get("WWW_SEARCH_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host=server_cfg.get("host", "0.0.0.0"),
        port=server_cfg.get("port", 8700),
        reload=reload_enabled,
    )
