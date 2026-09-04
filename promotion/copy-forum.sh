#!/bin/bash

# 推广材料快速复制脚本
# 使用方法: ./promotion/copy-forum.sh [选项]

PROMOTION_DIR="$(dirname "$0")"

show_menu() {
    echo "=========================================="
    echo "  ai-search-engine 推广材料复制工具"
    echo "=========================================="
    echo ""
    echo "中文平台:"
    echo "  1) V2EX 标题 + 内容"
    echo "  2) 知乎 标题 + 内容"
    echo "  3) 掘金 标题 + 内容"
    echo ""
    echo "英文平台:"
    echo "  4) Reddit r/selfhosted"
    echo "  5) Reddit r/Python"
    echo "  6) Reddit r/LocalLLaMA"
    echo "  7) Hacker News Show HN"
    echo ""
    echo "社交媒体:"
    echo "  8) Twitter 推文 (特性介绍)"
    echo "  9) Twitter 推文 (对比 Perplexica)"
    echo ""
    echo "博客:"
    echo "  10) 中文博客全文"
    echo "  11) 英文博客全文"
    echo ""
    echo "  0) 退出"
    echo ""
}

copy_to_clipboard() {
    local content="$1"
    if command -v pbcopy &> /dev/null; then
        echo "$content" | pbcopy
        echo "✓ 已复制到剪贴板"
    elif command -v xclip &> /dev/null; then
        echo "$content" | xclip -selection clipboard
        echo "✓ 已复制到剪贴板"
    else
        echo "⚠ 无法复制到剪贴板，请手动选择复制"
        echo ""
        echo "$content"
    fi
}

get_v2ex() {
    local title="[分享] 我用 Python 重写了 Perplexica，部署更简单，功能更强"
    local content=$(cat <<'EOF'
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
EOF
)
    echo "标题: $title"
    echo ""
    echo "内容:"
    echo "$content"
    echo ""
    copy_to_clipboard "标题: $title

$content"
    echo ""
    echo "正在打开浏览器..."
    open "https://www.v2ex.com/new"
}

get_zhihu() {
    local title="如何搭建一个私有的 AI 搜索引擎？推荐一个开源项目 ai-search-engine"
    local content=$(cat <<'EOF'
在 AI 时代，传统的搜索引擎正在被重新定义。最近我发现了一个很有意思的开源项目 **ai-search-engine**，它是一个基于 Python/FastAPI 的 AI 搜索引擎，灵感来自 Perplexica，但在易用性和安全性上做了很多改进。

### 项目特点

1. **部署简单**：只需要 Python 3.11+，不需要 PostgreSQL 等外部数据库
2. **安全可靠**：内置 CSRF 防护、SSRF 防护、安全响应头、暴力破解防护等
3. **多用户支持**：内置 API Key 认证和管理后台
4. **搜索稳定**：支持 SearXNG + DuckDuckGo 多引擎容错
5. **中文优化**：自动将中文查询改写为英文搜索

### 快速体验

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
uvicorn main:app --port 8700
```

访问 http://localhost:8700 即可使用。

项目地址：https://github.com/LiuChenICBC/ai-search-engine
EOF
)
    echo "标题: $title"
    echo ""
    echo "内容:"
    echo "$content"
    echo ""
    copy_to_clipboard "标题: $title

$content"
    echo ""
    echo "正在打开浏览器..."
    open "https://www.zhihu.com/creator/content"
}

get掘金() {
    local title="Python 开发者福音：用 FastAPI 打造私有 AI 搜索引擎，比 Perplexica 更易用"
    local content=$(cat <<'EOF'
## 前言

如果你关注 AI 搜索领域，一定听说过 Perplexica。它是一个优秀的开源 AI 搜索引擎，但 TypeScript/Next.js 的技术栈对 Python 开发者不太友好。

今天介绍一个 Python 替代方案：**ai-search-engine**

## 核心特性

### 1. 多搜索引擎聚合

- SearXNG 优先，DuckDuckGo 自动降级
- 并行搜索 + 超时控制
- 智能重试 + 指数退避

### 2. 智能研究流程

```
用户提问
  → LLM 分类（决定搜索策略）
  → 多引擎并行搜索
  → 抓取网页内容
  → LLM 综合回答（带引用）
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

## 快速开始

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
uvicorn main:app --port 8700
```

## 项目地址

https://github.com/LiuChenICBC/ai-search-engine

**标签**: Python, FastAPI, AI, 搜索引擎, Perplexica, LLM, 开源项目
EOF
)
    echo "标题: $title"
    echo ""
    echo "内容:"
    echo "$content"
    echo ""
    copy_to_clipboard "标题: $title

$content"
    echo ""
    echo "正在打开浏览器..."
    open "https://juejin.cn/post/new"
}

get_reddit_selfhosted() {
    local title="I built a Python alternative to Perplexica - easier deployment, better security, multi-user support"
    local content=$(cat <<'EOF'
Hey selfhosters!

I've been using Perplexica for AI-powered search, but found the TypeScript/Next.js stack and PostgreSQL requirement a bit heavy for my needs.

So I built **ai-search-engine** - a Python/FastAPI alternative that's simpler to deploy while adding some important features:

**Key improvements over Perplexica:**

- **SQLite instead of PostgreSQL** - zero database dependencies
- **Multi-user authentication** - built-in API key management and admin panel
- **Production-grade security** - CSRF protection, SSRF prevention, security headers, brute-force protection
- **Multi-engine search** - SearXNG + DuckDuckGo with automatic fallback
- **Dual model architecture** - small model for query classification (saves costs), large model for answers
- **Chinese language support** - auto-rewrites Chinese queries to English for better results

**Quick start:**

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8700
```

Or with Docker:

```bash
docker-compose --profile searxng up -d
```

**Tech stack:**
- Python 3.11+ / FastAPI
- SQLite (WAL mode)
- SearXNG + DuckDuckGo
- LM Studio / Ollama / OpenAI for LLM

GitHub: https://github.com/LiuChenICBC/ai-search-engine

Would love to hear your feedback!
EOF
)
    echo "标题: $title"
    echo ""
    echo "内容:"
    echo "$content"
    echo ""
    copy_to_clipboard "标题: $title

$content"
    echo ""
    echo "正在打开浏览器..."
    open "https://www.reddit.com/r/selfhosted/submit"
}

