"""
Logging Service – structured JSON logging for every agent interaction.
Logs are appended to logs/agent_logs.json and also written to Python's logging system.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

# Configure Python root logger
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger("school_erp")


class LoggingService:
    """
    Appends structured interaction logs to a JSON lines file.
    Each interaction (one user query → one response) is a single JSON object.
    """

    def __init__(self) -> None:
        self._logs_dir: Path = settings.logs_dir
        self._log_file: Path = self._logs_dir / settings.agent_log_file
        self._ensure_log_file()

    def _ensure_log_file(self) -> None:
        """Create the logs directory and empty log array if not present."""
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        if not self._log_file.exists():
            self._log_file.write_text("[]", encoding="utf-8")

    def log_interaction(
        self,
        session_id: str,
        user_query: str,
        intent: str,
        execution_plan: Dict[str, Any],
        tools_called: List[str],
        execution_time_ms: float,
        response_summary: str,
        status: str = "success",
        error: Optional[str] = None,
    ) -> None:
        """
        Append a structured log entry for one agent interaction.

        Args:
            session_id: Session identifier.
            user_query: The raw user message.
            intent: Detected intent label.
            execution_plan: The full execution plan dict.
            tools_called: List of tool names that were invoked.
            execution_time_ms: Total processing time in milliseconds.
            response_summary: First 200 chars of the generated response.
            status: 'success' or 'error'.
            error: Error message if status is 'error'.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "user_query": user_query,
            "intent": intent,
            "execution_plan": execution_plan,
            "tools_called": tools_called,
            "execution_time_ms": round(execution_time_ms, 2),
            "response_summary": response_summary[:200],
            "status": status,
            "error": error,
        }

        # Append to JSON file
        self._append_to_file(entry)

        # Also log to Python logger
        if status == "success":
            logger.info(
                "Chat interaction | session=%s | intent=%s | tools=%s | time=%.0fms",
                session_id, intent, tools_called, execution_time_ms,
            )
        else:
            logger.error(
                "Chat error | session=%s | intent=%s | error=%s",
                session_id, intent, error,
            )

    def _append_to_file(self, entry: Dict[str, Any]) -> None:
        """Safely append a log entry to the JSON array file."""
        try:
            content = self._log_file.read_text(encoding="utf-8").strip()
            logs: List[Dict[str, Any]] = json.loads(content) if content else []
        except (json.JSONDecodeError, OSError):
            logs = []

        logs.append(entry)

        # Keep last 1000 entries to prevent unbounded growth
        if len(logs) > 1000:
            logs = logs[-1000:]

        self._log_file.write_text(
            json.dumps(logs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent log entries."""
        try:
            content = self._log_file.read_text(encoding="utf-8").strip()
            logs: List[Dict[str, Any]] = json.loads(content) if content else []
            return logs[-limit:]
        except (json.JSONDecodeError, OSError):
            return []


# Module-level singleton
logging_service = LoggingService()