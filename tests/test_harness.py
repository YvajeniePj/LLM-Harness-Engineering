import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.agents.dispatcher import DispatcherAgent
from src.llm.client import MockLLMClient
from src.schema import ReviewReport, ReviewSeverity, SubAgentRole
from src.skills.registry import SkillRegistry


def test_skills_loading():
    """Verify that external markdown skills are discovered and parsed with frontmatter."""
    registry = SkillRegistry()
    skills = registry.list_skills()

    assert len(skills) >= 2, f"Expected at least 2 skills, found {len(skills)}"
    skill_names = {s.name for s in skills}
    assert "security_owasp" in skill_names
    assert "clean_architecture" in skill_names
    assert "pytest_testing" in skill_names


def test_skills_injection_formatting():
    """Verify runtime injection formatting block contains rules and metadata."""
    registry = SkillRegistry()
    injected_block = registry.format_skills_injection(["security_owasp"])

    assert "RUNTIME INJECTED SKILLS" in injected_block
    assert "Constant-Time Comparison" in injected_block
    assert "OWASP Secure Coding" in injected_block


def test_review_report_approval_logic():
    """Verify ReviewReport helper properties."""
    approved_report = ReviewReport(status="approved", summary="All good", issues=[])
    assert approved_report.is_approved is True

    rejected_report = ReviewReport(
        status="changes_requested",
        summary="Found flaws",
        issues=[
            {
                "severity": ReviewSeverity.CRITICAL,
                "rule_violated": "security_owasp",
                "description": "Timing attack",
                "suggestion": "Use hmac.compare_digest",
            }
        ],
    )
    assert rejected_report.is_approved is False


def test_dispatcher_harness_full_loop():
    """Verify full end-to-end execution of Dispatcher with Mock LLM."""
    registry = SkillRegistry()
    llm = MockLLMClient()
    dispatcher = DispatcherAgent(llm_client=llm, skills_registry=registry)

    events = []

    def on_event(event_type, data):
        events.append(event_type)

    request = "Implement a secure token manager in Python."
    artifacts = dispatcher.run_harness(request, on_event=on_event)

    assert "PLANNING_COMPLETED" in events
    assert "SKILL_INJECTION" in events
    assert "REVIEW_COMPLETED" in events
    assert "FEEDBACK_LOOP_TRIGGERED" in events
    assert "HARNESS_COMPLETED" in events

    assert "SessionTokenManager" in artifacts["code"]
    assert "hmac.compare_digest" in artifacts["code"]
    assert "test_issue_token_success" in artifacts["tests"]
    assert len(artifacts["review_history"]) >= 2
