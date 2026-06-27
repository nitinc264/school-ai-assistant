"""
Agent Planner – the central AI agent that orchestrates the full pipeline:
  User Message → Gemini Planning → Tool Execution → Gemini Response → Memory Save
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.agents.executor import ToolExecutor
from app.config import settings
from app.memory.conversation_memory import ConversationMemory
from app.models.schemas import (
    ChatResponse,
    ExecutionPlan,
    ToolResult,
)
from app.services.gemini_service import GeminiService
from app.services.logging_service import logging_service
from app.tools.tool_registry import ToolRegistry
from app.utils.prompts import (
    get_planner_system_prompt,
    get_response_system_prompt,
    get_status_from_intent,
)


class AgentPlanner:
    """
    Orchestrates the complete agent workflow:
    1. Load conversation history from SQLite memory.
    2. Call Gemini to generate a structured execution plan (intent + tools).
    3. Execute each planned ERP tool via ToolExecutor.
    4. Call Gemini again to generate a natural language response from tool results.
    5. Save interaction to memory and logs.
    6. Return structured ChatResponse.
    """

    def __init__(
        self,
        gemini_service: GeminiService,
        memory: ConversationMemory,
        registry: ToolRegistry,
    ) -> None:
        self._gemini = gemini_service
        self._memory = memory
        self._executor = ToolExecutor(registry)

    def process(
        self,
        message: str,
        student_id: str,
        session_id: str,
    ) -> ChatResponse:
        """
        Process a user message end-to-end and return a ChatResponse.

        Args:
            message: The user's natural language query.
            student_id: The student's ERP ID.
            session_id: Conversation session identifier.

        Returns:
            ChatResponse with intent, tool results, and AI-generated reply.

        Raises:
            RuntimeError: If Gemini planning or response generation fails.
        """
        start_time = time.monotonic()

        # 1. Load conversation history
        history = self._memory.get_formatted_for_gemini(
            session_id,
            limit=settings.max_history_messages,
        )

        # 2. Generate execution plan via Gemini
        plan_dict = self._gemini.plan(
            user_message=message,
            conversation_history=history,
            system_prompt=get_planner_system_prompt(),
        )

        plan = self._parse_plan(plan_dict)

        # 3. Execute tools
        tool_results: List[ToolResult] = self._executor.execute_plan(
            plan=plan,
            student_id=student_id,
            user_message=message,
        )

        # 3a. If ALL tools failed with a "not found" error, raise KeyError so the
        #     API layer can return a proper 404 response.
        if tool_results and all(not r.success for r in tool_results):
            first_error = tool_results[0].error or "Student record not found."
            if "not found" in first_error.lower() or "no " in first_error.lower():
                raise KeyError(first_error)

        # 4. Handle performance summary (bonus feature)
        if plan.is_performance_summary:
            response_text = self._generate_performance_summary(
                tool_results=tool_results,
                student_id=student_id,
                session_id=session_id,
                message=message,
                history=history,
            )
        else:
            # Standard response generation
            tool_results_serialized = self._serialize_results(tool_results)
            response_text = self._gemini.generate_response(
                user_message=message,
                tool_results=tool_results_serialized,
                conversation_history=history,
                system_prompt=get_response_system_prompt(),
                intent=plan.intent,
            )

        # 5. Determine status
        tool_results_dicts = self._serialize_results(tool_results)
        status = get_status_from_intent(plan.intent, tool_results_dicts)

        # 6. Primary tool label
        primary_tool = self._get_primary_tool_label(plan)

        # 7. Save to memory
        self._memory.add_message(session_id, "user", message)
        self._memory.add_message(session_id, "assistant", response_text, intent=plan.intent)

        # 8. Calculate execution time
        elapsed_ms = (time.monotonic() - start_time) * 1000

        # 9. Log the interaction
        logging_service.log_interaction(
            session_id=session_id,
            user_query=message,
            intent=plan.intent,
            execution_plan=plan.model_dump(),
            tools_called=plan.tools,
            execution_time_ms=elapsed_ms,
            response_summary=response_text[:200],
            status="success",
        )

        return ChatResponse(
            intent=plan.intent,
            tool=primary_tool,
            response=response_text,
            status=status,
            execution_plan=plan,
            tool_results=tool_results,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
        )

    def _parse_plan(self, plan_dict: Dict[str, Any]) -> ExecutionPlan:
        """
        Parse and validate the JSON dict returned by Gemini into an ExecutionPlan.
        Provides safe defaults if fields are missing.
        """
        tools = plan_dict.get("tools", [])
        if isinstance(tools, str):
            tools = [tools]

        # Normalize tool names to lowercase
        tools = [t.lower().strip() for t in tools if t]

        # Fallback if Gemini returned no tools
        if not tools:
            tools = ["attendance"]

        return ExecutionPlan(
            intent=plan_dict.get("intent", "General Query"),
            tools=tools,
            reasoning=plan_dict.get("reasoning", "No reasoning provided."),
            is_multi_step=len(tools) > 1 or plan_dict.get("is_multi_step", False),
            is_performance_summary=plan_dict.get("is_performance_summary", False),
        )

    def _serialize_results(self, tool_results: List[ToolResult]) -> List[Dict[str, Any]]:
        """Convert ToolResult objects to plain dicts for JSON serialization."""
        return [
            {
                "tool_name": r.tool_name,
                "success": r.success,
                "data": r.data,
                "error": r.error,
            }
            for r in tool_results
        ]

    def _get_primary_tool_label(self, plan: ExecutionPlan) -> str:
        """Return a display-friendly label for the primary tool used."""
        tool_labels = {
            "attendance": "Attendance Tool",
            "marks": "Marks Tool",
            "fees": "Fees Tool",
            "homework": "Homework Tool",
            "timetable": "Timetable Tool",
        }
        if plan.is_multi_step and len(plan.tools) > 1:
            labels = [tool_labels.get(t, t.title()) for t in plan.tools]
            return ", ".join(labels)
        primary = plan.tools[0] if plan.tools else "unknown"
        return tool_labels.get(primary, primary.title() + " Tool")

    def _generate_performance_summary(
        self,
        tool_results: List[ToolResult],
        student_id: str,
        session_id: str,
        message: str,
        history: List[Dict[str, Any]],
    ) -> str:
        """
        Generate an enhanced academic performance summary (Bonus Feature #2).
        Augments the tool results with a structured summary prompt.
        """
        tool_results_dicts = self._serialize_results(tool_results)
        summary_prompt = (
            "Generate a comprehensive Academic Performance Summary with these sections:\n"
            "1. **Overall Performance** – summarize the student's general standing.\n"
            "2. **Strong Subjects** – list subjects where marks ≥ 85.\n"
            "3. **Weak Subjects** – list subjects where marks < 70 with specific advice.\n"
            "4. **Attendance Summary** – current percentage and whether it's at risk.\n"
            "5. **AI Suggestions** – 3-4 personalized, actionable improvement tips.\n\n"
            "Be encouraging and constructive. Use the ERP data provided."
        )
        augmented_message = f"{message}\n\n{summary_prompt}"
        return self._gemini.generate_response(
            user_message=augmented_message,
            tool_results=tool_results_dicts,
            conversation_history=history,
            system_prompt=get_response_system_prompt(),
            intent="Academic Performance Summary",
        )