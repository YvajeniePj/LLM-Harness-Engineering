---
name: pytest_testing
title: Pytest TDD & Comprehensive Test Patterns
version: 1.0.0
target_agents:
  - tester
description: Best practices for engineering automated test suites using pytest, covering AAA structure, boundary testing, mock isolation, and security test cases.
tags:
  - pytest
  - testing
  - tdd
  - quality
---

# Pytest Testing Standards & Patterns

You must generate robust, self-contained automated tests according to these standards:

## 1. Structure & AAA Pattern
- Every test function must strictly follow the **Arrange - Act - Assert** pattern:
  - **Arrange**: Set up test fixtures, input parameters, and mocks.
  - **Act**: Invoke the single method/function under test.
  - **Assert**: Verify the expected outcome, state changes, and side-effects.
- Use explicit, descriptive test names in snake_case format: `test_<feature>_<condition>_<expected_result>()`.

## 2. Comprehensive Coverage & Boundary Cases
- **Happy Path**: Test standard valid scenarios with expected outputs.
- **Negative & Edge Cases**:
  - Null/empty inputs, boundary values (0, -1, max int, extreme string lengths).
  - Malformed tokens, invalid characters, expired TTLs.
  - Type errors and validation exceptions (`pytest.raises(CustomException)`).
- **Security Scenarios**: Explicitly verify constant-time comparison or rejection of timing attack inputs, invalid cryptographic tokens, and privilege escalation attempts.

## 3. Test Isolation & Mocking
- Tests must be completely independent and deterministic. Running tests in any order should produce identical results.
- Use pytest fixtures for reusable setup/teardown. Avoid sharing mutable global state between tests.
- When testing timing or network services, mock time or use explicit fixtures to avoid flaky sleep delays.
