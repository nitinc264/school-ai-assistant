"""
Centralized prompt templates for the AI agent planner and response generator.
All Gemini prompts are defined here to keep agent logic clean and maintainable.
"""

from datetime import date


def get_planner_system_prompt() -> str:
    """
    Returns the system prompt for the Gemini planner.
    The planner's sole job is to analyze intent and produce a structured execution plan.
    """
    today = date.today().strftime("%A, %B %d, %Y")
    return f"""You are the planning module of a School ERP AI Assistant.
Today's date is {today}.

Your ONLY job is to analyze the user's message and conversation history, then return a structured JSON execution plan.

Available ERP tools:
- attendance: Fetch attendance records, percentage, absences, monthly breakdown, or calculate if a target % is achievable.
- marks: Fetch subject-wise marks, grades, averages, strongest/weakest subjects.
- fees: Fetch fee payment status, pending amounts, payment history.
- homework: Fetch pending/completed assignments, due dates, overdue work.
- timetable: Fetch today's/tomorrow's class schedule, subject timings.

Rules:
1. NEVER use keyword matching. Always reason semantically.
2. For multi-part queries (e.g. "show attendance and fees"), include ALL relevant tools.
3. Use conversation history to resolve references like "those marks" or "that subject".
4. For "performance summary", "how am I doing", "academic overview" → use tools: ["marks", "attendance"] and set is_performance_summary to true.
5. For multi-tool queries, set is_multi_step to true.

You MUST respond with ONLY valid JSON. No explanation, no markdown, no code fences.

Response format:
{{
  "intent": "<short intent label, e.g. Attendance, Marks, Fees, Homework, Timetable, Performance Summary, Multi-Step>",
  "tools": ["<tool1>", "<tool2>"],
  "reasoning": "<1-2 sentence explanation of your plan>",
  "is_multi_step": <true|false>,
  "is_performance_summary": <true|false>
}}"""


def get_response_system_prompt() -> str:
    """
    Returns the system prompt for the Gemini response generator.
    The response generator transforms raw tool data into a friendly reply.
    """
    today = date.today().strftime("%A, %B %d, %Y")
    return f"""You are a friendly and knowledgeable School ERP Assistant.
Today's date is {today}.

You have already fetched data from the school ERP system. Your job is to:
1. Read the tool results provided.
2. Answer the user's question clearly and concisely using that data.
3. Be warm, encouraging, and student-focused.
4. Format numbers neatly (e.g. percentages to 1 decimal, currency with ₹ symbol).
5. If attendance is below 75%, add a gentle warning.
6. If fees are overdue, clearly highlight the urgency.
7. For performance summaries, structure the response with clear sections.
8. Do NOT invent or hallucinate data beyond what is provided in the tool results.

Keep responses concise but complete. Use bullet points or numbered lists only when listing multiple items."""


def get_status_from_intent(intent: str, tool_results: list) -> str:
    """
    Derives a simple status label based on intent and tool results.
    tool_results is a list of dicts: {tool_name, success, data, error}.
    """
    intent_lower = intent.lower()
    if not tool_results:
        return "Unknown"

    # Check for any failed tool
    if any(not r.get("success") for r in tool_results):
        return "Error"

    for result in tool_results:
        tool_name = result.get("tool_name", "")
        data = result.get("data") or {}

        if tool_name == "attendance":
            attended = data.get("attended", 0)
            total = data.get("total_classes", 1)
            pct = (attended / total * 100) if total > 0 else 0
            if pct >= 90:
                return "Excellent"
            elif pct >= 75:
                return "Good"
            else:
                return "Warning"

        if tool_name == "marks":
            # subjects is a list of dicts with 'marks' key
            subjects = data.get("subjects", [])
            if subjects:
                avg = sum(s["marks"] for s in subjects) / len(subjects)
                if avg >= 85:
                    return "Excellent"
                elif avg >= 70:
                    return "Good"
                else:
                    return "Needs Improvement"

        if tool_name == "fees":
            pending = data.get("pending", 0)
            return "Paid" if pending == 0 else "Pending"

        if tool_name == "homework":
            summary = data.get("summary", {})
            if summary.get("overdue", 0) > 0:
                return "Overdue"
            elif summary.get("pending", 0) > 0:
                return "Pending"
            else:
                return "All Done"

        if tool_name == "timetable":
            return "Scheduled"

    if "performance" in intent_lower or "summary" in intent_lower:
        return "Analyzed"

    if "multi" in intent_lower:
        return "Completed"

    return "Completed"