"""Developer subagent specializing in code generation and refactoring."""

from __future__ import annotations

import re
from typing import Dict, List, Optional
from src.agents.base import BaseAgent
from src.llm.client import BaseLLMClient
from src.schema import AgentExecutionResult, ReviewReport, SubAgentRole
from src.skills.registry import SkillRegistry

DEVELOPER_SYSTEM_PROMPT = """Role: Developer (Senior Software Engineer)
You are an expert Python software engineer specializing in clean, robust, and maintainable systems.
Your responsibility is to design and implement modular, type-safe, and self-documenting code.
Follow all injected skills and guidelines strictly. Output clean, complete Python code with docstrings."""


class DeveloperAgent(BaseAgent):
    """Subagent responsible for implementing and revising code solutions."""

    def __init__(self, llm_client: BaseLLMClient, skills_registry: SkillRegistry):
        super().__init__(
            name="DeveloperAgent",
            role=SubAgentRole.DEVELOPER,
            base_system_prompt=DEVELOPER_SYSTEM_PROMPT,
            llm_client=llm_client,
            skills_registry=skills_registry,
        )

    def generate_solution(
        self,
        step_id: int,
        task_description: str,
        skill_names: Optional[List[str]] = None,
    ) -> AgentExecutionResult:
        """Generate initial code implementation for the task."""
        prompt = (
            f"Please implement a complete, production-ready solution for the following requirement:\n\n"
            f"REQUIREMENT:\n{task_description}\n\n"
            f"Provide clean, self-contained Python code. Ensure full type annotations and custom exceptions."
        )
        result = self.execute(step_id=step_id, task_prompt=prompt, skill_names=skill_names)
        result.code_artifacts["solution.py"] = self._extract_code(result.raw_output)
        return result

    def apply_revision(
        self,
        step_id: int,
        original_code: str,
        review_report: ReviewReport,
        skill_names: Optional[List[str]] = None,
    ) -> AgentExecutionResult:
        """Refactor code to fix issues identified by ReviewerAgent."""
        issues_text = "\n".join(
            f"- [{issue.severity.upper()}] {issue.rule_violated}: {issue.description}\n  Suggested Fix: {issue.suggestion}"
            for issue in review_report.issues
        )
        prompt = (
            f"REVISION REQUEST:\n"
            f"The code review rejected your previous implementation with the following issues:\n"
            f"{issues_text}\n\n"
            f"Please refactor the code to eliminate all reported vulnerabilities and warnings while maintaining all functionality.\n"
            f"Output the complete updated Python code."
        )
        context = {"previous_implementation": original_code}
        result = self.execute(step_id=step_id, task_prompt=prompt, skill_names=skill_names, context=context)
        result.code_artifacts["solution.py"] = self._extract_code(result.raw_output)
        return result

    def _extract_code(self, raw_output: str) -> str:
        """Extract code from markdown code blocks or return raw string."""
        match = re.search(r"```(?:python)?\s*(.*?)\s*```", raw_output, re.DOTALL)
        if match:
            return match.group(1).strip()
        return raw_output.strip()
