# 部署指南

## 部署方式

- [Mac 单机部署](#mac-单机部署)（推荐开发/个人使用）
- [Docker 部署](#docker-部署)（推荐生产环境）
- [生产环境注意事项](#生产环境注意事项)

---

## Mac 单机部署

### 环境要求

- macOS 12+ (Monterey 或更高)
- Python 3.11+
- 本地 LLM 服务（LM Studio 或 Ollama）

### 步骤 1: 安装 Python 环境

```bash
# 使用 pyenv 管理 Python 版本（推荐）
brew install pyenv

# 安装 Python 3.11
pyenv install 3.11.15
pyenv local 3.11.15

# 或者使用系统 Python
python3 --version  # 确认 >= 3.11
```

### 步骤 2: 安装 LLM 服务

#### 方案 A: LM Studio（推荐，支持更多模型）

1. 下载并安装 [LM Studio](https://lmstudio.ai/)
2. 下载模型（如 Qwen3.6-35B-A3B）
3. 启动本地服务器:
   - 点击 "Local Server" 标签
   - 选择模型
   - 点击 "Start Server"
   - 默认端口: `1234`

#### 方案 B: Ollama

```bash
# 安装 Ollama
brew install ollama

# 启动服务
ollama serve

# 拉取模型
ollama pull qwen3:8b
```

### 步骤 3: 安装项目依赖

```bash
# 克隆项目
git clone <repo-url>
cd ai-search-engine

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 4: 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
# 管理后台密码（必须设置）
WWW_SEARCH_ADMIN_PASSWORD='your-strong-password-here'

# Session 签名密钥（必须设置）
WWW_SEARCH_SECRET_KEY=*** -c 'import secrets; print(secrets.token_hex(32))')

# LLM API Key（可选，覆盖 config.yaml）
# WWW_SEARCH_LLM_API_KEY='your-llm-api-key'

# 开发模式自动重载（可选）
# WWW_SEARCH_RELOAD='true'
EOF

# 加载环境变量
export $(cat .env | xargs)
```

### 步骤 5: 配置 config.yaml

```yaml
# LLM 设置
llm:
  api_base: "http://localhost:1234/v1"  # LM Studio 默认端口
  # api_base: "http://localhost:11434/v1"  # Ollama 默认端口
  api_key: "lm-studio"  # 可通过 WWW_SEARCH_LLM_API_KEY 覆盖
  model: "default"
  temperature: 0.3
  max_tokens: 4096

# 搜索设置
search:
  searxng_url: ""  # 留空则使用 DuckDuckGo
  use_ddgs: true
  max_results: 8
  max_scrape: 4

# 服务器设置
server:
  host: "0.0.0.0"
  port: 8700
  cors_origins: ["http://localhost:8700"]
```

### 步骤 6: 启动服务

```bash
# 开发模式（自动重载）
uvicorn main:app --host 0.0.0.0 --port 8700 --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8700 --workers 1
```

### 步骤 7: 验证部署

```bash
# 检查健康状态
curl http://localhost:8700/api/health

# 预期响应:
# {"status": "ok", "service": "ai-search-engine", "llm": "connected"}
```

访问 http://localhost:8700 打开 Web UI。

### 步骤 8: 创建第一个 API Key

1. 访问 http://localhost:8700/admin/login
2. 使用设置的密码登录
3. 进入 "创建用户" 页面
4. 输入用户名，点击创建
5. **保存显示的 API Key**（只显示一次）

### 后台运行（可选）

```bash
# 使用 nohup 后台运行
nohup uvicorn main:app --host 0.0.0.0 --port 8700 > ai-search-engine.log 2>&1 &

# 查看日志
tail -f ai-search-engine.log

# 停止服务
lsof -ti:8700 | xargs kill
```

### 使用 launchd 开机自启（可选）

```bash
# 创建 plist 文件
cat > ~/Library/LaunchAgents/com.wwwsearch.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wwwsearch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourname/projects/ai-search-engine/.venv/bin/uvicorn</string>
        <string>main:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8700</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yourname/projects/ai-search-engine</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>WWW_SEARCH_ADMIN_PASSWORD</key>
        <string>your-password</string>
        <key>WWW_SEARCH_SECRET_KEY</key>
        <string>your-secret-key</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/yourname/projects/ai-search-engine/ai-search-engine.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourname/projects/ai-search-engine/ai-search-engine.error.log</string>
</dict>
</plist>
EOF

# 加载服务
launchctl load ~/Library/LaunchAgents/com.wwwsearch.plist

# 查看状态
launchctl list | grep wwwsearch

# 停止服务
launchctl unload ~/Library/LaunchAgents/com.wwwsearch.plist
```

---

## Docker 部署

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8700

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8700/api/health')" || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8700"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  ai-search-engine:
    build: .
    ports:
      - "8700:8700"
    environment:
      - WWW_SEARCH_ADMIN_PASSWORD=${WWW_SEARCH_ADMIN_PASSWORD}
      - WWW_SEARCH_SECRET_KEY=${WWW_SEARCH_SECRET_KEY}
      - WWW_SEARCH_LLM_API_KEY=${WWW_SEARCH_LLM_API_KEY}
    volumes:
      - ./data:/app/data  # 持久化数据库
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8700/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 启动

```bash
# 设置环境变量
export WWW_SEARCH_ADMIN_PASSWORD='your-password'
export WWW_SEARCH_SECRET_KEY=*** -c 'import secrets; print(secrets.token_hex(32))')

# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

---

## 生产环境注意事项

### 1. 安全配置

- **HTTPS**: 使用反向代理（Nginx/Caddy）终止 TLS
- **SECRET_KEY**: 使用强随机密钥，定期轮换
- **ADMIN_PASSWORD**: 使用强密码，定期更换
- **CORS**: 限制 `cors_origins` 为实际域名

### 2. 性能优化

- **workers**: 根据 CPU 核心数设置 `--workers`
- **数据库**: SQLite WAL 模式已启用，适合读多写少场景
- **缓存**: 考虑添加 Redis 缓存搜索结果

### 3. 监控

- **日志**: 配置日志轮转（logrotate）
- **健康检查**: 使用 `/api/health` 端点
- **指标**: 管理后台提供使用统计

### 4. 备份

```bash
# 备份数据库
cp www_search.db www_search.db.backup.$(date +%Y%m%d)

# 备份配置
tar czf config_backup.tar.gz config.yaml .env
```

### 5. 更新

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt

# 重启服务
# Mac: launchctl unload/load ~/Library/LaunchAgents/com.wwwsearch.plist
# Docker: docker compose up -d --build
```
