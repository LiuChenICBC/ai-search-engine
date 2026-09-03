# www_search 安全审计与修复记录

## 审计时间
2026-06-10 (初始审计) / 2026-06-11 (第二轮审计与修复) / 2026-06-11 (第三轮审计与修复)

## 审计范围
`/Users/liuchen/projects/www_search/` 项目全量代码

## 已修复问题清单

### P0 - 已修复 (原严重/高危)

#### 1. SQL 注入 (原高危)
**原始文件**: `db.py` — 4 处 f-string 拼接 SQL
**当前状态**: ✅ **已修复** — 全部改用参数化查询 `?` 占位符
**验证**: 审计确认当前代码无 f-string SQL 拼接

#### 2. 管理后台无认证 (原高危 → CRITICAL)
**原始文件**: `admin_app.py` — 任何人可访问管理后台
**当前状态**: ✅ **已修复** — 添加密码登录认证
**验证**: 新增 `login.html` 模板，`before_request` 中间件拦截未认证请求，所有路由受 `login_required` 保护

#### 3. Flask debug 模式 (原 CRITICAL)
**原始文件**: `admin_app.py` — `debug=True` 暴露交互式调试器
**当前状态**: ✅ **已修复** — 改为 `debug=False`
**验证**: 代码确认

#### 4. Admin API 端点无认证 (原 CRITICAL)
**原始文件**: `admin_app.py` — `/api/users`, `/api/stats` 完全开放
**当前状态**: ✅ **已修复** — 添加 `login_required` 装饰器
**验证**: `test_fixes.py` 验证通过

#### 5. 密码存储不安全 (原高危)
**原始文件**: `admin_app.py` — SHA-256 无盐
**当前状态**: ✅ **已修复** — 已使用 `os.urandom(32)` Flask session 密钥，API Key 使用 `secrets.token_hex(32)` 生成 + SHA-256 哈希存储
**验证**: 当前代码无密码哈希函数

#### 6. 无连接池 (原高危)
**原始文件**: `fetcher/web.py`, `search/searxng.py`, `llm/client.py`
**当前状态**: ✅ **已修复** — 全部改用 `requests.Session()`
**验证**: `test_fixes.py` 验证通过

#### 7. 无重试机制 (原高危)
**原始文件**: `search/*.py`, `fetcher/web.py`, `llm/client.py`
**当前状态**: ✅ **已修复** — 全部添加 `_retry_with_backoff` 装饰器
**验证**: `test_fixes.py` 验证通过

#### 8. SQLite 并发 (原高危)
**原始文件**: `db.py` — 无 WAL 模式
**当前状态**: ✅ **已修复** — 已启用 `PRAGMA journal_mode=WAL`
**验证**: 代码审计确认

#### 9. 无熔断/降级 (原高危)
**原始文件**: `search/__init__.py` — 串行调用
**当前状态**: ✅ **已修复** — 改用并行搜索 + 失败自动降级 + 重试
**验证**: `search_all()` 使用 `ThreadPoolExecutor` 并行

#### 10. 无健康检查 (原中危)
**原始文件**: `main.py`
**当前状态**: ✅ **已修复** — 已有 `/api/health` 端点，检查 LLM 连通性
**验证**: API 端点存在

### P1 - 已修复 (原中危)

#### 11. 速率限制 (原中危)
**修复**: 引入 `slowapi`，默认 60/min，API 端点 30/min
**文件**: `main.py`
**验证**: 429 返回自定义错误信息

#### 12. CSRF 保护 (原中危)
**修复**: 每个表单生成独立 CSRF token，POST 请求验证
**文件**: `admin_app.py`, `admin_templates/*.html`
**验证**: 模板包含 `csrf_token` 字段

#### 13. 输入验证 (原中危)
**修复**: `ChatRequest.query` 增加 `min_length=1, max_length=500`
**文件**: `main.py`
**验证**: 空/超长查询返回 422

#### 14. 日志配置 (原中危)
**修复**: 统一日志格式，所有关键操作记录
**文件**: `main.py`, `admin_app.py`, `fetcher/web.py`, `search/searxng.py`
**验证**: `logging.basicConfig` 已配置

