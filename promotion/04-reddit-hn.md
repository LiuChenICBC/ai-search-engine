# Reddit / Hacker News 帖子文案

## Reddit - r/selfhosted

### Title
I built a Python alternative to Perplexica - easier deployment, better security, multi-user support

### Body
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

---

## Reddit - r/Python

### Title
ai-search-engine: A Python/FastAPI alternative to Perplexica with better security and multi-user support

### Body
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

---

## Reddit - r/LocalLLaMA

### Title
Private AI Search Engine in Python - works with Ollama/LM Studio, no cloud dependencies

### Body
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

---

## Hacker News - Show HN

### Title
Show HN: ai-search-engine – Python/FastAPI alternative to Perplexica

### Body
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
