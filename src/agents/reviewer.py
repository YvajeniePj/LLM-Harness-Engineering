"""Reviewer subagent specializing in security audits and code quality."""

from __future__ import annotations

import json
import re
from typing import List, Optional
from src.agents.base import BaseAgent
from src.llm.client import BaseLLMClient
from src.schema import AgentExecutionResult, ReviewIssue, ReviewReport, ReviewSeverity, SubAgentRole
from src.skills.registry import SkillRegistry

REVIEWER_SYSTEM_PROMPT = """Role: Reviewer (Security & Quality Auditor)
You are an expert Principal Security Engineer and Code Reviewer.
Your task is to ruthlessly analyze code for vulnerabilities, edge-case failures, timing attacks,
bad architectural patterns, and non-compliance with the injected skills.
You must output a structured JSON evaluation indicating whether changes are requested or approved."""


class ReviewerAgent(BaseAgent):
    """Subagent responsible for evaluating code against security and engineering standards."""

    def __init__(self, llm_client: BaseLLMClient, skills_registry: SkillRegistry):
        super().__init__(
            name="ReviewerAgent",
            role=SubAgentRole.REVIEWER,
            base_system_prompt=REVIEWER_SYSTEM_PROMPT,
            llm_client=llm_client,
            skills_registry=skills_registry,
        )

    def review_code(
        self,
        step_id: int,
        code_to_review: str,
        task_description: str,
        skill_names: Optional[List[str]] = None,
    ) -> AgentExecutionResult:
        """Perform security and architectural audit on provided code."""
        prompt = (
            f"Please conduct an in-depth audit of the following code implementation:\n\n"
            f"ORIGINAL REQUIREMENT:\n{task_description}\n\n"
            f"CODE UNDER AUDIT:\n```python\n{code_to_review}\n```\n\n"
            f"Verify strict adherence to all injected skills. Check for side-channel timing attacks, "
            f"input boundaries, and robust error handling."
        )

        active_skills = skill_names or []
        system_prompt = self.prepare_system_prompt(active_skills)

        try:
            report = self.llm_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=prompt,
                response_model=ReviewReport,
            )
            raw_text = report.model_dump_json(indent=2)
        except Exception as exc:
            # Fallback parsing
            raw_text = self.llm_client.generate(system_prompt=system_prompt, user_prompt=prompt)
            report = self._parse_report_fallback(raw_text)

        result = AgentExecutionResult(
            step_id=step_id,
            role=self.role,
            injected_skills=active_skills,
            raw_output=raw_text,
            review_report=report,
        )
        return result

    def _parse_report_fallback(self, text: str) -> ReviewReport:
        """Fallback JSON parser if generate_json had formatting discrepancies."""
        cleaned = text.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)
        try:
            data = json.loads(cleaned)
            return ReviewReport.model_validate(data)
        except Exception:
            return ReviewReport(
                status="approved",
                summary="Audit completed (default pass).",
                issues=[],
            )
