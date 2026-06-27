"""
Marks ERP Tool.
Loads marks/grades data from mock JSON and returns structured results.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


class MarksTool:
    """Retrieves and analyses academic marks for a given student."""

    TOOL_NAME = "marks"

    def __init__(self) -> None:
        self._data_path: Path = settings.mock_data_dir / "marks.json"
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if not self._data_path.exists():
            raise FileNotFoundError(f"Marks data not found at {self._data_path}")
        with open(self._data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute(
        self,
        student_id: str,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch marks data for a student.

        Args:
            student_id: The student's unique ID.
            subject: Optional specific subject name to filter.

        Returns:
            Dict with marks, grades, averages, and analysis.

        Raises:
            KeyError: If student_id is not found.
            ValueError: If specified subject is not found.
        """
        if student_id not in self._data:
            raise KeyError(f"No marks records found for student ID '{student_id}'.")

        record = self._data[student_id]
        subjects: Dict[str, Any] = record["subjects"]

        if subject:
            # Find case-insensitive match
            matched = next(
                (k for k in subjects if k.lower() == subject.lower()), None
            )
            if matched is None:
                available = ", ".join(subjects.keys())
                raise ValueError(
                    f"Subject '{subject}' not found. Available subjects: {available}"
                )
            return {
                "student_name": record["student_name"],
                "class": record["class"],
                "semester": record["semester"],
                "subject_detail": {
                    "subject": matched,
                    **subjects[matched],
                },
            }

        # Full analysis
        avg = round(sum(s["marks"] for s in subjects.values()) / len(subjects), 1)
        strongest = max(subjects.items(), key=lambda x: x[1]["marks"])
        weakest = min(subjects.items(), key=lambda x: x[1]["marks"])
        strong_subjects = [k for k, v in subjects.items() if v["marks"] >= 85]
        weak_subjects = [k for k, v in subjects.items() if v["marks"] < 70]

        subjects_list = [
            {"subject": name, **data}
            for name, data in subjects.items()
        ]
        subjects_list.sort(key=lambda x: x["marks"], reverse=True)

        return {
            "student_name": record["student_name"],
            "class": record["class"],
            "semester": record["semester"],
            "subjects": subjects_list,
            "average_score": avg,
            "highest_marks": {
                "subject": strongest[0],
                "marks": strongest[1]["marks"],
                "grade": strongest[1]["grade"],
            },
            "lowest_marks": {
                "subject": weakest[0],
                "marks": weakest[1]["marks"],
                "grade": weakest[1]["grade"],
            },
            "strong_subjects": strong_subjects,
            "weak_subjects": weak_subjects,
            "total_subjects": len(subjects),
            "exam_dates": record.get("exam_dates", {}),
        }