"""
History Service – provides a clean API for conversation history retrieval.
Acts as the service layer between the API endpoints and the memory layer.
"""

from typing import List

from app.memory.conversation_memory import ConversationMemory
from app.models.schemas import HistoryEntry, HistoryResponse


class HistoryService:
    """Service layer for reading and managing conversation history."""

    def __init__(self, memory: ConversationMemory) -> None:
        self._memory = memory

    def get_history(self, session_id: str, limit: int = 20) -> HistoryResponse:
        """
        Retrieve formatted conversation history for a session.

        Args:
            session_id: Session to retrieve history for.
            limit: Maximum messages to return.

        Returns:
            HistoryResponse with all messages.
        """
        raw_messages = self._memory.get_history(session_id, limit=limit)
        entries = [
            HistoryEntry(
                id=msg["id"],
                session_id=msg["session_id"],
                role=msg["role"],
                content=msg["content"],
                intent=msg.get("intent"),
                timestamp=msg["timestamp"],
            )
            for msg in raw_messages
        ]
        return HistoryResponse(
            session_id=session_id,
            total_messages=len(entries),
            messages=entries,
        )