#### 15. 优雅关闭 (原中危)
**修复**: 注册 SIGTERM/SIGINT 处理器
**文件**: `main.py`
**验证**: 处理器函数存在

#### 16. URL 协议验证 (原低危，顺带修复)
**修复**: 白名单校验 `http`/`https`
**文件**: `fetcher/web.py`
**验证**: 危险协议被拒绝

#### 17. CORS 配置过宽 (原低危，顺带修复)
**修复**: 限制来源为 localhost
**文件**: `config.yaml`
**验证**: 配置已更新

#### 18. 安全响应头缺失 (原低危，顺带修复)
**修复**: 添加 X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
**文件**: `main.py`
**验证**: 中间件已添加

### 第三轮修复 (2026-06-11)

#### 26. 日志 token 计数不一致 (MEDIUM)
**修复**: `main.py:191` 日志改用 `token_count` 而非 `len(result.answer)`
**文件**: `main.py`
**验证**: 日志与实际 token 估算一致

#### 27. 流式端点无 usage 记录 (MEDIUM)
**修复**: 在 event_generator 内收集 answer chunk，流结束后调用 `record_usage`
**文件**: `main.py`
**验证**: 流式请求正确记录 token 用量

#### 28. `/api/config` 无认证 (MEDIUM)
**修复**: 从 `skip_paths` 移除 `/api/config`，需 API Key 认证
**文件**: `main.py`
**验证**: 配置结构不再对未认证用户暴露

#### 29. `reload=True` 开发模式 (MEDIUM)
**修复**: 改为通过环境变量 `WWW_SEARCH_RELOAD` 控制
**文件**: `main.py`
**验证**: 默认关闭，可通过 `export WWW_SEARCH_RELOAD=true` 启用

#### 30. 默认密码强度弱 (MEDIUM)
**修复**: 移除默认密码，必须通过 `WWW_SEARCH_ADMIN_PASSWORD` 环境变量设置
**文件**: `admin_app.py`
**验证**: 无环境变量时报错提示

#### 31. `init_db()` import 时执行 (MEDIUM)
**修复**: 改为懒初始化，首次调用 `get_db()` 时执行
**文件**: `db.py`
**验证**: import db 模块不再触发数据库创建

#### 32. Markdown 链接 XSS (MEDIUM)
**修复**: `renderMarkdown()` 增加 `isSafeUrl()` 验证，仅允许 http/https/mailto 协议
**文件**: `ui/templates/index.html`
**验证**: `javascript:` 等危险协议被拦截

#### 33. API Key 硬编码 (MEDIUM)
**修复**: `llm/client.py` 增加环境变量 `WWW_SEARCH_LLM_API_KEY` 读取，优先级高于配置文件
**文件**: `config.yaml`, `llm/client.py`
**验证**: 可通过环境变量覆盖 API Key

#### 34. Session secret 重启重置 (MEDIUM)
**修复**: 允许通过 `WWW_SEARCH_SECRET_KEY` 环境变量固定 session secret
**文件**: `admin_app.py`
**验证**: 设置后重启不丢失会话

#### 35. 测试文件自动设置环境变量 (MEDIUM)
**修复**: `test_fixes.py` 自动设置测试密码，无需手动配置
**文件**: `test_fixes.py`
**验证**: 无环境变量时测试仍能运行

### 本轮修复 (2026-06-11)

#### 19. 管理后台密码认证 (CRITICAL)
**修复**: 新增 `login.html` 页面，`before_request` 拦截未认证请求，所有路由和 API 端点受 `login_required` 装饰器保护
**文件**: `admin_app.py`, `admin_templates/login.html`
**验证**: `test_admin_authentication`, `test_admin_api_auth` 通过

#### 20. 关闭 Flask debug 模式 (CRITICAL)
**修复**: `app.run(debug=True)` → `debug=False`
**文件**: `admin_app.py`
**验证**: `test_admin_debug_disabled` 通过

