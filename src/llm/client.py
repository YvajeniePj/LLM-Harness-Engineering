"""LLM client interfaces supporting Mock, Local LLM (Ollama/LM Studio), and Cloud API."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from src.config import LLMProvider, settings
from src.llm.mock_responses import MOCK_CASE_1_TOKEN_MANAGER

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Generate text completion from system and user prompts."""
        pass

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        """Generate structured Pydantic object from prompts."""
        pass


class OpenAILLMClient(BaseLLMClient):
    """OpenAI API client compatible with Cloud OpenAI, Ollama, LM Studio, vLLM, and Groq."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        from openai import OpenAI

        self.api_key = api_key or "dummy-key-for-local"
        self.base_url = base_url
        self.model = model or "gpt-4o-mini"
        self.timeout = timeout

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            err_msg = str(exc)
            if "Connection error" in err_msg or "Failed to connect" in err_msg:
                target = self.base_url or "api.openai.com"
                raise ConnectionError(
                    f"Could not connect to LLM endpoint at [{target}]. "
                    f"Check that your local LLM (Ollama/LM Studio) is running, "
                    f"or switch to mock mode with '--provider mock'. Details: {exc}"
                ) from exc
            raise

    def generate_json(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        system_with_schema = (
            f"{system_prompt}\n\n"
            f"CRITICAL REQUIREMENT: You MUST respond strictly with a valid JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include any preamble or text outside of the JSON block."
        )

        raw = self.generate(system_with_schema, user_prompt, temperature=0.1)

        # Clean potential markdown wrapping ```json ... ```
        cleaned = raw.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)
        elif cleaned.startswith("{") and cleaned.endswith("}"):
            pass
        else:
            # Fallback search for first { and last }
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start : end + 1]

        data = json.loads(cleaned)
        return response_model.model_validate(data)


class MockLLMClient(BaseLLMClient):
    """Deterministic Mock LLM client simulating multi-agent interactions."""

    def __init__(self):
        self._dev_iteration = 0
        self._reviewer_iteration = 0

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        # Detect agent role from prompt contents
        if "Role: Developer" in system_prompt or "DEVELOPER" in system_prompt:
            if "REVISION REQUEST" in user_prompt or "issues" in user_prompt.lower():
                return MOCK_CASE_1_TOKEN_MANAGER["developer_fixed_code"]
            return MOCK_CASE_1_TOKEN_MANAGER["developer_initial_code"]

        if "Role: Tester" in system_prompt or "TESTER" in system_prompt:
            return MOCK_CASE_1_TOKEN_MANAGER["tester_code"]

        if "Role: Reviewer" in system_prompt or "REVIEWER" in system_prompt:
            if "Fixed" in user_prompt or "Hardened" in user_prompt:
                return MOCK_CASE_1_TOKEN_MANAGER["reviewer_approval"]
            return MOCK_CASE_1_TOKEN_MANAGER["reviewer_rejection"]

        if "DISPATCHER" in system_prompt or "Dispatcher" in system_prompt:
            return MOCK_CASE_1_TOKEN_MANAGER["dispatcher_plan"]

        return "Mock response generated for: " + user_prompt[:100]

    def generate_json(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        raw_text = self.generate(system_prompt, user_prompt)
        # Extract json if in markdown
        cleaned = raw_text.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)
        data = json.loads(cleaned)
        return response_model.model_validate(data)


def create_llm_client(
    provider: Optional[LLMProvider] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMClient:
    """Factory creating appropriate LLM client based on configuration."""
    active_provider = provider or settings.provider

    if active_provider == LLMProvider.MOCK:
        return MockLLMClient()

    if active_provider == LLMProvider.LOCAL:
        return OpenAILLMClient(
            base_url=base_url or settings.local_base_url,
            api_key=api_key or settings.local_api_key,
            model=model or settings.local_model,
        )

    if active_provider == LLMProvider.OPENAI:
        return OpenAILLMClient(
            base_url=base_url or settings.openai_base_url,
            api_key=api_key or settings.openai_api_key,
            model=model or settings.openai_model,
        )

    raise ValueError(f"Unknown LLM provider: {active_provider}")
