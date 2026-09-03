"""SQLite 数据库层 - API Key 认证 + 使用统计"""

import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

from config.constants import DEFAULT_USAGE_LIMIT, MAX_QUERY_LENGTH_USAGE

logger = logging.getLogger("www_search.db")


DB_PATH = os.path.join(os.path.dirname(__file__), "www_search.db")


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数（按 1 token ≈ 4 字符粗略估算）"""
    # 中文字符每个约 1.5 token，英文每 3-4 字符 1 token
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", text))
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars / 3.5 + 0.5)


def _hash_key(api_key: str) -> str:
    """SHA-256 哈希 API Key（永不存明文）"""
    return hashlib.sha256(api_key.encode()).hexdigest()


# 时序安全比较的 dummy 值（防止时序攻击泄露"用户是否存在"）
_DUMMY_HASH = "0" * 64


def _generate_key() -> str:
    """生成随机 API Key (64 字符 hex)"""
    return secrets.token_hex(32)


@contextmanager
def get_db():
    """获取数据库连接（上下文管理器）"""
    ensure_db()  # 懒初始化：首次使用时创建表
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库表（使用直接连接避免通过 get_db() 导致递归）"""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                api_key_hash TEXT UNIQUE NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                total_tokens INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT,
                tokens_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_records(user_id);
            CREATE INDEX IF NOT EXISTS idx_usage_time ON usage_records(created_at);
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_user(username: str) -> dict:
    """创建用户，生成 API Key（只返回一次）"""
    api_key = _generate_key()
    api_key_hash = _hash_key(api_key)

    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, api_key_hash) VALUES (?, ?)",
                (username, api_key_hash),
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"用户名已存在: {username}")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return {
        "id": user_id,
        "username": username,
        "api_key": api_key,  # ⚠️ 只显示这一次！
        "api_key_hash": api_key_hash,
        "enabled": True,
        "created_at": datetime.now().isoformat(),
        "total_tokens": 0,
    }


def verify_api_key(api_key: str) -> dict | None:
    """验证 API Key（时序安全比较）"""
    api_key_hash = _hash_key(api_key)

    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE api_key_hash = ? AND enabled = 1",
            (api_key_hash,),
        ).fetchone()

        if user is None:
            # dummy 比较：防止时序攻击泄露"用户是否存在"
            hmac.compare_digest(api_key_hash, _DUMMY_HASH)
            return None

        # 时序安全比较（SQL WHERE 已做哈希匹配，此处为防御性检查）
        stored_hash = user["api_key_hash"]
        if not hmac.compare_digest(api_key_hash, stored_hash):
            return None

        # 更新 last_used_at（仅在 key 有效时更新）
        conn.execute(
            "UPDATE users SET last_used_at = ? WHERE id = ?",
            (datetime.now().isoformat(), user["id"]),
        )

        return dict(user)


def record_usage(user_id: int, query: str = "", tokens_used: int = 0):
    """记录使用量"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO usage_records (user_id, query, tokens_used) VALUES (?, ?, ?)",
            (user_id, query[:MAX_QUERY_LENGTH_USAGE], tokens_used),  # 截断 query 防过大
        )
        conn.execute(
            "UPDATE users SET total_tokens = total_tokens + ? WHERE id = ?",
            (tokens_used, user_id),
        )


def get_user(user_id: int) -> dict | None:
    """获取用户信息"""
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(user) if user else None


def get_all_users() -> list[dict]:
    """获取所有用户（不含 api_key_hash）"""
    with get_db() as conn:
        users = conn.execute(
            "SELECT id, username, enabled, created_at, last_used_at, total_tokens "
            "FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [dict(u) for u in users]


def toggle_user(user_id: int) -> dict:
    """启用/禁用用户"""
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            raise ValueError(f"User {user_id} not found")

        new_enabled = 0 if user["enabled"] else 1
        conn.execute(
            "UPDATE users SET enabled = ? WHERE id = ?",
            (new_enabled, user_id),
        )
        return dict(
            conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        )


def regenerate_key(user_id: int) -> dict:
    """重新生成 API Key（旧 Key 立即失效）"""
    new_key = _generate_key()
    new_hash = _hash_key(new_key)

    with get_db() as conn:
        # 在同一事务内读取和更新，避免 TOCTOU 竞态
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            raise ValueError(f"User {user_id} not found")

        conn.execute(
            "UPDATE users SET api_key_hash = ? WHERE id = ?",
            (new_hash, user_id),
        )

    return {
        "id": user["id"],
        "username": user["username"],
        "api_key": new_key,  # ⚠️ 只显示这一次！
        "enabled": bool(user["enabled"]),
        "created_at": user["created_at"],
        "total_tokens": user["total_tokens"],
    }


def get_usage_stats(user_id: int, limit: int = DEFAULT_USAGE_LIMIT) -> list[dict]:
    """获取用户使用记录"""
    with get_db() as conn:
        records = conn.execute(
            "SELECT id, query, tokens_used, created_at "
            "FROM usage_records WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in records]


def get_global_stats() -> dict:
    """获取全局统计"""
    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        enabled_users = conn.execute(
            "SELECT COUNT(*) FROM users WHERE enabled = 1"
        ).fetchone()[0]
        total_records = conn.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0]
        total_tokens = conn.execute(
            "SELECT COALESCE(SUM(total_tokens), 0) FROM users"
        ).fetchone()[0]

        # 最近 7 天使用趋势
        daily_usage = conn.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as count, COALESCE(SUM(tokens_used), 0) as tokens "
            "FROM usage_records WHERE created_at >= datetime('now', '-7 days') "
            "GROUP BY DATE(created_at) ORDER BY day"
        ).fetchall()

        return {
            "total_users": total_users,
            "enabled_users": enabled_users,
            "disabled_users": total_users - enabled_users,
            "total_records": total_records,
            "total_tokens": total_tokens,
            "daily_usage": [dict(d) for d in daily_usage],
        }


_db_initialized = False
_db_init_failed = False
_db_lock = threading.Lock()  # 保护 ensure_db() 的线程安全


def ensure_db():
    """确保数据库已初始化（懒初始化，失败后可重试）"""
    global _db_initialized, _db_init_failed
    with _db_lock:
        if _db_initialized:
            return
        if _db_init_failed:
            # 上次失败后重试
            _db_init_failed = False
        try:
            init_db()
            _db_initialized = True
        except Exception as e:
            _db_init_failed = True
            logger.error(f"[db] 数据库初始化失败: {e}")
            raise


# 在首次使用数据库时自动初始化（不再在 import 时执行）
# init_db() 改为由 get_db() 内部调用 ensure_db()
# 保留兼容：任何调用 get_db 的地方都会触发初始化
