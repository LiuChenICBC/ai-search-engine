# Twitter/X 推文文案

## 主推文

### 版本 1（特性介绍）
🚀 Just released ai-search-engine - a Python alternative to Perplexica

✅ Multi-engine search (SearXNG + DuckDuckGo)
✅ Streaming output
✅ Multi-user auth
✅ Production security (CSRF, SSRF)
✅ SQLite - zero dependencies

Deploy in 3 commands:
```
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
```

#Python #AI #OpenSource #SearchEngine

---

### 版本 2（对比 Perplexica）
Why I built ai-search-engine:

Perplexica uses TypeScript + PostgreSQL 😅

ai-search-engine:
• Python/FastAPI
• SQLite (zero deps)
• Multi-user auth
• CSRF/SSRF protection
• SearXNG + DuckDuckGo fallback

Same AI search, simpler stack.

GitHub: https://github.com/LiuChenICBC/ai-search-engine

#Python #FastAPI #LLM

---

### 版本 3（隐私/自托管）
Build your own private AI search engine 🔍

ai-search-engine:
• 100% local - no data leaves your machine
• Works with Ollama/LM Studio
• Self-hosted search via SearXNG
• Multi-user support
• One-click Docker deploy

Perfect for privacy-conscious users.

GitHub: https://github.com/LiuChenICBC/ai-search-engine

#SelfHosted #Privacy #AI

---

## 系列推文

### Thread 1/4
🧵 Thread: Why I built ai-search-engine

The AI search space is heating up. Perplexica is great, but as a Python developer, I wanted something simpler to deploy.

So I built ai-search-engine - a Python/FastAPI alternative with better security and multi-user support.

---

### Thread 2/4
Key features:

1️⃣ Multi-engine search - SearXNG + DuckDuckGo with automatic fallback
2️⃣ Dual model architecture - small model for classification, large for answers
3️⃣ Streaming output via SSE
4️⃣ Production security - CSRF, SSRF, brute-force protection

---

### Thread 3/4
Why Python?

• No PostgreSQL needed (SQLite)
• Simpler deployment (just Python 3.11+)
• Better async with FastAPI
• Easier to extend

Deploy in 3 commands:
```
git clone https://github.com/LiuChenICBC/ai-search-engine.git
cd ai-search-engine
pip install -r requirements.txt
```

---

### Thread 4/4
Perfect for:
• Privacy-conscious users
• Self-hosters
• Python developers
• Small teams

GitHub: https://github.com/LiuChenICBC/ai-search-engine

Star ⭐ and PR welcome!

#Python #AI #OpenSource #SearchEngine #Perplexica

---

## 产品更新推文

### v1.0.0 发布
🎉 v1.0.0 released!

ai-search-engine is now production-ready:
• Multi-engine search
• Multi-user auth
• Production security
• Docker deployment

Try it now: https://github.com/LiuChenICBC/ai-search-engine

#Python #AI #Release

---

### 新功能发布
✨ New feature: Dual model architecture

Now you can use a small model for query classification (saves costs) and a large model for generating answers (better quality).

Configure in config.yaml:
```yaml
llm:
  model: "gpt-4"
  classify_model: "gpt-3.5"
```

#AI #LLM #Python

---

## 互动推文

### 提问式
Building a private AI search engine? 🤔

What's more important to you?
• Privacy (local LLM)
• Features (multi-user, admin panel)
• Simplicity (easy deployment)

ai-search-engine has all three 🔥

GitHub: https://github.com/LiuChenICBC/ai-search-engine

---

### 对比式
Perplexica vs ai-search-engine:

TypeScript + PostgreSQL vs Python + SQLite
Single model vs Dual model
No auth vs Multi-user auth
Basic security vs Production security

Choose based on your needs 🤷‍♂️

Both are open source ❤️

#AI #OpenSource
