# 中文社区推广文案

## V2EX

### 标题
[分享] 我用 Python 重写了 Perplexica，部署更简单，功能更强

### 内容
最近 AI 搜索引擎很火，Perplexica 是其中的佼佼者。但它的 TypeScript/Next.js 技术栈和 PostgreSQL 依赖让我这个 Python 开发者觉得门槛有点高。

于是我用 Python/FastAPI 重写了一个版本：**ai-search-engine**

### 主要改进

| 对比项 | ai-search-engine | Perplexica |
|--------|-----------------|-----------|
| 技术栈 | Python / FastAPI | TypeScript / Next.js |
| 数据库 | SQLite（零依赖） | PostgreSQL |
| 部署 | 只需 Python 3.11+ | 需要 Node.js + PostgreSQL |
| 多用户 | 内置 API Key + 管理后台 | 无 |
| 安全 | CSRF/SSRF/安全头/暴力破解防护 | 基本无 |
| 搜索容错 | SearXNG + DuckDuckGo 自动降级 | 仅 SearXNG |
| 中文支持 | 查询自动改写为英文搜索 | 无 |

### 特性

- 多搜索引擎聚合（SearXNG + DuckDuckGo）
- 智能研究流程（分类 → 搜索 → 抓取 → 综合回答）
- 流式输出（SSE）
- 双模型架构（分类用小模型省成本，回答用大模型保证质量）
- 多用户认证（API Key + 管理面板）
- 生产级安全（CSRF、SSRF、安全头等）
- 零外部依赖（SQLite WAL 模式）

### 快速开始

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8700
```

Docker 一键部署：

```bash
docker-compose --profile searxng up -d
```

### 项目地址

https://github.com/LiuChenICBC/ai-search-engine

欢迎 Star 和 PR！

---

## 知乎

### 标题
如何搭建一个私有的 AI 搜索引擎？推荐一个开源项目 ai-search-engine

### 内容
在 AI 时代，传统的搜索引擎正在被重新定义。最近我发现了一个很有意思的开源项目 **ai-search-engine**，它是一个基于 Python/FastAPI 的 AI 搜索引擎，灵感来自 Perplexica，但在易用性和安全性上做了很多改进。

### 项目特点

1. **部署简单**：只需要 Python 3.11+，不需要 PostgreSQL 等外部数据库
2. **安全可靠**：内置 CSRF 防护、SSRF 防护、安全响应头、暴力破解防护等
3. **多用户支持**：内置 API Key 认证和管理后台
4. **搜索稳定**：支持 SearXNG + DuckDuckGo 多引擎容错
5. **中文优化**：自动将中文查询改写为英文搜索

### 工作流程

```
用户提问
  → LLM 分类（决定搜索策略）
  → 多引擎并行搜索
  → 抓取网页内容
  → LLM 综合回答（带引用）
```

### 适用场景

- 个人私有搜索引擎
- 企业内部知识问答
- 学术研究辅助
- 家庭 NAS 搭建

### 快速体验

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
uvicorn main:app --port 8700
```

访问 http://localhost:8700 即可使用。

项目地址：https://github.com/LiuChenICBC/ai-search-engine

---

## 掘金

### 标题
Python 开发者福音：用 FastAPI 打造私有 AI 搜索引擎，比 Perplexica 更易用

### 内容
## 前言

如果你关注 AI 搜索领域，一定听说过 Perplexica。它是一个优秀的开源 AI 搜索引擎，但 TypeScript/Next.js 的技术栈对 Python 开发者不太友好。

今天介绍一个 Python 替代方案：**ai-search-engine**

## 为什么选择 Python？

- 更低的部署门槛（不需要 Node.js + PostgreSQL）
- 更丰富的生态（FastAPI、requests、beautifulsoup4）
- 更容易定制和扩展

## 核心特性

### 1. 多搜索引擎聚合

```python
# 自动降级：SearXNG → DuckDuckGo
# 并行搜索 + 超时控制
# 智能重试 + 指数退避
```

### 2. 智能研究流程

```python
# 1. classify: LLM 分类查询
# 2. search: 多引擎并行搜索
# 3. extract: 抓取网页内容
# 4. synthesize: LLM 综合回答
```

### 3. 双模型架构

```yaml
llm:
  model: "gpt-4"           # 回答模型
  classify_model: "gpt-3.5" # 分类模型（省成本）
```

### 4. 安全特性

- API Key SHA-256 哈希存储
- CSRF 双重提交保护
- SSRF 防护（协议白名单 + IP 检查）
- 安全响应头（CSP, HSTS, X-Frame-Options）
- 登录暴力破解防护

## 部署方式

### 方式一：本地部署

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
uvicorn main:app --port 8700
```

### 方式二：Docker 部署

```bash
docker-compose --profile searxng up -d
```

### 方式三：生产部署

详见项目文档：docs/DEPLOY.md

## 与 Perplexica 对比

| 功能 | ai-search-engine | Perplexica |
|------|-----------------|-----------|
| 部署难度 | ⭐ 简单 | ⭐⭐⭐ 复杂 |
| 安全性 | ⭐⭐⭐ 完善 | ⭐ 基础 |
| 多用户 | ✅ 内置 | ❌ 无 |
| 搜索容错 | ✅ 多引擎 | ❌ 单引擎 |
| 中文支持 | ✅ 自动改写 | ❌ 无 |

## 总结

ai-search-engine 是一个功能完善、安全可靠、部署简单的 AI 搜索引擎。如果你是 Python 开发者，或者想要一个轻量级的私有搜索引擎，值得一试。

GitHub: https://github.com/LiuChenICBC/ai-search-engine

---

**标签**: Python, FastAPI, AI, 搜索引擎, Perplexica, LLM, 开源项目

---

## SegmentFault / CSDN

### 标题
Python 实现的 AI 搜索引擎：ai-search-engine 项目介绍

### 内容
## 项目简介

ai-search-engine 是一个基于 Python/FastAPI 的 AI 搜索引擎，灵感来自 Perplexica，但在安全性、多用户管理和部署便捷性上做了大幅增强。

## 主要特性

1. **多搜索引擎聚合**：SearXNG 优先，DuckDuckGo 自动降级
2. **智能研究流程**：LLM 分类 → 查询改写 → 多引擎搜索 → 网页抓取 → 综合回答
3. **流式输出**：SSE 实时流式回答
4. **双模型架构**：分类用小模型，回答用大模型
5. **多用户认证**：API Key SHA-256 哈希存储 + 管理后台
6. **生产级安全**：CSRF/SSRF/安全头/暴力破解防护
7. **零外部依赖**：SQLite WAL 模式

## 快速开始

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
uvicorn main:app --port 8700
```

## 项目地址

https://github.com/LiuChenICBC/ai-search-engine

## 相关资源

- [API 文档](docs/API.md)
- [部署指南](docs/DEPLOY.md)
- [架构文档](docs/ARCHITECTURE.md)
