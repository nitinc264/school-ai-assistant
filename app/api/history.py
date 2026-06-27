"""
History API endpoint – GET /chat/history
Returns the conversation history for a given session.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.models.schemas import HistoryResponse
from app.services.history_service import HistoryService

router = APIRouter()


def get_history_service() -> HistoryService:
    """Dependency provider for HistoryService."""
    from app.main import history_service
    return history_service


@router.get(
    "/chat/history",
    response_model=HistoryResponse,
    summary="Retrieve conversation history",
    description=(
        "Fetch the stored conversation history for a given session. "
        "History is ordered chronologically (oldest first). "
        "Useful for debugging, auditing, or displaying past conversations."
    ),
    responses={
        200: {"description": "Conversation history for the session"},
    },
)
async def get_chat_history(
    session_id: str = Query(default="default", description="Session identifier"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of messages to return"),
    service: Annotated[HistoryService, Depends(get_history_service)] = None,
) -> HistoryResponse:
    """
    Return conversation history for the specified session.

    Args:
        session_id: The session to retrieve history for.
        limit: Maximum number of messages (1-100).
    """
    return service.get_history(session_id=session_id, limit=limit)