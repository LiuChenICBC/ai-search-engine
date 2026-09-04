# API 文档

## 基础信息

- Base URL: `http://localhost:8700`
- 认证方式: `X-API-Key` 请求头
- 内容类型: `application/json`

## 端点列表

### 公开端点（无需认证）

#### GET /
Web UI 首页，返回 HTML 页面。

#### GET /api/health
健康检查，验证 LLM 连通性。

**响应:**
```json
{
  "status": "ok",
  "service": "ai-search-engine",
  "llm": "connected"
}
```

或 LLM 不可用时:
```json
{
  "status": "degraded",
  "service": "ai-search-engine",
  "llm_error": "Connection refused"
}
```

### API 端点（需要 X-API-Key）

#### POST /api/chat
非流式聊天，执行完整研究流程。

**请求头:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**请求体:**
```json
{
  "query": "Python 异步编程最佳实践",
  "stream": false
}
```

**响应:**
```json
{
  "answer": "## 回答\n\nPython 异步编程...",
  "sources": [
    {
      "title": "Python 异步编程指南",
      "url": "https://example.com/python-async",
      "snippet": "Python 3.5 引入了 async/await..."
    }
  ]
}
```

**错误响应:**
- `401`: 缺少或无效 API Key
- `422`: 输入验证失败（空查询、超长查询）
- `429`: 请求过于频繁

#### POST /api/chat/stream
流式聊天，SSE 实时输出。

**请求体:**
```json
{
  "query": "Python 异步编程最佳实践",
  "stream": true
}
```

**SSE 事件:**
```
data: {"type": "status", "text": "🔍 分析问题..."}

data: {"type": "status", "text": "🌐 搜索: Python async best practices"}

data: {"type": "status", "text": "✅ 找到 8 个结果"}

data: {"type": "status", "text": "📄 抓取 4 个页面..."}

data: {"type": "status", "text": "✍️ 综合信息中..."}

data: {"type": "answer_chunk", "text": "## 回答\n\n"}

data: {"type": "answer_chunk", "text": "Python 异步编程..."}

data: {"type": "sources", "sources": [...]}

data: {"type": "done"}
```

#### GET /api/config
获取当前配置（隐藏敏感信息）。

**响应:**
```json
{
  "llm": {
    "api_base": "http://localhost:1234/v1",
    "api_key": "***",
    "model": "default",
    "temperature": 0.3
  },
  "search": {
    "max_results": 8,
    "max_scrape": 4
  }
}
```

### 管理后台端点（需要登录 session）

#### GET /admin/login
登录页面。

#### POST /admin/login
处理登录。

**表单数据:**
```
password: your-admin-password
```

**响应:**
- 成功: `303` 重定向到 `/admin`
- 失败: `303` 重定向到 `/admin/login?flash=error:密码错误`

#### GET /admin
管理仪表盘，显示统计信息。

#### GET /admin/users/create
创建用户页面。

#### POST /admin/users/create
创建新用户。

**表单数据:**
```
username: newuser
csrf_token: your-csrf-token
```

#### POST /admin/users/toggle/<user_id>
启用/禁用用户。

#### POST /admin/users/regenerate/<user_id>
重新生成 API Key。

#### GET /admin/users/usage/<user_id>
查看用户使用记录。

#### GET /admin/api/users
API: 获取所有用户列表。

**响应:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "user1",
      "enabled": true,
      "created_at": "2026-01-01T00:00:00",
      "last_used_at": "2026-06-15T10:00:00",
      "total_tokens": 10000
    }
  ]
}
```

#### GET /admin/api/stats
API: 获取全局统计。

**响应:**
```json
{
  "total_users": 5,
  "enabled_users": 4,
  "disabled_users": 1,
  "total_records": 100,
  "total_tokens": 50000,
  "daily_usage": [
    {"day": "2026-06-15", "count": 10, "tokens": 5000}
  ]
}
```

#### POST /admin/logout
登出。

## 错误码

| 状态码 | 含义 |
|--------|------|
| 401 | 缺少或无效认证 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 输入验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 服务降级（LLM 不可用） |

## 速率限制

- 默认: 60 请求/分钟（按 IP）
- /api/chat: 30 请求/分钟
- /api/config: 10 请求/分钟
- 登录: 5 次/5 分钟（防暴力破解）

## CLI 使用

```bash
# 直接搜索
python3 cli.py "Python 异步编程"

# 指定配置
python3 cli.py "Python 异步编程" --config config.yaml
```
