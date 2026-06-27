"""
Tool Executor – orchestrates execution of one or more ERP tools.
Handles parameter mapping, error isolation per tool, and result aggregation.
"""

from typing import Any, Dict, List

from app.models.schemas import ExecutionPlan, ToolResult
from app.tools.tool_registry import ToolRegistry


class ToolExecutor:
    """
    Executes ERP tools based on the agent's execution plan.
    Each tool is called independently so failures in one don't block others.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute_plan(
        self,
        plan: ExecutionPlan,
        student_id: str,
        user_message: str,
    ) -> List[ToolResult]:
        """
        Execute all tools specified in the execution plan.

        Args:
            plan: The AI-generated execution plan with tool names.
            student_id: Student identifier passed to every tool.
            user_message: Original user message (used to extract optional params).

        Returns:
            List of ToolResult objects, one per tool in the plan.
        """
        results: List[ToolResult] = []

        for tool_name in plan.tools:
            kwargs = self._extract_kwargs(tool_name, user_message)
            raw_result = self._registry.execute(
                tool_name=tool_name,
                student_id=student_id,
                **kwargs,
            )
            results.append(
                ToolResult(
                    tool_name=tool_name,
                    success=raw_result["success"],
                    data=raw_result.get("data"),
                    error=raw_result.get("error"),
                )
            )

        return results

    def _extract_kwargs(self, tool_name: str, user_message: str) -> Dict[str, Any]:
        """
        Extract optional keyword arguments from the user message for specific tools.
        This uses simple heuristics – the AI planner handles semantic understanding.

        Args:
            tool_name: The tool being called.
            user_message: The original user message.

        Returns:
            Dict of additional kwargs to pass to the tool's execute() method.
        """
        msg_lower = user_message.lower()
        kwargs: Dict[str, Any] = {}

        if tool_name == "attendance":
            # Detect target percentage queries
            import re
            pct_match = re.search(r"(\d{2,3})\s*%?\s*(?:attendance|percent)", msg_lower)
            if pct_match:
                kwargs["target_percentage"] = float(pct_match.group(1))

            # Detect month references (basic: "this month" → current month)
            from datetime import date
            if "this month" in msg_lower:
                kwargs["month"] = date.today().strftime("%Y-%m")
            elif "last month" in msg_lower:
                from datetime import timedelta
                last = date.today().replace(day=1) - timedelta(days=1)
                kwargs["month"] = last.strftime("%Y-%m")
            elif "june" in msg_lower:
                kwargs["month"] = "2025-06"
            elif "july" in msg_lower:
                kwargs["month"] = "2025-07"
            elif "may" in msg_lower:
                kwargs["month"] = "2025-05"

        elif tool_name == "marks":
            # Detect subject name mentions
            subjects = [
                "mathematics", "science", "english", "history",
                "computer science", "hindi", "geography",
            ]
            for subj in subjects:
                if subj in msg_lower:
                    kwargs["subject"] = subj.title()
                    break

        elif tool_name == "fees":
            if "pending" in msg_lower or "unpaid" in msg_lower:
                kwargs["filter_status"] = "Pending"
            elif "paid" in msg_lower and "history" in msg_lower:
                kwargs["filter_status"] = "Paid"

        elif tool_name == "homework":
            from datetime import date
            if "pending" in msg_lower:
                kwargs["status_filter"] = "Pending"
            elif "completed" in msg_lower or "done" in msg_lower:
                kwargs["status_filter"] = "Completed"
            elif "overdue" in msg_lower:
                kwargs["status_filter"] = "Overdue"
            if "today" in msg_lower:
                kwargs["due_date"] = date.today().isoformat()
            elif "tomorrow" in msg_lower:
                from datetime import timedelta
                kwargs["due_date"] = (date.today() + timedelta(days=1)).isoformat()

        elif tool_name == "timetable":
            if "today" in msg_lower:
                kwargs["day"] = "today"
            elif "tomorrow" in msg_lower:
                kwargs["day"] = "tomorrow"
            else:
                days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
                for d in days:
                    if d in msg_lower:
                        kwargs["day"] = d.capitalize()
                        break

            subjects = [
                "mathematics", "science", "english", "history",
                "computer science", "hindi", "geography",
            ]
            for subj in subjects:
                if subj in msg_lower and "when" in msg_lower:
                    kwargs["subject"] = subj.title()
                    break

        return kwargs