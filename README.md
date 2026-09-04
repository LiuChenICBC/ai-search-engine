# ai-search-engine - Perplexica 风格 AI 搜索引擎

基于 FastAPI 的本地 AI 搜索引擎，支持多搜索引擎聚合、网页内容抓取和 LLM 综合回答。

灵感来自 [Perplexica](https://github.com/ItzCrazyKns/Perplexica)，但在安全性、多用户管理和部署便捷性上做了大幅增强。

## 为什么选择 ai-search-engine？

| 维度 | ai-search-engine | Perplexica |
|------|-----------------|-----------|
| 技术栈 | Python / FastAPI | TypeScript / Next.js |
| 数据库 | SQLite（零依赖） | PostgreSQL |
| 部署门槛 | 只需 Python 3.11+ | 需要 Node.js + PostgreSQL |
| 多用户认证 | 内置 API Key + 管理后台 | 无（Upcoming Feature） |
| 安全防护 | CSRF / SSRF / 安全头 / 暴力破解防护 | 基本无 |
| 搜索容错 | SearXNG + DuckDuckGo 自动降级 + 重试 | 仅 SearXNG |
| 双模型架构 | 分类用小模型，回答用大模型 | 单模型 |
| 中文优化 | 查询自动改写为英文搜索 | 无 |

## 特性

- **多搜索引擎聚合**：SearXNG 优先，DuckDuckGo 自动降级，并行搜索 + 超时取消 + 重试退避
- **智能研究流程**：LLM 分类 → 查询改写为英文 → 多引擎搜索 → 网页抓取 → 综合回答
- **流式输出**：SSE 实时流式回答
- **双模型架构**：`classify_model` 处理查询分类（省成本），`model` 生成综合回答
- **多用户认证**：API Key SHA-256 哈希存储 + 时序安全比较，管理员面板 + 使用统计
- **生产级安全**：CSRF 双重提交、SSRF 防护、安全响应头、登录暴力破解防护、请求大小限制
- **零外部依赖**：SQLite WAL 模式，开箱即用，无需 PostgreSQL
- **可配置**：YAML 配置 LLM/搜索/抓取/服务器参数

## 快速开始

### 环境要求

- Python 3.11+
- 本地 LLM 服务（LM Studio / Ollama）或 OpenAI API

### 安装

```bash
# 克隆项目
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 或使用 pyproject.toml
pip install -e .
```

### 配置

```bash
# 复制环境变量示例
cp .env.example .env
# 编辑 .env 填入实际值

# 设置管理后台密码
export WWW_SEARCH_ADMIN_PASSWORD='your-strong-password'
export WWW_SEARCH_SECRET_KEY='your-secret-key-here'

# 可选：LLM API Key（覆盖 config.yaml）
export WWW_SEARCH_LLM_API_KEY='your-api-key'
```

### 启动

```bash
# 开发模式
uvicorn main:app --host 0.0.0.0 --port 8700 --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8700 --workers 1
```

访问 http://localhost:8700 使用 Web UI。

## 项目结构

```
ai-search-engine/
├── agent/              # 研究代理（编排搜索、抓取、LLM）
├── fetcher/            # 网页内容抓取
├── llm/                # LLM 客户端
├── search/             # 搜索引擎（SearXNG、DuckDuckGo）
├── ui/                 # Web UI（模板、静态文件）
├── config/             # 常量配置
├── docs/               # 文档（API、部署、架构）
├── .github/workflows/  # CI/CD（GitHub Actions）
├── main.py             # FastAPI 入口
├── db.py               # SQLite 数据库层
├── middleware.py       # 中间件（认证、CSRF、安全头）
├── utils.py            # 工具函数
├── config.yaml         # 配置文件
├── .env.example        # 环境变量示例
├── requirements.txt    # 依赖列表（版本钉住）
├── pyproject.toml      # 项目配置（构建、lint）
├── Dockerfile          # 容器化构建
├── docker-compose.yml  # Compose 编排（含可选 SearXNG）
└── LICENSE             # MIT 许可证
```

## API 文档

详见 [docs/API.md](docs/API.md)

## 部署

详见 [docs/DEPLOY.md](docs/DEPLOY.md)

### Docker（推荐）

```bash
# 复制环境变量配置
cp .env.example .env
# 编辑 .env 填入密码和密钥

# 启动（含 SearXNG）
docker-compose --profile searxng up -d

# 仅启动应用
docker-compose up -d
```

## 持续集成

项目使用 GitHub Actions 自动运行 ruff lint、ruff format、mypy 类型检查和 pytest 测试。详见 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)。

## 架构

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 测试

```bash
# 运行所有测试
python3 -m pytest test_*.py -v

# 测试覆盖
python3 -m pytest test_*.py --cov=. --cov-report=term-missing
```

## 安全特性

- API Key SHA-256 哈希存储 + 时序安全比较
- CSRF 双重提交（cookie + form token）+ 签名 session
- SSRF 防护（URL 协议白名单 + DNS 解析后 IP 检查）
- 登录暴力破解防护（5 次/5 分钟）
- 安全响应头（CSP, HSTS, X-Frame-Options, X-Content-Type-Options）
- Pydantic 输入校验
- 速率限制（slowapi）
- 请求大小限制（1MB）

## 许可证

[MIT License](LICENSE)
