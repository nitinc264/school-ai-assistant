"""
Centralized configuration management using Pydantic Settings.
All environment variables and application settings are defined here.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini model name")

    # Application
    app_name: str = Field(default="School AI ERP Assistant", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    db_path: str = Field(default="./data/conversations.db", description="SQLite database path")

    # Student defaults
    default_student_id: str = Field(default="STU001", description="Default student ID")

    # Mock data
    mock_data_dir: Path = Field(default=BASE_DIR / "mock_data", description="Mock data directory")

    # Logs
    logs_dir: Path = Field(default=BASE_DIR / "logs", description="Logs directory")
    agent_log_file: str = Field(default="agent_logs.json", description="Agent log filename")

    # Agent
    max_history_messages: int = Field(default=20, description="Max conversation history messages to pass to Gemini")
    gemini_temperature: float = Field(default=0.2, description="Gemini temperature for planning")
    gemini_response_temperature: float = Field(default=0.7, description="Gemini temperature for response generation")


settings = Settings()