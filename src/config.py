"""Configuration management for LLM Harness."""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM backend providers."""
    MOCK = "mock"
    LOCAL = "local"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Provider configuration: 'mock', 'local', or 'openai'
    provider: LLMProvider = Field(default=LLMProvider.MOCK, alias="LLM_PROVIDER")

    # Local LLM settings (Ollama, LM Studio, vLLM)
    local_base_url: str = Field(default="http://localhost:11434/v1", alias="LOCAL_LLM_BASE_URL")
    local_model: str = Field(default="gemma4:12b", alias="LOCAL_LLM_MODEL")
    local_api_key: str = Field(default="ollama", alias="LOCAL_LLM_API_KEY")

    # Cloud OpenAI / Compatible settings
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    skills_dir: Path = Path(__file__).resolve().parent.parent / "skills"

    # Runtime
    max_feedback_iterations: int = 2
    temperature: float = 0.2
    request_timeout: float = 60.0


settings = Settings()
