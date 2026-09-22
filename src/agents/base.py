"""Base subagent class with dynamic skills injection capabilities."""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from src.llm.client import BaseLLMClient
from src.schema import AgentExecutionResult, SubAgentRole
from src.skills.registry import SkillRegistry


class BaseAgent:
    """Base class for specialized subagents inside the Harness execution context."""

    def __init__(
        self,
        name: str,
        role: SubAgentRole,
        base_system_prompt: str,
        llm_client: BaseLLMClient,
        skills_registry: SkillRegistry,
    ):
        self.name = name
        self.role = role
        self.base_system_prompt = base_system_prompt
        self.llm_client = llm_client
        self.skills_registry = skills_registry

    def prepare_system_prompt(self, skill_names: List[str]) -> str:
        """Compose the runtime system prompt by dynamically injecting requested skills.
        
        This prevents context bloat: agents only receive guidelines relevant
        to their current subtask.
        """
        parts = [self.base_system_prompt]

        if skill_names:
            skills_block = self.skills_registry.format_skills_injection(skill_names)
            if skills_block:
                parts.append("\n" + skills_block)

        return "\n\n".join(parts)

    def execute(
        self,
        step_id: int,
        task_prompt: str,
        skill_names: Optional[List[str]] = None,
        context: Optional[Dict[str, str]] = None,
    ) -> AgentExecutionResult:
        """Execute a subtask with dynamic skill injection."""
        active_skills = skill_names or []
        system_prompt = self.prepare_system_prompt(active_skills)

        # Append optional context from previous subagent steps
        user_prompt = task_prompt
        if context:
            context_blocks = ["### PREVIOUS STEP ARTIFACTS / CONTEXT:"]
            for key, val in context.items():
                context_blocks.append(f"#### {key}:\n```\n{val}\n```")
            user_prompt = f"{user_prompt}\n\n" + "\n\n".join(context_blocks)

        start_time = time.time()
        output = self.llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        duration = time.time() - start_time

        return AgentExecutionResult(
            step_id=step_id,
            role=self.role,
            injected_skills=active_skills,
            raw_output=output,
            execution_time_sec=round(duration, 3),
        )
