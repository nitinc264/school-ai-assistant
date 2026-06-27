"""
Chat API endpoint – POST /chat
Accepts a natural language message and returns an AI-generated ERP response.
"""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.planner import AgentPlanner
from app.models.schemas import ChatRequest, ChatResponse
from app.services.logging_service import logging_service

router = APIRouter()


def get_agent_planner() -> AgentPlanner:
    """Dependency provider for AgentPlanner. Pulls from app state."""
    from app.main import agent_planner
    return agent_planner


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the School ERP AI Assistant",
    description=(
        "Send a natural language query. The AI agent will detect your intent, "
        "select the appropriate ERP tool(s), fetch the data, and return a structured response. "
        "Conversation history is maintained per session_id."
    ),
    responses={
        200: {"description": "Successful AI response with ERP data"},
        400: {"description": "Empty or invalid message"},
        404: {"description": "Student not found"},
        503: {"description": "AI service unavailable"},
    },
)
async def chat(
    request: ChatRequest,
    planner: Annotated[AgentPlanner, Depends(get_agent_planner)],
) -> ChatResponse:
    """
    Process a natural language query through the AI agent pipeline.

    - Validates the request
    - Runs the agent planner (intent detection → tool execution → response generation)
    - Returns a structured ChatResponse
    """
    try:
        response = planner.process(
            message=request.message,
            student_id=request.student_id,
            session_id=request.session_id,
        )
        return response

    except KeyError as exc:
        logging_service.log_interaction(
            session_id=request.session_id,
            user_query=request.message,
            intent="Unknown",
            execution_plan={},
            tools_called=[],
            execution_time_ms=0,
            response_summary="",
            status="error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except ValueError as exc:
        logging_service.log_interaction(
            session_id=request.session_id,
            user_query=request.message,
            intent="Unknown",
            execution_plan={},
            tools_called=[],
            execution_time_ms=0,
            response_summary="",
            status="error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except RuntimeError as exc:
        logging_service.log_interaction(
            session_id=request.session_id,
            user_query=request.message,
            intent="Unknown",
            execution_plan={},
            tools_called=[],
            execution_time_ms=0,
            response_summary="",
            status="error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(exc)}",
        )

    except Exception as exc:
        logging_service.log_interaction(
            session_id=request.session_id,
            user_query=request.message,
            intent="Unknown",
            execution_plan={},
            tools_called=[],
            execution_time_ms=0,
            response_summary="",
            status="error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(exc)}",
        )