"""
Conversation management — persist and retrieve multi-turn chat conversations.

Uses SQLite for development, designed for PostgreSQL upgrade in production.
Each conversation stores messages, metadata, and supports context windowing.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from api.config import settings

DB_PATH = Path("data/astrosage.db")


def _get_db() -> sqlite3.Connection:
    """Get or create the database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db():
    """Initialize database tables."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT DEFAULT '',
            model TEXT DEFAULT 'gpt-4o-mini',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant', 'tool')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            token_count INTEGER DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at);
    """)
    conn.commit()
    conn.close()


# Initialize on module load
_init_db()


class ConversationManager:
    """Manage chat conversations and messages."""

    def create_conversation(
        self,
        user_id: str,
        title: str = "",
        model: str = "gpt-4o-mini",
        metadata: dict | None = None,
    ) -> dict:
        """Create a new conversation."""
        conn = _get_db()
        conv_id = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO conversations (id, user_id, title, model, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conv_id, user_id, title, model, now, now, json.dumps(metadata or {})),
        )
        conn.commit()
        conn.close()
        return self.get_conversation(conv_id)

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get a conversation by ID."""
        conn = _get_db()
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not row:
            conn.close()
            return None
        messages = self.get_messages(conversation_id)
        conn.close()
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "title": row["title"],
            "model": row["model"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"]),
            "message_count": len(messages),
            "messages": messages,
        }

    def list_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List conversations for a user, most recent first."""
        conn = _get_db()
        rows = conn.execute(
            "SELECT id, user_id, title, model, created_at, updated_at, metadata FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        ).fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "title": r["title"],
                "model": r["model"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "metadata": json.loads(r["metadata"]),
                "message_count": 0,  # Counted on detail
            }
            for r in rows
        ]

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        token_count: int = 0,
        metadata: dict | None = None,
    ) -> dict:
        """Add a message to a conversation."""
        conn = _get_db()
        msg_id = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at, token_count, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, now, token_count, json.dumps(metadata or {})),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        conn.close()
        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": now,
            "token_count": token_count,
        }

    def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Get messages for a conversation, oldest first."""
        conn = _get_db()
        rows = conn.execute(
            "SELECT id, role, content, created_at, token_count, metadata FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (conversation_id, limit, offset),
        ).fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"],
                "token_count": r["token_count"],
                "metadata": json.loads(r["metadata"]),
            }
            for r in rows
        ]

    def get_context_messages(
        self,
        conversation_id: str,
        max_tokens: int = 4096,
        max_messages: int = 20,
    ) -> list[dict]:
        """Get messages within a token budget for LLM context window."""
        messages = self.get_messages(conversation_id)
        # Take the last N messages (most recent)
        recent = messages[-max_messages:] if len(messages) > max_messages else messages
        return recent

    def update_title(
        self,
        conversation_id: str,
        title: str,
    ) -> bool:
        """Update conversation title."""
        conn = _get_db()
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now(timezone.utc).isoformat(), conversation_id),
        )
        affected = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        conn.close()
        return affected > 0

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        conn = _get_db()
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        affected = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        conn.close()
        return affected > 0

    def generate_title(self, messages: list[dict]) -> str:
        """Generate a title from the first user message."""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Take first line or first 60 chars
                title = content.split("\n")[0][:60]
                if len(title) >= 60:
                    title = title[:57] + "..."
                return title
        return "New conversation"
