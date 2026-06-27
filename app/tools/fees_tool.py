"""
Fees ERP Tool.
Loads fee payment data from mock JSON and returns structured results.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


class FeesTool:
    """Retrieves fee payment status and history for a given student."""

    TOOL_NAME = "fees"

    def __init__(self) -> None:
        self._data_path: Path = settings.mock_data_dir / "fees.json"
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if not self._data_path.exists():
            raise FileNotFoundError(f"Fees data not found at {self._data_path}")
        with open(self._data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute(
        self,
        student_id: str,
        filter_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch fee data for a student.

        Args:
            student_id: The student's unique ID.
            filter_status: Optional filter – 'Paid', 'Pending', or 'Overdue'.

        Returns:
            Dict with fee summary and payment history.

        Raises:
            KeyError: If student_id is not found.
        """
        if student_id not in self._data:
            raise KeyError(f"No fee records found for student ID '{student_id}'.")

        record = self._data[student_id]
        history: List[Dict[str, Any]] = record["payment_history"]

        if filter_status:
            history = [
                p for p in history
                if p["status"].lower() == filter_status.lower()
            ]

        pending_items = [p for p in record["payment_history"] if p["status"] in ("Pending", "Overdue")]
        overdue_items = [p for p in record["payment_history"] if p["status"] == "Overdue"]

        return {
            "student_name": record["student_name"],
            "class": record["class"],
            "academic_year": record["academic_year"],
            "total_fees": record["total_fees"],
            "paid": record["paid"],
            "pending": record["pending"],
            "fee_status": "Fully Paid" if record["pending"] == 0 else "Pending",
            "due_date": record.get("due_date"),
            "overdue_amount": sum(p["amount"] for p in overdue_items),
            "pending_items": pending_items,
            "overdue_items": overdue_items,
            "payment_history": history,
            "payment_completion_pct": round((record["paid"] / record["total_fees"] * 100), 1) if record["total_fees"] > 0 else 0.0,
        }