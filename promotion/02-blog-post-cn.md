# 我用 Python 重写了 Perplexica，功能更强，部署更简单

## 前言

最近 AI 搜索引擎非常火，[Perplexica](https://github.com/ItzCrazyKns/Perplexica) 是其中的佼佼者。但作为 Python 开发者，我觉得它的 TypeScript/Next.js 技术栈门槛有点高，还需要 PostgreSQL 数据库。

于是我用 Python/FastAPI 重写了一个版本，项目名叫 **ai-search-engine**。它保留了 Perplexica 的核心功能，同时在安全性、多用户管理和部署便捷性上做了大幅增强。

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

## 核心特性

### 1. 多搜索引擎聚合

- **SearXNG 优先**：自托管的元搜索引擎
- **DuckDuckGo 降级**：SearXNG 不可用时自动切换
- **并行搜索 + 超时控制**：多个引擎同时搜索，超时自动取消
- **智能重试**：失败自动重试，指数退避

### 2. 智能研究流程

```
用户查询
  │
  ▼
classify (LLM 分类，决定搜索策略)
  │
  ▼
search_all (多引擎并行搜索 + 去重)
  │
  ▼
extract_multiple (抓取网页内容 + 去噪)
  │
  ▼
synthesize (LLM 综合回答 + 引用来源)
```

### 3. 双模型架构

- **classify_model**：处理查询分类，用小模型节省成本
- **model**：生成综合回答，用大模型保证质量

### 4. 流式输出

SSE 实时流式回答，用户体验更好：

```javascript
// 前端接收流式响应
const eventSource = new EventSource('/api/chat/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'answer_chunk') {
    appendToUI(data.text);
  }
};
```

### 5. 多用户认证

- API Key SHA-256 哈希存储
- 时序安全比较（防止时序攻击）
- 管理员面板 + 使用统计
- 支持创建/禁用/删除用户

### 6. 生产级安全

- **CSRF 双重提交**：cookie + form token
- **SSRF 防护**：URL 协议白名单 + DNS 解析后 IP 检查
- **安全响应头**：CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **暴力破解防护**：5 次/5 分钟限制
- **速率限制**：slowapi
- **请求大小限制**：1MB

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
```

### 配置

```bash
# 复制环境变量示例
cp .env.example .env

# 设置管理后台密码
export WWW_SEARCH_ADMIN_PASSWORD='your-strong-password'
export WWW_SEARCH_SECRET_KEY='your-secret-key-here'
```

### 启动

```bash
# 开发模式
uvicorn main:app --host 0.0.0.0 --port 8700 --reload
```

访问 http://localhost:8700 使用 Web UI。

### Docker 一键部署

```bash
# 启动（含 SearXNG）
docker-compose --profile searxng up -d
```

## 部署建议

### 本地部署（推荐）

使用 LM Studio 或 Ollama 作为 LLM 后端，完全离线运行，数据不出本机。

### 云服务器部署

1. 使用 Docker Compose
2. 配置 Nginx 反向代理
3. 使用 Let's Encrypt 配置 HTTPS

### 家庭服务器

在树莓派或 NAS 上部署，配合 SearXNG，打造私有搜索引擎。

## 与 Perplexica 的对比

Perplexica 是一个优秀的项目，ai-search-engine 在它的基础上做了以下增强：

1. **部署更简单**：不需要 PostgreSQL，SQLite 零依赖
2. **更安全**：完整的安全防护体系
3. **多用户支持**：内置 API Key 认证和管理后台
4. **搜索更稳定**：多引擎容错，自动降级
5. **中文优化**：自动将中文查询改写为英文搜索

## 项目地址

GitHub: https://github.com/LiuChenICBC/ai-search-engine

欢迎 Star 和 PR！

## 总结

ai-search-engine 是一个功能完善、安全可靠、部署简单的 AI 搜索引擎。如果你是 Python 开发者，或者想要一个轻量级的私有搜索引擎，它是一个不错的选择。

如果你有问题或建议，欢迎在 GitHub 上提 Issue。

---

**标签**: #AI #搜索引擎 #Python #FastAPI #Perplexica #LLM #开源项目
