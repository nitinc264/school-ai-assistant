"""
Attendance ERP Tool.
Loads attendance data from mock JSON and returns structured results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings


class AttendanceTool:
    """Retrieves and computes attendance data for a given student."""

    TOOL_NAME = "attendance"

    def __init__(self) -> None:
        self._data_path: Path = settings.mock_data_dir / "attendance.json"
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Load attendance mock data from disk."""
        if not self._data_path.exists():
            raise FileNotFoundError(f"Attendance data not found at {self._data_path}")
        with open(self._data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute(
        self,
        student_id: str,
        month: Optional[str] = None,
        target_percentage: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Fetch attendance data for a student.

        Args:
            student_id: The student's unique ID.
            month: Optional month filter in YYYY-MM format.
            target_percentage: If provided, calculate whether the student can reach this %.

        Returns:
            Dict containing attendance data and computed metrics.

        Raises:
            KeyError: If student_id is not found in mock data.
        """
        if student_id not in self._data:
            raise KeyError(f"No attendance records found for student ID '{student_id}'.")

        record = self._data[student_id]
        total = record["total_classes"]
        attended = record["attended"]
        percentage = round((attended / total * 100), 1) if total > 0 else 0.0
        missed = total - attended

        result: Dict[str, Any] = {
            "student_name": record["student_name"],
            "class": record["class"],
            "academic_year": record["academic_year"],
            "total_classes": total,
            "attended": attended,
            "missed": missed,
            "percentage": percentage,
            "status": self._classify_attendance(percentage),
            "remaining_classes_in_semester": record.get("remaining_classes_in_semester", 0),
        }

        # Monthly breakdown
        monthly_data = record.get("monthly", {})
        if month:
            if month not in monthly_data:
                result["monthly_detail"] = None
                result["monthly_note"] = f"No data found for month {month}."
            else:
                m = monthly_data[month]
                m_pct = round((m["attended"] / m["total"] * 100), 1) if m["total"] > 0 else 0.0
                result["monthly_detail"] = {
                    "month": month,
                    "total": m["total"],
                    "attended": m["attended"],
                    "missed": m["total"] - m["attended"],
                    "percentage": m_pct,
                    "absences": m.get("absences", []),
                }
        else:
            result["monthly_summary"] = []
            for m_key, m_val in monthly_data.items():
                m_pct = round((m_val["attended"] / m_val["total"] * 100), 1) if m_val["total"] > 0 else 0.0
                result["monthly_summary"].append({
                    "month": m_key,
                    "total": m_val["total"],
                    "attended": m_val["attended"],
                    "missed": m_val["total"] - m_val["attended"],
                    "percentage": m_pct,
                    "absences": m_val.get("absences", []),
                })

        # Target percentage feasibility
        if target_percentage is not None:
            result["target_analysis"] = self._can_maintain_target(
                attended, total, target_percentage,
                record.get("remaining_classes_in_semester", 0),
            )

        return result

    def _classify_attendance(self, percentage: float) -> str:
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 75:
            return "Good"
        elif percentage >= 60:
            return "Warning"
        else:
            return "Critical"

    def _can_maintain_target(
        self,
        current_attended: int,
        current_total: int,
        target_pct: float,
        remaining_classes: int,
    ) -> Dict[str, Any]:
        """
        Calculate whether a student can achieve a target attendance percentage.
        Assumes the student attends ALL remaining classes.
        """
        projected_total = current_total + remaining_classes
        projected_attended = current_attended + remaining_classes
        projected_pct = round((projected_attended / projected_total * 100), 1) if projected_total > 0 else 0.0

        # Minimum classes to attend out of remaining to hit target
        # target = (current_attended + x) / (current_total + remaining_classes) * 100
        # x = target * (current_total + remaining_classes) / 100 - current_attended
        required_attended = (target_pct / 100) * projected_total - current_attended
        required_attended = max(0, round(required_attended))

        achievable = required_attended <= remaining_classes

        return {
            "target_percentage": target_pct,
            "current_percentage": round((current_attended / current_total * 100), 1) if current_total > 0 else 0.0,
            "remaining_classes": remaining_classes,
            "classes_must_attend": int(required_attended),
            "can_skip_and_still_achieve": max(0, remaining_classes - int(required_attended)),
            "achievable": achievable,
            "projected_if_all_attended": projected_pct,
        }