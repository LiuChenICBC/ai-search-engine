"""应用常量配置"""

import os

# Session 配置
SESSION_MAX_AGE = 3600  # 秒 (1 小时)
SESSION_COOKIE_MAX_AGE = 7200  # 秒 (2 小时 - admin cookie)
CSRF_TOKEN_BYTES = 32  # CSRF token 字节数

# 登录速率限制
MAX_LOGIN_ATTEMPTS = 5  # 最大尝试次数
LOGIN_WINDOW_SECONDS = 300  # 时间窗口 (5 分钟)
MAX_LOGIN_TRACKED_IPS = 10000  # 最大跟踪 IP 数

# 用户名限制
MAX_USERNAME_LENGTH = 64

# 查询限制
MAX_QUERY_LENGTH = 500

# 速率限制
DEFAULT_RATE_LIMIT = "60/minute"
CHAT_RATE_LIMIT = "30/minute"
CONFIG_RATE_LIMIT = "10/minute"

# 数据库
DB_FILENAME = "www_search.db"

# 使用记录
MAX_QUERY_LENGTH_USAGE = 500  # 截断 query 长度
DEFAULT_USAGE_LIMIT = 100  # 默认使用记录限制
MAX_USAGE_LIMIT = 200  # 最大使用记录限制

# 抓取配置
DEFAULT_FETCH_TIMEOUT = 15.0  # 秒
MAX_REDIRECTS = 5
MAX_RETRIES = 2
BASE_RETRY_DELAY = 1.0  # 秒
MAX_CONTENT_LENGTH = 8000  # 字符
FETCH_PARALLEL_TIMEOUT = 45  # 并行抓取总超时 (秒)
FETCH_MAX_WORKERS = 4  # 并行抓取最大线程数
MIN_PARAGRAPH_LENGTH = 20  # 过滤短片段的最小长度

# LLM 配置
DEFAULT_LLM_TIMEOUT = 120  # 秒
DEFAULT_LLM_RETRIES = 3
CLASSIFY_TIMEOUT = 240  # 分类超时 (秒)
CLASSIFY_MAX_TOKENS = 8192  # 分类最大 token 数（模型有思考过程，需要足够空间）

# 搜索配置
SEARCH_PARALLEL_TIMEOUT = 30  # 并行搜索总超时 (秒)
DEFAULT_MAX_RESULTS = 10  # 默认最大搜索结果数
DEFAULT_MAX_SCRAPE = 6  # 默认抓取页面数（多抓几页保证信息充分）
SOURCE_SNIPPET_LENGTH = 200  # 来源摘要截断长度

# DNS 解析
DNS_RESOLVE_TIMEOUT = 5.0  # 秒

# 服务器配置
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8700

# Cookie 安全配置（生产环境设 WWW_SEARCH_SECURE_COOKIES=1）
SECURE_COOKIES = os.environ.get("WWW_SEARCH_SECURE_COOKIES", "0") == "1"

# 请求大小限制
MAX_REQUEST_BODY_SIZE = 1024 * 1024  # 1MB

# 安全头
X_FRAME_OPTIONS = "DENY"
HSTS_MAX_AGE = "max-age=2592000; includeSubDomains; preload"
REFERRER_POLICY = "strict-origin-when-cross-origin"
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; frame-ancestors 'none'"
)
