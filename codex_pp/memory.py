"""
memory.py - 持久化记忆
===================
- 对话历史(SQLite)
- 项目上下文
- 用户偏好
- 跨会话保持
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

DB_DIR = Path.home() / ".codex-pp"
DB_FILE = DB_DIR / "memory.db"


def ensure_db():
    """确保数据库存在"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_message(session_id: str, role: str, content: str):
    """保存一条对话消息"""
    conn = ensure_db()
    conn.execute(
        "INSERT INTO conversations (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, time.time()),
    )
    conn.commit()
    conn.close()


def get_conversation(session_id: str, limit: int = 50) -> list:
    """获取会话历史"""
    conn = ensure_db()
    cur = conn.execute(
        "SELECT role, content, created_at FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {"role": r[0], "content": r[1], "created_at": r[2]}
        for r in reversed(rows)
    ]


def clear_conversation(session_id: str):
    """清空会话历史"""
    conn = ensure_db()
    conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def set_memory(key: str, value):
    """存储一个记忆项"""
    conn = ensure_db()
    conn.execute(
        "INSERT OR REPLACE INTO memories (key, value, updated_at) VALUES (?, ?, ?)",
        (key, json.dumps(value, ensure_ascii=False), time.time()),
    )
    conn.commit()
    conn.close()


def get_memory(key: str, default=None):
    """读取一个记忆项"""
    conn = ensure_db()
    cur = conn.execute("SELECT value FROM memories WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return row[0]
    return default


def list_memories() -> list:
    """列出所有记忆项"""
    conn = ensure_db()
    cur = conn.execute("SELECT key, value, updated_at FROM memories ORDER BY updated_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [
        {"key": r[0], "value": r[1], "updated_at": r[2]}
        for r in rows
    ]


def delete_memory(key: str) -> bool:
    """删除一个记忆项"""
    conn = ensure_db()
    cur = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_stats() -> dict:
    """获取记忆统计"""
    conn = ensure_db()
    cur1 = conn.execute("SELECT COUNT(*) FROM conversations")
    msg_count = cur1.fetchone()[0]
    cur2 = conn.execute("SELECT COUNT(*) FROM memories")
    mem_count = cur2.fetchone()[0]
    cur3 = conn.execute("SELECT COUNT(DISTINCT session_id) FROM conversations")
    sess_count = cur3.fetchone()[0]
    conn.close()
    return {
        "messages": msg_count,
        "memories": mem_count,
        "sessions": sess_count,
    }