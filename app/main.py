"""
FastAPI application entry point.
Wires together all services, agent components, and API routers.
Swagger UI available at http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.planner import AgentPlanner
from app.api.chat import router as chat_router
from app.api.history import router as history_router
from app.config import settings
from app.memory.conversation_memory import ConversationMemory
from app.models.schemas import ErrorResponse
from app.services.gemini_service import GeminiService
from app.services.history_service import HistoryService
from app.services.logging_service import logger
from app.tools.tool_registry import ToolRegistry

# ─── Module-level singletons (used by dependency providers) ───────────────────

memory: ConversationMemory = None  # type: ignore[assignment]
gemini_service: GeminiService = None  # type: ignore[assignment]
tool_registry: ToolRegistry = None  # type: ignore[assignment]
agent_planner: AgentPlanner = None  # type: ignore[assignment]
history_service: HistoryService = None  # type: ignore[assignment]


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize all services on startup and clean up on shutdown."""
    global memory, gemini_service, tool_registry, agent_planner, history_service

    logger.info("Starting School AI ERP Assistant v%s", settings.app_version)

    memory = ConversationMemory(db_path=settings.db_path)
    logger.info("Conversation memory initialized at %s", settings.db_path)

    gemini_service = GeminiService()
    logger.info("Gemini service initialized (model=%s)", settings.gemini_model)

    tool_registry = ToolRegistry()
    logger.info("Tool registry initialized with tools: %s", tool_registry.available_tools)

    agent_planner = AgentPlanner(
        gemini_service=gemini_service,
        memory=memory,
        registry=tool_registry,
    )
    logger.info("Agent planner ready")

    history_service = HistoryService(memory=memory)

    logger.info("School AI ERP Assistant is ready 🎓")
    yield

    logger.info("Shutting down School AI ERP Assistant")


# ─── App factory ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description=(
        "An Agentic AI-powered School ERP Assistant that understands natural language, "
        "plans execution, selects ERP tools automatically, maintains conversation memory, "
        "and generates intelligent responses.\n\n"
        "**Supported queries include:**\n"
        "- Attendance: *'Show my attendance this month'*, *'Can I maintain 90% attendance?'*\n"
        "- Marks: *'Show my Mathematics marks'*, *'Which subject has the highest score?'*\n"
        "- Fees: *'How much fee is pending?'*, *'Show payment history'*\n"
        "- Homework: *'What homework is pending?'*, *'Show overdue assignments'*\n"
        "- Timetable: *'Show tomorrow's timetable'*, *'When is my Mathematics class?'*\n"
        "- Multi-step: *'Show my attendance, marks and pending fees'*\n"
        "- Performance: *'Summarize my academic performance this semester'*"
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception handlers ───────────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            status_code=400,
        ).model_dump(mode="json"),
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="Not Found",
            detail=str(exc),
            status_code=404,
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred. Please try again.",
            status_code=500,
        ).model_dump(mode="json"),
    )


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(history_router, prefix="/api/v1", tags=["History"])


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict:
    """Returns application health status."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "model": settings.gemini_model,
    }


@app.get("/", tags=["Health"], summary="Root – redirects to docs")
async def root() -> dict:
    """Root endpoint with basic info."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }