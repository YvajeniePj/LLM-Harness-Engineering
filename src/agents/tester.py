"""Tester subagent specializing in automated test generation with pytest."""

from __future__ import annotations

import re
from typing import Dict, List, Optional
from src.agents.base import BaseAgent
from src.llm.client import BaseLLMClient
from src.schema import AgentExecutionResult, SubAgentRole
from src.skills.registry import SkillRegistry

TESTER_SYSTEM_PROMPT = """Role: Tester (QA Automation & TDD Specialist)
You are an expert QA Engineer and Test Automation Specialist.
Your responsibility is to design robust, deterministic, and comprehensive pytest suites.
Adhere strictly to the injected testing standards (Arrange-Act-Assert, boundary cases,
security edge cases, fixtures, and failure modes).
Output complete, runnable pytest test code with assertions."""


class TestAgent(BaseAgent):
    """Subagent responsible for generating comprehensive automated tests."""

    def __init__(self, llm_client: BaseLLMClient, skills_registry: SkillRegistry):
        super().__init__(
            name="TestAgent",
            role=SubAgentRole.TESTER,
            base_system_prompt=TESTER_SYSTEM_PROMPT,
            llm_client=llm_client,
            skills_registry=skills_registry,
        )

    def generate_tests(
        self,
        step_id: int,
        task_description: str,
        solution_code: str,
        skill_names: Optional[List[str]] = None,
    ) -> AgentExecutionResult:
        """Generate pytest test cases covering happy path, edge cases, and security."""
        prompt = (
            f"Generate a complete, self-contained pytest test suite for the following implementation:\n\n"
            f"REQUIREMENT:\n{task_description}\n\n"
            f"IMPLEMENTATION TO TEST:\n```python\n{solution_code}\n```\n\n"
            f"Follow the AAA (Arrange-Act-Assert) pattern. Include edge cases (empty inputs, "
            f"boundary lengths, expiration, invalid tokens) and verify error exceptions."
        )
        active_skills = skill_names or ["pytest_testing"]
        result = self.execute(step_id=step_id, task_prompt=prompt, skill_names=active_skills)
        result.code_artifacts["test_solution.py"] = self._extract_code(result.raw_output)
        return result

    def _extract_code(self, raw_output: str) -> str:
        """Extract code from markdown code blocks or return raw string."""
        match = re.search(r"```(?:python)?\s*(.*?)\s*```", raw_output, re.DOTALL)
        if match:
            return match.group(1).strip()
        return raw_output.strip()
