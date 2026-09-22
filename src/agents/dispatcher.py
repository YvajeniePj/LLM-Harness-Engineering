"""Root Harness Orchestrator (Dispatcher) with metaprompt and hierarchical execution."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel

from src.agents.developer import DeveloperAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.tester import TestAgent
from src.llm.client import BaseLLMClient
from src.schema import (
    AgentExecutionResult,
    ExecutionPlan,
    ReviewReport,
    SubAgentRole,
    TaskStep,
)
from src.skills.registry import SkillRegistry

DISPATCHER_METAPROMPT = """You are the ROOT HARNESS ORCHESTRATOR (Dispatcher Agent).
Your sole purpose is to supervise and coordinate multi-agent execution for complex software engineering problems.

STRICT OPERATIONAL RULES:
1. You DO NOT write code or tests yourself.
2. You decompose complex requirements into an ExecutionPlan containing discrete TaskSteps.
3. For each step, you assign the specialized subagent role (developer, reviewer, or tester)
   and determine which modular Skills from the skills catalog must be dynamically injected.
4. You enforce the Feedback Loop: If ReviewerAgent requests changes due to security or architectural
   flaws, you route the findings back to DeveloperAgent for a remediation pass before proceeding to testing.
"""


class DispatcherAgent:
    """Central orchestrator managing task decomposition, skills assignment, and subagent execution."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        skills_registry: SkillRegistry,
        max_feedback_iterations: int = 2,
    ):
        self.llm_client = llm_client
        self.skills_registry = skills_registry
        self.max_feedback_iterations = max_feedback_iterations

        # Initialize subagents
        self.developer = DeveloperAgent(llm_client, skills_registry)
        self.reviewer = ReviewerAgent(llm_client, skills_registry)
        self.tester = TestAgent(llm_client, skills_registry)

    def plan_task(self, user_request: str) -> ExecutionPlan:
        """Decompose user request into a structured multi-agent execution plan."""
        skills = self.skills_registry.list_skills()
        skills_catalog_desc = "\n".join(
            f"- '{s.name}': {s.title} (targets: {', '.join(s.target_agents)}) -> {s.description}"
            for s in skills
        )

        user_prompt = (
            f"USER REQUEST:\n{user_request}\n\n"
            f"AVAILABLE MODULAR SKILLS CATALOG:\n{skills_catalog_desc}\n\n"
            f"Create a multi-step ExecutionPlan. Assign subagents (developer, reviewer, tester) "
            f"and choose which skill_names to dynamically inject into each step."
        )

        try:
            plan = self.llm_client.generate_json(
                system_prompt=DISPATCHER_METAPROMPT,
                user_prompt=user_prompt,
                response_model=ExecutionPlan,
            )
            return plan
        except Exception:
            # Fallback robust default plan for Software Engineering
            return ExecutionPlan(
                task_description=user_request,
                rationale="Fallback SE multi-stage pipeline: implementation with clean architecture -> security review -> test generation.",
                steps=[
                    TaskStep(
                        step_id=1,
                        title="Develop Initial Solution",
                        role=SubAgentRole.DEVELOPER,
                        skill_names=["clean_architecture"],
                        instructions="Implement production-grade solution with clean design and type hints.",
                    ),
                    TaskStep(
                        step_id=2,
                        title="Conduct Security & Standards Audit",
                        role=SubAgentRole.REVIEWER,
                        skill_names=["security_owasp", "clean_architecture"],
                        instructions="Audit code against OWASP standards, timing attacks, and boundary checks.",
                    ),
                    TaskStep(
                        step_id=3,
                        title="Generate Comprehensive Test Suite",
                        role=SubAgentRole.TESTER,
                        skill_names=["pytest_testing"],
                        instructions="Generate pytest test suite covering normal, boundary, and security test cases.",
                    ),
                ],
            )

    def run_harness(
        self,
        user_request: str,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Execute complete Harness loop with skills injection and feedback cycles."""

        def notify(event_type: str, data: Dict[str, Any]):
            if on_event:
                on_event(event_type, data)

        start_time = time.time()
        notify("HARNESS_STARTED", {"request": user_request})

        # Phase 1: Planning
        notify("PLANNING_STARTED", {})
        plan = self.plan_task(user_request)
        notify("PLANNING_COMPLETED", {"plan": plan})

        artifacts: Dict[str, Any] = {
            "request": user_request,
            "plan": plan,
            "code": "",
            "review_history": [],
            "tests": "",
            "metrics": {},
        }

        # Phase 2: Code Generation by Developer
        dev_step = next((s for s in plan.steps if s.role == SubAgentRole.DEVELOPER), plan.steps[0])
        notify("SKILL_INJECTION", {"agent": "DeveloperAgent", "skills": dev_step.skill_names})
        notify("STEP_STARTED", {"step": dev_step, "agent": "DeveloperAgent"})

        dev_res = self.developer.generate_solution(
            step_id=dev_step.step_id,
            task_description=user_request,
            skill_names=dev_step.skill_names,
        )
        current_code = dev_res.code_artifacts.get("solution.py", dev_res.raw_output)
        artifacts["code"] = current_code
        notify("STEP_COMPLETED", {"step": dev_step, "agent": "DeveloperAgent", "result": dev_res})

        # Phase 3: Review & Feedback Loop
        rev_step = next((s for s in plan.steps if s.role == SubAgentRole.REVIEWER), None)
        rev_skills = rev_step.skill_names if rev_step else ["security_owasp", "clean_architecture"]

        for iteration in range(1, self.max_feedback_iterations + 1):
            notify("SKILL_INJECTION", {"agent": "ReviewerAgent", "skills": rev_skills})
            notify("STEP_STARTED", {"step_id": 2, "agent": "ReviewerAgent", "iteration": iteration})

            rev_res = self.reviewer.review_code(
                step_id=2,
                code_to_review=current_code,
                task_description=user_request,
                skill_names=rev_skills,
            )
            report: ReviewReport = rev_res.review_report or ReviewReport(
                status="approved", summary="Passed without objections", issues=[]
            )
            artifacts["review_history"].append(report)
            notify("REVIEW_COMPLETED", {"report": report, "iteration": iteration})

            if report.is_approved:
                notify("REVIEW_APPROVED", {"iteration": iteration})
                break

            # Feedback Loop: Reviewer rejected code, route to Developer for fix
            notify("FEEDBACK_LOOP_TRIGGERED", {"issues": report.issues, "iteration": iteration})
            fix_res = self.developer.apply_revision(
                step_id=20 + iteration,
                original_code=current_code,
                review_report=report,
                skill_names=["clean_architecture", "security_owasp"],
            )
            current_code = fix_res.code_artifacts.get("solution.py", fix_res.raw_output)
            artifacts["code"] = current_code
            notify("CODE_REVISED", {"iteration": iteration, "new_code": current_code})

        # Phase 4: Test Suite Generation
        test_step = next((s for s in plan.steps if s.role == SubAgentRole.TESTER), None)
        test_skills = test_step.skill_names if test_step else ["pytest_testing"]

        notify("SKILL_INJECTION", {"agent": "TestAgent", "skills": test_skills})
        notify("STEP_STARTED", {"step_id": 3, "agent": "TestAgent"})

        test_res = self.tester.generate_tests(
            step_id=3,
            task_description=user_request,
            solution_code=current_code,
            skill_names=test_skills,
        )
        tests_code = test_res.code_artifacts.get("test_solution.py", test_res.raw_output)
        artifacts["tests"] = tests_code
        notify("STEP_COMPLETED", {"step_id": 3, "agent": "TestAgent", "result": test_res})

        total_duration = time.time() - start_time
        artifacts["metrics"]["total_duration_sec"] = round(total_duration, 2)
        notify("HARNESS_COMPLETED", {"artifacts": artifacts})

        return artifacts
