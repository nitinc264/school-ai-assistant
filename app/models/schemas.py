"""
Pydantic schemas for all request/response models used across the application.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ─── Request Models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Incoming chat message from a user."""

    message: str = Field(..., description="Natural language query from the user")
    student_id: str = Field(default="STU001", description="Student identifier")
    session_id: str = Field(default="default", description="Session identifier for conversation memory")

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message must not be empty or whitespace.")
        return v.strip()

    @field_validator("student_id")
    @classmethod
    def student_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("student_id must not be empty.")
        return v.strip().upper()


# ─── Tool Models ───────────────────────────────────────────────────────────────

class ToolCallPlan(BaseModel):
    """Represents a single planned tool invocation."""

    tool_name: str = Field(..., description="Name of the ERP tool to call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the tool")


class ExecutionPlan(BaseModel):
    """The AI agent's execution plan before running tools."""

    intent: str = Field(..., description="Detected user intent")
    tools: List[str] = Field(..., description="List of tool names to invoke")
    reasoning: str = Field(..., description="AI reasoning for this plan")
    is_multi_step: bool = Field(default=False, description="Whether multiple tools are required")
    is_performance_summary: bool = Field(default=False, description="Whether this is an academic summary request")


class ToolResult(BaseModel):
    """Result from a single ERP tool execution."""

    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─── Response Models ───────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    """Structured response returned to the client after processing a chat message."""

    intent: str = Field(..., description="Detected intent")
    tool: str = Field(..., description="Primary ERP tool used")
    response: str = Field(..., description="Natural language response from the AI")
    status: str = Field(..., description="Status indicator e.g. Good, Pending, Warning")
    execution_plan: ExecutionPlan = Field(..., description="The agent's execution plan")
    tool_results: List[ToolResult] = Field(default_factory=list, description="Raw results from each tool")
    session_id: str = Field(..., description="Session ID for this conversation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HistoryEntry(BaseModel):
    """A single entry in the conversation history."""

    id: int
    session_id: str
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    intent: Optional[str] = None
    timestamp: str


class HistoryResponse(BaseModel):
    """Response for GET /chat/history."""

    session_id: str
    total_messages: int
    messages: List[HistoryEntry]


# ─── Error Models ──────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)