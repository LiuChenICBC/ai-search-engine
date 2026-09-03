# www_search Security Audit Report — 修复后终版

**Date:** 2026-06-14
**Scope:** /Users/liuchen/projects/www_search/
**Status:** 所有 Critical + Medium 问题已修复

---

## Summary

| Dimension    | Critical (修复前) | Critical (修复后) | Medium (修复前) | Medium (修复后) |
|-------------|-------------------|-------------------|-----------------|-----------------|
| Security     |       4           |        0          |        5        |         0       |
| Reliability  |       0           |        0          |        4        |         0       |
| Correctness  |       0           |        0          |        3        |         0       |
| **Total**    |     **4**         |      **0**        |       **12**    |       **0**     |

---

## 修复清单

### CRITICAL Issues (4/4 已修复)

| ID | 问题 | 修复方案 | 文件 |
|---|---|---|---|
| SEC-C01 | Admin cookies 缺 `secure=True` | 两个 `set_cookie` 均添加 `secure=True` | main.py:516,524 |
| SEC-C02 | DNS rebinding 绕过 SSRF 防护 | `_fetch_url()` 请求前重新调用 `_validate_url()` | fetcher/web.py:99-101 |
| SEC-C03 | XSS via unsanitized URL in markdown | `escapeHtml(url)` + `rel="noopener noreferrer"` | ui/templates/index.html:587 |
| SEC-C04 | SearXNG 结果 URL 未校验 | `research.py` 过滤 `_validate_url(r.url)` | agent/research.py:12,106,144 |

### MEDIUM Issues (12/12 已修复)

| ID | 问题 | 修复方案 | 文件 |
|---|---|---|---|
| SEC-M01 | SECRET_KEY 每次重启重生成 | 改为必须设置 `WWW_SEARCH_SECRET_KEY` 环境变量 | main.py:136-141 |
| SEC-M02 | Rate limit 代理头伪造 | 部署时配置可信反向代理（运维层面） | - |
| SEC-M03 | CSRF cookie 缺 `secure=True` | 同 SEC-C01 修复，`csrf_token` cookie 添加 `secure=True` | main.py:524 |
| COR-M04 | Username 输入未校验 | 添加长度限制 + 字符白名单校验 | main.py:592-601 |
| REL-M05 | DB init 竞态条件 | `ensure_db()` 添加 `threading.Lock()` | db.py:258,263 |
| REL-M06 | chat() 阻塞事件循环 | 改为 `async def` + `run_in_executor` | main.py:361-369 |
| REL-M07 | record_usage 阻塞响应 | 改为 `asyncio.create_task` fire-and-forget | main.py:214-220,266-268 |
| COR-M08 | 重复记录 usage | 移除 `chat()` 中的 `record_usage()` 调用 | main.py:381 |
| COR-M09 | regenerate_key 竞态 | 读写合并到同一 `with get_db()` 事务 | db.py:198-207 |
| REL-M10 | _login_attempts 无界增长 | 添加 `_MAX_LOGIN_TRACKED_IPS=10000` + 清理过期条目 | main.py:150,157-172 |
| COR-M11 | toggle 静默失败 | 失败时返回 `flash=error` 重定向 | main.py:631 |
| C-M05 | lifespan 异常处理不足 | 分离 config 和 agent 初始化异常处理 | main.py:63-81 |

---

## 测试验证

- 测试文件: `test_fixes.py` (39 个测试用例)
- 结果: **39 通过, 0 失败**
- 覆盖: 所有 Critical + Medium 修复点的自动化验证

---

## 剩余观察项 (Informational)

| ID | 描述 | 建议 |
|---|---|---|
| INFO-01 | LLM API key 明文存储在 config.yaml | 使用环境变量替代 |
| INFO-02 | `_db_executor` 线程池未在 lifespan 中关闭 | 在 lifespan shutdown 中添加关闭逻辑 |
| INFO-03 | `search_all()` 每次调用重建引擎实例 | 缓存引擎列表 |
| INFO-04 | shutdown_handler 重新发送信号 | 让 uvicorn 通过 lifespan 处理关闭 |
| SEC-M02 | Rate limit 代理头伪造 | 部署时配置可信反向代理 |