get_reddit_python() {
    local title="ai-search-engine: A Python/FastAPI alternative to Perplexica with better security and multi-user support"
    local content=$(cat <<'EOF'
Hi r/Python!

I built a Python implementation of Perplexica-style AI search engine. Here's what makes it different:

**Features:**
- Multi-engine search (SearXNG + DuckDuckGo with fallback)
- Streaming output via SSE
- Dual model architecture (classify with small model, answer with large model)
- Multi-user API key authentication
- Production security (CSRF, SSRF, security headers)
- SQLite - zero external database dependencies

**Why Python/FastAPI?**
- Simpler deployment (just Python 3.11+)
- Better async support
- Easier to extend and customize
- Lower memory footprint

**Quick start:**

```bash
pip install -r requirements.txt
uvicorn main:app --port 8700
```

GitHub: https://github.com/LiuChenICBC/ai-search-engine

Feedback and contributions welcome!
EOF
)
    echo "标题: $title"
    echo ""
    echo "内容:"
    echo "$content"
    echo ""
    copy_to_clipboard "标题: $title

$content"
    echo ""
    echo "正在打开浏览器..."
    open "https://www.reddit.com/r/Python/submit"
}

get_reddit_localllama() {
    local title="Private AI Search Engine in Python - works with Ollama/LM Studio, no cloud dependencies"
    local content=$(cat <<'EOF'
Built a self-hosted AI search engine that works entirely offline with local LLMs.

**Features:**
- Uses SearXNG (self-hosted) or DuckDuckGo for web search
- Sends search results to your local LLM (Ollama/LM Studio) for synthesis
- Streaming answers with source citations
- Multi-user support with API keys
- One-click Docker deployment with SearXNG included

**How it works:**
1. User asks question
2. System classifies query and rewrites for better search
3. Searches multiple engines in parallel
4. Fetches and cleans web content
5. LLM synthesizes answer with citations

**Privacy:**
- 100% local - no data leaves your machine
- SQLite for storage - no external database
- Self-hosted search via SearXNG

GitHub: https://github.com/LiuChenICBC/ai-search-engine
EOF
)
    echo "标题: $title"
    echo ""
    echo "内容:"
    echo "$content"
    echo ""
    copy_to_clipboard "标题: $title

$content"
    echo ""
    echo "正在打开浏览器..."
    open "https://www.reddit.com/r/LocalLLaMA/submit"
}

