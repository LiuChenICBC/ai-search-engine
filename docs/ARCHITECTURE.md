# 架构文档

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         Web UI / API Client                 │
└───────────────┬─────────────────────────────┬───────────────┘
                │ HTTP/SSE                    │
                ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  API Routes │  │ Admin Routes│  │   Middleware Stack   │  │
│  │  /api/chat  │  │  /admin/*   │  │  - API Key Auth     │  │
│  │  /api/config│  │             │  │  - Rate Limiting    │  │
│  │  /api/health│  │             │  │  - CSRF Protection  │  │
│  └──────┬──────┘  └──────┬──────┘  │  - Security Headers │  │
│         │                │         └─────────────────────┘  │
│         ▼                ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Research Agent (agent/)                 │    │
│  │  1. classify(query) → search strategy                │    │
│  │  2. search_all(query) → results                      │    │
│  │  3. extract_multiple(urls) → content                 │    │
│  │  4. synthesize(context) → answer                     │    │
│  └──────┬──────────┬──────────┬──────────┬─────────────┘    │
│         │          │          │          │                   │
│         ▼          ▼          ▼          ▼                   │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐           │
│  │   LLM    │ │  Search  │ │Fetcher │ │   DB   │           │
│  │  Client  │ │ Engines  │ │  Web   │ │ SQLite │           │
│  └──────────┘ └──────────┘ └────────┘ └────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 模块详解

### 1. Research Agent (`agent/research.py`)

编排完整的研究流程：

```
用户查询
  │
  ▼
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
│ classify │───→│  search  │───→│  scrape  │───→│synthesize│
│ (LLM)    │     │ (engines)│     │ (top N)  │     │  (LLM)  │
└─────────┘     └──────────┘     └──────────┘     └─────────┘
  │               │                  │                  │
  ▼               ▼                  ▼                  ▼
策略决定       多引擎并行        内容提取          综合回答
+ URL 改写     + 去重           + 去噪           + 引用
```

**关键类:**
- `ResearchAgent`: 主控制器
- `ResearchResult`: 结果数据类

**流式支持:**
- `research()`: 同步返回完整结果
- `research_stream()`: SSE 流式输出

### 2. 搜索引擎 (`search/`)

**架构:**
```
BaseSearchEngine (ABC)
  ├── SearXNGSearch
  └── DuckDuckGoSearch
```

**特性:**
- 插件式扩展（实现 `BaseSearchEngine` 即可）
- 并行搜索 + 超时控制
- 结果去重（按 URL）
- 自动降级（SearXNG 失败 → DuckDuckGo）

### 3. 网页抓取 (`fetcher/web.py`)

**流程:**
```
URL 验证 → 协议检查 → DNS 解析 → IP 安全检查
                    ↓
             请求 + 重定向链验证
                    ↓
          HTML 解析 (BeautifulSoup)
                    ↓
          内容提取 (article/main → body)
                    ↓
          去噪 + 截断
```

**安全措施:**
- 协议白名单（http/https only）
- DNS rebinding 防护（请求前重新验证）
- 重定向链逐跳验证
- 内网 IP 禁止

### 4. LLM 客户端 (`llm/client.py`)

**特性:**
- OpenAI 兼容 API
- 同步 requests（避免 async 兼容问题）
- 指数退避重试
- 推理模型支持（reasoning_content 回退）
- 流式输出（SSE parsing）

### 5. 数据库 (`db.py`)

**表结构:**
```sql
users (
  id, username, api_key_hash, enabled,
  created_at, last_used_at, total_tokens
)

usage_records (
  id, user_id, query, tokens_used, created_at
)
```

**特性:**
- 懒初始化 + 线程安全
- WAL 模式（并发读写）
- 参数化查询（防 SQL 注入）
- API Key SHA-256 哈希存储

### 6. 中间件栈 (`main.py`)

**执行顺序（请求→响应）:**
```
1. APIKeyMiddleware      - API Key 认证
2. SlowAPIMiddleware     - 速率限制
3. CORSMiddleware        - CORS
4. add_security_headers  - 安全响应头
5. admin_csrf_middleware - CSRF 验证
```

## 数据流

### 非流式请求

```
Client → POST /api/chat
  │
  ▼
APIKeyMiddleware (验证 API Key)
  │
  ▼
chat() endpoint
  │
  ▼
run_in_executor(agent.research)
  │
  ├─→ LLM.classify(query)
  │
  ├─→ search_all(query)
  │   ├─→ SearXNGSearch.search()
  │   └─→ DuckDuckGoSearch.search()
  │
  ├─→ extract_multiple(urls)
  │
  └─→ LLM.chat(messages)
      │
      ▼
  JSONResponse + X-Tokens-Used header
      │
      ▼
  APIKeyMiddleware (记录使用量)
      │
      ▼
  Client ← 200 OK
```

### 流式请求

```
Client → POST /api/chat/stream
  │
  ▼
chat_stream() endpoint
  │
  ▼
event_generator()
  │
  ├─→ yield {"type": "status", "text": "🔍 分析问题..."}
  │
  ├─→ LLM.classify(query)
  │
  ├─→ yield {"type": "status", "text": "🌐 搜索: ..."}
  │
  ├─→ search_all(query)
  │
  ├─→ yield {"type": "status", "text": "✅ 找到 N 个结果"}
  │
  ├─→ extract_multiple(urls)
  │
  ├─→ yield {"type": "status", "text": "✍️ 综合信息中..."}
  │
  ├─→ for chunk in LLM.chat_stream(messages):
  │       yield {"type": "answer_chunk", "text": chunk}
  │
  ├─→ yield {"type": "sources", "sources": [...]}
  │
  └─→ yield {"type": "done"}
      │
      ▼
  StreamingResponse (text/event-stream)
      │
      ▼
  Client ← SSE stream
```

## 安全设计

### 认证流程

```
API 请求
  │
  ▼
检查 X-API-Key 头
  │
  ├─ 缺失 → 401
  │
  ├─ 存在 → SHA-256 哈希
  │         │
  │         ▼
  │    数据库查询 (WHERE hash = ? AND enabled = 1)
  │         │
  │         ├─ 无结果 → 时序安全 dummy 比较 → 401
  │         │
  │         └─ 有结果 → hmac.compare_digest → 200/401
  │
  ▼
设置 request.state.user
  │
  ▼
执行路由
  │
  ▼
记录使用量 (fire-and-forget)
```

### Admin Session 流程

```
登录请求
  │
  ▼
检查登录速率 (IP + 时间窗口)
  │
  ├─ 超限 → 拒绝
  │
  └─ 通过 → 验证密码
          │
          ├─ 错误 → 重定向到登录页
          │
          └─ 正确 → itsdangerous 签名 session
                   │
                   ▼
              set_cookie(admin_session, secure=True)
                   │
                   ▼
              重定向到 /admin
```

## 扩展点

### 添加新搜索引擎

```python
# search/my_engine.py
from .base import BaseSearchEngine, SearchResult

class MyEngineSearch(BaseSearchEngine):
    @property
    def name(self) -> str:
        return "my_engine"
    
    def search(self, query: str, max_results: int = 8) -> list[SearchResult]:
        # 实现搜索逻辑
        return [...]

# search/__init__.py
from .my_engine import MyEngineSearch

# config.yaml
search:
  my_engine_url: "http://..."
  use_my_engine: true
```

### 添加新中间件

```python
# middleware/custom.py
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 请求前处理
        response = await call_next(request)
        # 响应后处理
        return response

# main.py
app.add_middleware(CustomMiddleware)
```

## 配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `llm.api_base` | `http://localhost:1234/v1` | LLM API 地址 |
| `llm.api_key` | `lm-studio` | LLM API Key |
| `llm.model` | `default` | 回答模型 |
| `llm.classify_model` | 同 model | 分类模型 |
| `llm.temperature` | `0.3` | 温度参数 |
| `llm.max_tokens` | `4096` | 最大 token 数 |
| `search.searxng_url` | `""` | SearXNG 地址 |
| `search.use_ddgs` | `true` | 启用 DuckDuckGo |
| `search.max_results` | `8` | 最大搜索结果数 |
| `search.max_scrape` | `4` | 最大抓取页面数 |
| `fetcher.timeout` | `15` | 抓取超时 (秒) |
| `fetcher.max_content_length` | `8000` | 最大内容长度 |
| `server.host` | `0.0.0.0` | 监听地址 |
| `server.port` | `8700` | 监听端口 |
| `server.cors_origins` | `["http://localhost:8700"]` | CORS 允许来源 |
