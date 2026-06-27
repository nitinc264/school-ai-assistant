"""
Homework ERP Tool.
Loads homework/assignment data from mock JSON and returns structured results.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


class HomeworkTool:
    """Retrieves homework and assignment data for a given student."""

    TOOL_NAME = "homework"

    def __init__(self) -> None:
        self._data_path: Path = settings.mock_data_dir / "homework.json"
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if not self._data_path.exists():
            raise FileNotFoundError(f"Homework data not found at {self._data_path}")
        with open(self._data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute(
        self,
        student_id: str,
        status_filter: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch homework data for a student.

        Args:
            student_id: The student's unique ID.
            status_filter: Optional – 'Pending', 'Completed', or 'Overdue'.
            due_date: Optional – filter by due date (YYYY-MM-DD).

        Returns:
            Dict with all assignments and summary counts.

        Raises:
            KeyError: If student_id not found.
        """
        if student_id not in self._data:
            raise KeyError(f"No homework records found for student ID '{student_id}'.")

        record = self._data[student_id]
        assignments: List[Dict[str, Any]] = record["assignments"]

        today_str = date.today().isoformat()

        # Enrich assignments with overdue flag
        enriched: List[Dict[str, Any]] = []
        for a in assignments:
            item = dict(a)
            if item["status"] == "Pending" and item["due_date"] < today_str:
                item["status"] = "Overdue"
            days_remaining = None
            if item["status"] in ("Pending",):
                due = datetime.strptime(item["due_date"], "%Y-%m-%d").date()
                days_remaining = (due - date.today()).days
            item["days_remaining"] = days_remaining
            enriched.append(item)

        # Apply filters
        filtered = enriched
        if status_filter:
            filtered = [a for a in filtered if a["status"].lower() == status_filter.lower()]
        if due_date:
            filtered = [a for a in filtered if a["due_date"] == due_date]

        pending = [a for a in enriched if a["status"] == "Pending"]
        completed = [a for a in enriched if a["status"] == "Completed"]
        overdue = [a for a in enriched if a["status"] == "Overdue"]

        return {
            "student_name": record["student_name"],
            "assignments": filtered,
            "summary": {
                "total": len(enriched),
                "pending": len(pending),
                "completed": len(completed),
                "overdue": len(overdue),
            },
            "pending_assignments": pending,
            "overdue_assignments": overdue,
            "today": today_str,
        }