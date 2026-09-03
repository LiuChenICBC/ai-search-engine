"""API 路由 - /api/chat, /api/config, /api/health

使用 FastAPI Depends 依赖注入从 app.state 获取 agent 和 config，
替代原来的全局 state 闭包模式。
"""

import asyncio
import copy
import json
import logging

from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter

from agent.research import ResearchAgent
from db import estimate_tokens, record_usage
from middleware import get_db_executor

logger = logging.getLogger("www_search.routes.api")


# ── Pydantic 请求模型 ──────────────────────────────────────────────


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    stream: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


# ── 依赖注入函数 ───────────────────────────────────────────────────


def get_agent() -> ResearchAgent:
    """从 app.state 获取 agent 实例（通过 Depends 注入）"""
    # 这个函数会在路由执行时通过 request.app.state 访问
    raise NotImplementedError("Use get_agent_dep instead")


def get_agent_dep(request: Request) -> ResearchAgent:
    """依赖注入：从 app.state 获取 ResearchAgent"""
    agent = request.app.state.agent
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return agent


def get_config_dep(request: Request) -> dict:
    """依赖注入：从 app.state 获取配置"""
    config = request.app.state.config
    if config is None:
        raise HTTPException(status_code=503, detail="Config not loaded")
    return config


# ── 路由工厂 ───────────────────────────────────────────────────────


def create_api_routes(app: FastAPI):
    """创建 API 路由 — 通过 Depends 注入依赖"""

    @app.post("/api/chat")
    async def chat(
        req: ChatRequest,
        agent: ResearchAgent = Depends(get_agent_dep),
        request: Request = ...,
    ):
        """非流式聊天（在线程池中执行，不阻塞事件循环）"""
        loop = asyncio.get_event_loop()
        executor = get_db_executor()
        result = await loop.run_in_executor(executor, agent.research, req.query)

        # 设置 token 计数到响应头（中间件会据此记录使用量）
        response = JSONResponse(
            content=ChatResponse(
                answer=result.answer,
                sources=result.sources,
            ).model_dump(),
        )
        token_count = estimate_tokens(result.answer)
        response.headers["X-Tokens-Used"] = str(token_count)

        logger.info(
            f"200 POST /api/chat - query='{req.query[:50]}' tokens={token_count}"
        )
        return response

    @app.post("/api/chat/stream")
    def chat_stream(
        req: ChatRequest,
        agent: ResearchAgent = Depends(get_agent_dep),
        request: Request = ...,
    ):
        """流式聊天 - SSE"""

        def event_generator():
            user_id = None
            if hasattr(request, "state") and hasattr(request.state, "user"):
                user_id = request.state.user["id"]
            collected = []
            for event in agent.research_stream(req.query):
                if event.get("type") == "answer_chunk":
                    collected.append(event["text"])
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            # 流结束后记录使用量
            if user_id and collected:
                answer_text = "".join(collected)
                token_count = estimate_tokens(answer_text)
                if token_count > 0:
                    record_usage(user_id, query=req.query, tokens_used=token_count)
            yield "data: [DONE]\n\n"

        logger.info(f"200 POST /api/chat/stream - query='{req.query[:50]}'")
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/api/config")
    def get_config(
        config: dict = Depends(get_config_dep),
        request: Request = None,
    ):
        """获取当前配置（需要认证）"""
        if not hasattr(request, "state") or not hasattr(request.state, "user"):
            raise HTTPException(status_code=401, detail="需要 API Key")
        cfg = copy.deepcopy(config)
        # 隐藏敏感信息
        if "llm" in cfg:
            cfg["llm"]["api_key"] = "***" if cfg["llm"].get("api_key") else ""
        return cfg

    @app.get("/api/health")
    async def health(
        agent: ResearchAgent = Depends(get_agent_dep),
    ):
        """健康检查 - 验证 LLM 连通性（在线程池中执行，不阻塞事件循环）"""
        try:
            loop = asyncio.get_event_loop()
            executor = get_db_executor()
            result = await loop.run_in_executor(
                executor,
                lambda: agent.llm.chat([{"role": "user", "content": "ok"}]),
            )
            return {"status": "ok", "service": "www_search", "llm": "connected"}
        except Exception as e:
            logger.error(f"503 GET /api/health - LLM 连通性检查失败: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "degraded",
                    "service": "www_search",
                    "llm_error": str(e),
                },
            )
