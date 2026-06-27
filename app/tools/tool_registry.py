"""
Tool Registry – central mapping of ERP tool names to their implementations.
The agent executor uses this registry to dispatch tool calls.
"""

from typing import Any, Dict, Optional

from app.tools.attendance_tool import AttendanceTool
from app.tools.fees_tool import FeesTool
from app.tools.homework_tool import HomeworkTool
from app.tools.marks_tool import MarksTool
from app.tools.timetable_tool import TimetableTool


class ToolRegistry:
    """
    Singleton-style registry that holds all ERP tool instances.
    Provides a unified interface to execute any registered tool by name.
    """

    VALID_TOOLS = {"attendance", "marks", "fees", "homework", "timetable"}

    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {
            AttendanceTool.TOOL_NAME: AttendanceTool(),
            MarksTool.TOOL_NAME: MarksTool(),
            FeesTool.TOOL_NAME: FeesTool(),
            HomeworkTool.TOOL_NAME: HomeworkTool(),
            TimetableTool.TOOL_NAME: TimetableTool(),
        }

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Return the tool instance for a given tool name, or None if not found."""
        return self._tools.get(tool_name.lower())

    def execute(self, tool_name: str, student_id: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute a named ERP tool with the given parameters.

        Args:
            tool_name: Name of the tool (e.g. 'attendance', 'marks').
            student_id: Student identifier to pass to the tool.
            **kwargs: Additional parameters forwarded to the tool's execute() method.

        Returns:
            A result dict with 'success', 'tool_name', and either 'data' or 'error'.
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": f"Unknown tool '{tool_name}'. Valid tools: {', '.join(self.VALID_TOOLS)}",
            }

        try:
            data = tool.execute(student_id=student_id, **kwargs)
            return {
                "tool_name": tool_name,
                "success": True,
                "data": data,
            }
        except KeyError as exc:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": str(exc),
            }
        except ValueError as exc:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": str(exc),
            }
        except Exception as exc:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": f"Unexpected error in tool '{tool_name}': {str(exc)}",
            }

    @property
    def available_tools(self) -> list:
        """Return list of all registered tool names."""
        return list(self._tools.keys())


# Module-level singleton
tool_registry = ToolRegistry()