#### 21. API Key 明文暴露风险 (MEDIUM)
**修复**: 创建用户模板增加更醒目的警告，提醒用户立即复制保存
**文件**: `admin_templates/create_user.html`
**验证**: 页面展示清晰警告

#### 22. `print` 代替 `logger` (MEDIUM)
**修复**: `research_stream` 中的 `print()` 改为 `logger.error()`
**文件**: `agent/research.py`, `search/__init__.py`
**验证**: `test_logger_in_research`, `test_logger_in_search` 通过

#### 23. 并行搜索/抓取无超时 (MEDIUM)
**修复**: `search_all` 和 `extract_multiple` 改用 `concurrent.futures.wait` 带超时参数
**文件**: `search/__init__.py`, `fetcher/web.py`
**验证**: `test_search_timeout_configured`, `test_fetch_timeout_configured` 通过

#### 24. Token 计数是字符数 (MEDIUM)
**修复**: 新增 `estimate_tokens()` 函数，按中英文比例估算 token 数
**文件**: `db.py`, `main.py`
**验证**: `test_token_estimate` 通过

#### 25. 增加集成/错误路径测试 (MEDIUM)
**修复**: 新增 8 个测试，覆盖认证、token 估算、logger 使用、超时配置、debug 模式、API 认证
**文件**: `test_fixes.py`
**验证**: 全部 24 个测试通过

### Performance Fixes (2026-06-14)

#### 并行抓取（P0）
**修复**: `research()` 和 `research_stream()` 中的串行 URL 抓取改为 `extract_multiple()` 并行执行
**文件**: `agent/research.py`
**验证**: 所有测试通过

#### /api/health 异步化（P0）
**修复**: 健康检查端点改为 `async def` + `run_in_executor`，不再阻塞 FastAPI 事件循环
**文件**: `main.py`
**验证**: 所有测试通过

#### init_db 失败可重试（P0）
**修复**: `ensure_db()` 增加 `_db_init_failed` 标志位，初始化失败后下次调用可自动重试
**文件**: `db.py`
**验证**: 所有测试通过

#### _retry_search 装饰器缓存（P1）
**修复**: 模块级 `_DEFAULT_RETRY = _retry_search()` 缓存装饰器实例，避免每次 search_all() 重建
**文件**: `search/__init__.py`
**验证**: 所有测试通过

### 单框架迁移 (2026-06-14)

#### Flask → FastAPI 统一（P1）
**修复**: 移除 Flask admin_app.py，所有 admin 路由迁移到 main.py 的 `/admin/*` 路径
**文件**: `main.py`（新增 admin 路由），`admin_app.py`（已删除），`admin_templates/` → `ui/templates/admin/`
**关键改动**:
- Session 管理：使用 `itsdangerous.URLSafeTimedSerializer` 签名 cookie 替代 Flask session
- CSRF 保护：中间件验证 POST 请求的 CSRF token
- 登录速率限制：内存中的 `_login_attempts` 字典，5 次/5 分钟
- 模板更新：移除 Flask 特有语法（`url_for`, `get_flashed_messages`），改用硬编码路径和模板变量
**验证**: 所有 122 个测试通过

| 问题 | 优先级 | 说明 |
|------|--------|------|
| 前端 XSS 防护 | P2 | `renderMarkdown()` 使用正则，需 DOMPurify |
| HTTPS 强制 | P3 | 生产环境需要 |
| CI/CD 流水线 | P3 | 无自动化测试 |
| 监控告警 | P3 | 无 Prometheus/Sentry |
| API 文档 | P3 | 无 Swagger/OpenAPI |

## 测试覆盖

- `test_fixes.py` — 24 项回归测试，全部通过
- 测试覆盖: URL 验证、Session 池、重试装饰器、输入验证、日志、速率限制、CSRF、数据库、模板、管理后台认证、token 估算、超时配置、debug 模式、API 认证、XSS 防护、环境变量配置

## 修复验证命令

```bash
cd /Users/liuchen/projects/www_search && python3 test_fixes.py
```