get_hn() {
    local title="Show HN: ai-search-engine – Python/FastAPI alternative to Perplexica"
    local content=$(cat <<'EOF'
I built a Python-based AI search engine inspired by Perplexica. Here's why:

Perplexica is great but uses TypeScript/Next.js and requires PostgreSQL. I wanted something simpler to deploy with Python.

**Key features:**
- Multi-engine search with automatic fallback (SearXNG → DuckDuckGo)
- Dual model architecture (small model for classification, large for answers)
- Streaming SSE output
- Multi-user API key authentication
- Production security (CSRF, SSRF, security headers)
- SQLite – zero database dependencies
- Docker one-click deployment

**Quick demo:**

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
uvicorn main:app --port 8700
```

GitHub: https://github.com/LiuChenICBC/ai-search-engine

Would appreciate your feedback!
EOF
)
    echo "标题: $title"
    echo ""
    echo "内容:"
    echo "$content"
    echo ""
    copy_to_clipboard "标题: $title

$content"
    echo ""
    echo "正在打开浏览器..."
    open "https://news.ycombinator.com/submitlink"
}

get_twitter_1() {
    local tweet="🚀 Just released ai-search-engine - a Python alternative to Perplexica

✅ Multi-engine search (SearXNG + DuckDuckGo)
✅ Streaming output
✅ Multi-user auth
✅ Production security (CSRF, SSRF)
✅ SQLite - zero dependencies

Deploy in 3 commands:
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt

#Python #AI #OpenSource #SearchEngine"
    echo "推文:"
    echo "$tweet"
    echo ""
    copy_to_clipboard "$tweet"
    echo ""
    echo "正在打开浏览器..."
    open "https://twitter.com/compose/tweet"
}

get_twitter_2() {
    local tweet="Why I built ai-search-engine:

Perplexica uses TypeScript + PostgreSQL 😅

ai-search-engine:
• Python/FastAPI
• SQLite (zero deps)
• Multi-user auth
• CSRF/SSRF protection
• SearXNG + DuckDuckGo fallback

Same AI search, simpler stack.

GitHub: https://github.com/LiuChenICBC/ai-search-engine

#Python #FastAPI #LLM"
    echo "推文:"
    echo "$tweet"
    echo ""
    copy_to_clipboard "$tweet"
    echo ""
    echo "正在打开浏览器..."
    open "https://twitter.com/compose/tweet"
}

get_blog_cn() {
    local file="$PROMOTION_DIR/02-blog-post-cn.md"
    if [ -f "$file" ]; then
        echo "中文博客全文已输出到下方，已复制到剪贴板"
        echo "=========================================="
        cat "$file"
        echo ""
        copy_to_clipboard "$(cat "$file")"
        echo ""
        echo "正在打开浏览器..."
        open "https://juejin.cn/editor/drafts/new"
    else
        echo "文件不存在: $file"
    fi
}

get_blog_en() {
    local file="$PROMOTION_DIR/03-blog-post-en.md"
    if [ -f "$file" ]; then
        echo "英文博客全文已输出到下方，已复制到剪贴板"
        echo "=========================================="
        cat "$file"
        echo ""
        copy_to_clipboard "$(cat "$file")"
        echo ""
        echo "正在打开浏览器..."
        open "https://medium.com/new-story"
    else
        echo "文件不存在: $file"
    fi
}

# 主程序
if [ "$1" != "" ]; then
    case $1 in
        1) get_v2ex ;;
        2) get_zhihu ;;
        3) get掘金 ;;
        4) get_reddit_selfhosted ;;
        5) get_reddit_python ;;
        6) get_reddit_localllama ;;
        7) get_hn ;;
        8) get_twitter_1 ;;
        9) get_twitter_2 ;;
        10) get_blog_cn ;;
        11) get_blog_en ;;
        *) echo "无效选项" ;;
    esac
else
    while true; do
        show_menu
        read -p "请选择 (0-11): " choice
        echo ""
        case $choice in
            1) get_v2ex ;;
            2) get_zhihu ;;
            3) get掘金 ;;
            4) get_reddit_selfhosted ;;
            5) get_reddit_python ;;
            6) get_reddit_localllama ;;
            7) get_hn ;;
            8) get_twitter_1 ;;
            9) get_twitter_2 ;;
            10) get_blog_cn ;;
            11) get_blog_en ;;
            0) echo "退出"; exit 0 ;;
            *) echo "无效选项，请重试" ;;
        esac
        echo ""
        read -p "按回车继续..."
        clear
    done
fi
