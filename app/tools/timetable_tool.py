"""
Timetable ERP Tool.
Loads schedule data from mock JSON and returns structured results.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


class TimetableTool:
    """Retrieves class timetable data for a given student."""

    TOOL_NAME = "timetable"

    DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def __init__(self) -> None:
        self._data_path: Path = settings.mock_data_dir / "timetable.json"
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if not self._data_path.exists():
            raise FileNotFoundError(f"Timetable data not found at {self._data_path}")
        with open(self._data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute(
        self,
        student_id: str,
        day: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch timetable data for a student.

        Args:
            student_id: The student's unique ID.
            day: Optional day name ('Monday', 'today', 'tomorrow', etc.).
            subject: Optional subject name to find when that class occurs.

        Returns:
            Dict with the relevant schedule data.

        Raises:
            KeyError: If student_id not found.
        """
        if student_id not in self._data:
            raise KeyError(f"No timetable records found for student ID '{student_id}'.")

        record = self._data[student_id]
        schedule: Dict[str, Any] = record.get("schedule", {})

        today_date = date.today()
        today_name = self.DAY_NAMES[today_date.weekday()]  # weekday() returns 0=Monday

        resolved_day: Optional[str] = None
        if day:
            day_lower = day.strip().lower()
            if day_lower == "today":
                resolved_day = today_name
            elif day_lower == "tomorrow":
                tomorrow = today_date + timedelta(days=1)
                resolved_day = self.DAY_NAMES[tomorrow.weekday()]
            else:
                # Match day name case-insensitively
                matched = next(
                    (d for d in self.DAY_NAMES if d.lower() == day_lower), None
                )
                resolved_day = matched

        # If searching for a specific subject
        if subject:
            occurrences = []
            for day_name, periods in schedule.items():
                for period in periods:
                    if period["subject"].lower() == subject.lower():
                        occurrences.append({
                            "day": day_name,
                            "period": period["period"],
                            "time": period["time"],
                            "teacher": period["teacher"],
                            "room": period["room"],
                        })
            return {
                "student_name": record["student_name"],
                "class": record["class"],
                "subject_search": subject,
                "occurrences": occurrences,
                "today": today_name,
                "requested_day": resolved_day,
            }

        if resolved_day:
            day_schedule = schedule.get(resolved_day, [])
            first_class = day_schedule[0] if day_schedule else None
            last_class = day_schedule[-1] if day_schedule else None
            return {
                "student_name": record["student_name"],
                "class": record["class"],
                "day": resolved_day,
                "is_today": resolved_day == today_name,
                "classes": day_schedule,
                "total_periods": len(day_schedule),
                "first_class": first_class,
                "last_class": last_class,
                "today": today_name,
            }

        # Return full weekly schedule
        week_summary = []
        for day_name in self.DAY_NAMES:
            if day_name in schedule:
                week_summary.append({
                    "day": day_name,
                    "is_today": day_name == today_name,
                    "total_periods": len(schedule[day_name]),
                    "classes": schedule[day_name],
                })

        today_schedule = schedule.get(today_name, [])
        return {
            "student_name": record["student_name"],
            "class": record["class"],
            "today": today_name,
            "today_schedule": today_schedule,
            "today_first_class": today_schedule[0] if today_schedule else None,
            "weekly_schedule": week_summary,
        }