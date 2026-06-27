"""
Gemini Service – wrapper around the Google Generative AI SDK.
Provides a clean interface for planning and response generation calls.
"""

import json
import re
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from app.config import settings


class GeminiService:
    """
    Provides structured access to Google Gemini for:
    1. Planning (intent detection + tool selection) → JSON output
    2. Response generation (tool results → natural language)
    """

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please add it to your .env file."
            )
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model

    def _get_model(self, system_instruction: str, temperature: float) -> genai.GenerativeModel:
        """Instantiate a Gemini model with the given system instruction and temperature."""
        return genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_instruction,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048,
            ),
        )

    def plan(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        system_prompt: str,
    ) -> Dict[str, Any]:
        """
        Use Gemini to generate a structured execution plan.

        Args:
            user_message: The current user query.
            conversation_history: Prior messages formatted for Gemini chat.
            system_prompt: Planner system prompt.

        Returns:
            Parsed JSON dict with intent, tools, reasoning, flags.

        Raises:
            ValueError: If Gemini returns non-parseable JSON.
            RuntimeError: If the Gemini API call fails.
        """
        model = self._get_model(system_prompt, temperature=settings.gemini_temperature)

        try:
            if conversation_history:
                chat = model.start_chat(history=conversation_history)
                response = chat.send_message(user_message)
            else:
                response = model.generate_content(user_message)

            raw_text = response.text.strip()
            return self._parse_json_response(raw_text)

        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned non-JSON planning response: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Gemini planning call failed: {exc}") from exc

    def generate_response(
        self,
        user_message: str,
        tool_results: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        system_prompt: str,
        intent: str,
    ) -> str:
        """
        Use Gemini to generate a natural language response from tool results.

        Args:
            user_message: The original user query.
            tool_results: List of results returned by ERP tools.
            conversation_history: Prior conversation messages.
            system_prompt: Response generator system prompt.
            intent: Detected intent label for context.

        Returns:
            Natural language response string.

        Raises:
            RuntimeError: If the Gemini API call fails.
        """
        model = self._get_model(system_prompt, temperature=settings.gemini_response_temperature)

        # Build the prompt with tool results embedded
        results_text = json.dumps(tool_results, indent=2, ensure_ascii=False)
        augmented_message = (
            f"User question: {user_message}\n\n"
            f"Detected intent: {intent}\n\n"
            f"ERP Tool Results:\n{results_text}\n\n"
            "Please generate a helpful, friendly response based on the above data."
        )

        try:
            if conversation_history:
                chat = model.start_chat(history=conversation_history)
                response = chat.send_message(augmented_message)
            else:
                response = model.generate_content(augmented_message)

            return response.text.strip()

        except Exception as exc:
            raise RuntimeError(f"Gemini response generation failed: {exc}") from exc

    @staticmethod
    def _parse_json_response(text: str) -> Dict[str, Any]:
        """
        Parse a JSON string from Gemini, stripping any markdown code fences.

        Args:
            text: Raw text from Gemini.

        Returns:
            Parsed dict.

        Raises:
            ValueError: If parsing fails.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON from text that may have surrounding content
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse JSON from Gemini response: {text[:300]}")