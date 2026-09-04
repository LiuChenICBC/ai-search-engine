# I Rewrote Perplexica in Python - Better Features, Easier Deployment

## Introduction

AI search engines have been gaining traction recently, with [Perplexica](https://github.com/ItzCrazyKns/Perplexica) being one of the most popular options. However, as a Python developer, I found its TypeScript/Next.js stack and PostgreSQL requirement to be a high barrier to entry.

So I rewrote it using Python/FastAPI, naming it **ai-search-engine**. It retains Perplexica's core functionality while adding significant enhancements in security, multi-user management, and deployment simplicity.

## Why Choose ai-search-engine?

| Aspect | ai-search-engine | Perplexica |
|--------|-----------------|-----------|
| Tech Stack | Python / FastAPI | TypeScript / Next.js |
| Database | SQLite (zero dependencies) | PostgreSQL |
| Deployment | Python 3.11+ only | Node.js + PostgreSQL |
| Multi-user Auth | Built-in API Key + Admin Panel | None (Upcoming) |
| Security | CSRF / SSRF / Headers / Brute-force Protection | Minimal |
| Search Fallback | SearXNG + DuckDuckGo auto-fallback + retry | SearXNG only |
| Dual Model | Small model for classification, large for answers | Single model |
| Chinese Support | Auto query rewriting to English | None |

## Key Features

### 1. Multi-Engine Search Aggregation

- **SearXNG Priority**: Self-hosted meta search engine
- **DuckDuckGo Fallback**: Automatic switch when SearXNG unavailable
- **Parallel Search + Timeout**: Multiple engines simultaneously with timeout control
- **Smart Retry**: Exponential backoff on failure

### 2. Intelligent Research Pipeline

```
User Query
  │
  ▼
Classify (LLM determines search strategy)
  │
  ▼
Search All (parallel multi-engine search + dedup)
  │
  ▼
Extract Multiple (fetch web content + clean)
  │
  ▼
Synthesize (LLM generates answer + citations)
```

### 3. Dual Model Architecture

- **classify_model**: Handles query classification (cost-efficient)
- **model**: Generates comprehensive answers (quality-focused)

### 4. Streaming Output

SSE real-time streaming for better user experience:

```javascript
const eventSource = new EventSource('/api/chat/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'answer_chunk') {
    appendToUI(data.text);
  }
};
```

### 5. Multi-User Authentication

- API Key SHA-256 hashed storage
- Timing-safe comparison (prevents timing attacks)
- Admin panel + usage statistics
- Create/disable/delete users

### 6. Production-Grade Security

- **CSRF Double Submission**: cookie + form token
- **SSRF Protection**: URL protocol whitelist + DNS rebinding prevention
- **Security Headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Brute-force Protection**: 5 attempts/5 minutes
- **Rate Limiting**: slowapi
- **Request Size Limit**: 1MB

## Quick Start

### Prerequisites

- Python 3.11+
- Local LLM service (LM Studio / Ollama) or OpenAI API

### Installation

```bash
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
export WWW_SEARCH_ADMIN_PASSWORD='your-strong-password'
export WWW_SEARCH_SECRET_KEY='your-secret-key-here'
```

### Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8700 --reload
```

Visit http://localhost:8700 for the Web UI.

### Docker One-Click Deploy

```bash
docker-compose --profile searxng up -d
```

## Deployment Options

### Local (Recommended)

Use LM Studio or Ollama as LLM backend. Fully offline, data never leaves your machine.

### Cloud Server

1. Use Docker Compose
2. Configure Nginx reverse proxy
3. Set up Let's Encrypt HTTPS

### Home Server

Deploy on Raspberry Pi or NAS with SearXNG for a private search engine.

## Comparison with Perplexica

Perplexica is an excellent project. ai-search-engine builds on it with:

1. **Simpler Deployment**: No PostgreSQL needed, SQLite zero dependencies
2. **More Secure**: Complete security protection system
3. **Multi-user Support**: Built-in API Key auth and admin panel
4. **More Stable Search**: Multi-engine fallback, automatic degradation
5. **Chinese Optimization**: Auto query rewriting to English

## Project

GitHub: https://github.com/LiuChenICBC/ai-search-engine

Star and PR welcome!

## Conclusion

ai-search-engine is a feature-complete, secure, and simple-to-deploy AI search engine. If you're a Python developer or want a lightweight private search engine, it's a great choice.

For questions or suggestions, please open an issue on GitHub.

---

**Tags**: #AI #SearchEngine #Python #FastAPI #Perplexica #LLM #OpenSource
