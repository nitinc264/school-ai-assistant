"""
SQLite-backed conversation memory.
Stores and retrieves conversation history per session to enable multi-turn context.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings


class ConversationMemory:
    """
    Manages conversation history using SQLite.
    Each session maintains its own thread of messages.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or settings.db_path
        self._ensure_db_directory()
        self._initialize_db()

    def _ensure_db_directory(self) -> None:
        """Create the database directory if it does not exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Return a new SQLite connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self) -> None:
        """Create the conversations table if it does not exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT    NOT NULL,
            role        TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
            content     TEXT    NOT NULL,
            intent      TEXT,
            timestamp   TEXT    NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id);
        """
        with self._get_connection() as conn:
            conn.executescript(create_table_sql)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
    ) -> None:
        """
        Persist a single message to the conversation history.

        Args:
            session_id: Unique identifier for the conversation session.
            role: Either 'user' or 'assistant'.
            content: The text content of the message.
            intent: Optional detected intent label for assistant messages.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, role, content, intent, timestamp) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, intent, timestamp),
            )

    def get_history(
        self,
        session_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation history for a session.

        Args:
            session_id: The session to retrieve history for.
            limit: Maximum number of messages to return (most recent first).

        Returns:
            List of message dicts ordered chronologically (oldest first).
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, session_id, role, content, intent, timestamp
                FROM conversations
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        # Reverse so oldest messages come first (chronological order for context)
        return [dict(row) for row in reversed(rows)]

    def get_formatted_for_gemini(
        self,
        session_id: str,
        limit: int = 20,
    ) -> List[Dict[str, str]]:
        """
        Return conversation history formatted for Gemini's chat API.

        Args:
            session_id: The session to retrieve history for.
            limit: Maximum messages to include.

        Returns:
            List of {'role': ..., 'parts': [{'text': ...}]} dicts.
        """
        history = self.get_history(session_id, limit)
        formatted = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            formatted.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })
        return formatted

    def clear_session(self, session_id: str) -> int:
        """
        Delete all messages for a given session.

        Args:
            session_id: Session to clear.

        Returns:
            Number of rows deleted.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (session_id,),
            )
            return cursor.rowcount

    def count_messages(self, session_id: str) -> int:
        """Return the total number of messages in a session."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM conversations WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            return row["cnt"] if row else 0