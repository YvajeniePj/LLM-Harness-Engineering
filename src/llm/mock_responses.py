"""Deterministic realistic mock responses for Software Engineering domain.

Enables out-of-the-box instant execution and grading without requiring API keys.
"""

MOCK_CASE_1_TOKEN_MANAGER = {
    "dispatcher_plan": """{
  "task_description": "Design and implement a production-grade Secure Session Token Manager in Python with validation, expiration checks, and thorough tests.",
  "rationale": "High-risk cryptographic component. Requires strict adherence to OWASP security guidelines (timing-attack prevention) and clean architecture, followed by independent security review and automated test coverage.",
  "steps": [
    {
      "step_id": 1,
      "title": "Initial Implementation of SessionTokenManager",
      "role": "developer",
      "skill_names": ["clean_architecture"],
      "instructions": "Implement SessionTokenManager class with issue_token, validate_token, revoke_token, and cleanup_expired methods. Ensure type hints and proper exception hierarchy."
    },
    {
      "step_id": 2,
      "title": "Security & Architecture Code Audit",
      "role": "reviewer",
      "skill_names": ["security_owasp", "clean_architecture"],
      "instructions": "Audit SessionTokenManager implementation against OWASP top 10 guidelines, timing attack vulnerabilities, and clean code principles."
    },
    {
      "step_id": 3,
      "title": "Comprehensive Pytest Suite Generation",
      "role": "tester",
      "skill_names": ["pytest_testing"],
      "instructions": "Generate comprehensive pytest suite adhering to AAA pattern, boundary testing, token expiration, and security regression checks."
    }
  ]
}""",

    "developer_initial_code": '''"""Session Token Manager Module."""

from __future__ import annotations

import time
import secrets
from dataclasses import dataclass
from typing import Dict, Optional


class TokenError(Exception):
    """Base domain exception for token operations."""


class TokenNotFoundError(TokenError):
    """Raised when token does not exist."""


class TokenExpiredError(TokenError):
    """Raised when token has exceeded TTL."""


class InvalidTokenFormatError(TokenError):
    """Raised when token string fails format constraints."""


@dataclass(frozen=True)
class SessionToken:
    """Immutable representation of an active session token."""
    token_id: str
    user_id: str
    created_at: float
    expires_at: float
    metadata: Dict[str, str]

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class SessionTokenManager:
    """Manages generation, storage, and validation of user session tokens."""

    def __init__(self, default_ttl_seconds: int = 3600):
        self._tokens: Dict[str, SessionToken] = {}
        self._default_ttl = default_ttl_seconds

    def issue_token(self, user_id: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """Issue a cryptographically secure session token."""
        if not user_id or not user_id.strip():
            raise InvalidTokenFormatError("User ID must not be empty.")

        token_id = secrets.token_urlsafe(32)
        now = time.time()
        session = SessionToken(
            token_id=token_id,
            user_id=user_id,
            created_at=now,
            expires_at=now + self._default_ttl,
            metadata=metadata or {},
        )
        self._tokens[token_id] = session
        return token_id

    def validate_token(self, token_id: str) -> SessionToken:
        """Validate token and return active session.
        
        NOTE: Basic lookup for session token.
        """
        if not token_id or len(token_id) < 16:
            raise InvalidTokenFormatError("Invalid token format or length.")

        # VULNERABILITY: Iterating and using naive string equality check
        matched_token: Optional[SessionToken] = None
        for stored_id, session in self._tokens.items():
            if stored_id == token_id:  # Naive equality vulnerable to timing attacks
                matched_token = session
                break

        if not matched_token:
            raise TokenNotFoundError("Provided session token does not exist.")

        if matched_token.is_expired:
            del self._tokens[matched_token.token_id]
            raise TokenExpiredError("Session token has expired.")

        return matched_token

    def revoke_token(self, token_id: str) -> None:
        """Revoke and delete a session token."""
        if token_id in self._tokens:
            del self._tokens[token_id]

    def cleanup_expired(self) -> int:
        """Prune expired tokens and return count of deleted sessions."""
        now = time.time()
        expired_keys = [k for k, v in self._tokens.items() if now > v.expires_at]
        for key in expired_keys:
            del self._tokens[key]
        return len(expired_keys)
''',

    "reviewer_rejection": """{
  "status": "changes_requested",
  "summary": "Code structure and Clean Architecture are excellent. However, a CRITICAL security vulnerability was detected during validation check regarding timing attacks.",
  "issues": [
    {
      "severity": "critical",
      "rule_violated": "security_owasp / Section 1. Cryptographic Security & Timing Attack Prevention",
      "description": "In `validate_token`, comparison `stored_id == token_id` utilizes standard Python string equality. This is susceptible to side-channel timing attacks, leaking token prefix bytes.",
      "suggestion": "Replace naive equality check with constant-time comparison `secrets.compare_digest(stored_id, token_id)` or `hmac.compare_digest` to guarantee constant-time execution."
    },
    {
      "severity": "warning",
      "rule_violated": "security_owasp / Section 2. Input Validation",
      "description": "Length check `len(token_id) < 16` allows arbitrary large payload strings, opening possibilities for unbounded memory pressure.",
      "suggestion": "Constrain maximum allowable token length (e.g. `len(token_id) > 128` should immediately raise `InvalidTokenFormatError`)."
    }
  ]
}""",

    "developer_fixed_code": '''"""Session Token Manager Module (Hardened against OWASP Guidelines)."""

from __future__ import annotations

import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Dict, Optional


class TokenError(Exception):
    """Base domain exception for token operations."""


class TokenNotFoundError(TokenError):
    """Raised when token does not exist."""


class TokenExpiredError(TokenError):
    """Raised when token has exceeded TTL."""


class InvalidTokenFormatError(TokenError):
    """Raised when token string fails format constraints."""


@dataclass(frozen=True)
class SessionToken:
    """Immutable representation of an active session token."""
    token_id: str
    user_id: str
    created_at: float
    expires_at: float
    metadata: Dict[str, str]

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class SessionTokenManager:
    """Manages generation, storage, and validation of user session tokens."""

    MAX_TOKEN_LENGTH: int = 128
    MIN_TOKEN_LENGTH: int = 16

    def __init__(self, default_ttl_seconds: int = 3600):
        self._tokens: Dict[str, SessionToken] = {}
        self._default_ttl = default_ttl_seconds

    def issue_token(self, user_id: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """Issue a cryptographically secure session token."""
        if not user_id or not user_id.strip():
            raise InvalidTokenFormatError("User ID must not be empty.")

        token_id = secrets.token_urlsafe(32)
        now = time.time()
        session = SessionToken(
            token_id=token_id,
            user_id=user_id,
            created_at=now,
            expires_at=now + self._default_ttl,
            metadata=metadata or {},
        )
        self._tokens[token_id] = session
        return token_id

    def validate_token(self, token_id: str) -> SessionToken:
        """Validate token using constant-time comparison against timing attacks."""
        if not isinstance(token_id, str):
            raise InvalidTokenFormatError("Token must be a valid string.")

        if not (self.MIN_TOKEN_LENGTH <= len(token_id) <= self.MAX_TOKEN_LENGTH):
            raise InvalidTokenFormatError(
                f"Token length must be between {self.MIN_TOKEN_LENGTH} and {self.MAX_TOKEN_LENGTH} chars."
            )

        # Constant-time lookup prevents timing side-channel attacks
        matched_token: Optional[SessionToken] = None
        for stored_id, session in self._tokens.items():
            if hmac.compare_digest(stored_id, token_id):
                matched_token = session
                break

        if not matched_token:
            raise TokenNotFoundError("Provided session token does not exist or has been revoked.")

        if matched_token.is_expired:
            self._tokens.pop(matched_token.token_id, None)
            raise TokenExpiredError("Session token has expired.")

        return matched_token

    def revoke_token(self, token_id: str) -> None:
        """Revoke and securely delete a session token."""
        if not isinstance(token_id, str):
            return
        self._tokens.pop(token_id, None)

    def cleanup_expired(self) -> int:
        """Prune expired tokens and return count of deleted sessions."""
        now = time.time()
        expired_keys = [k for k, v in self._tokens.items() if now > v.expires_at]
        for key in expired_keys:
            self._tokens.pop(key, None)
        return len(expired_keys)
''',

    "reviewer_approval": """{
  "status": "approved",
  "summary": "All critical security and architecture concerns resolved. Code adheres strictly to OWASP guidelines and Clean Architecture.",
  "issues": []
}""",

    "tester_code": '''"""Automated test suite for SessionTokenManager following Pytest TDD patterns."""

import time
import pytest

# Under test imports
from session_manager import (
    SessionTokenManager,
    InvalidTokenFormatError,
    TokenNotFoundError,
    TokenExpiredError,
)


@pytest.fixture
def token_manager() -> SessionTokenManager:
    """Fixture providing a fresh SessionTokenManager with 2-second TTL for testing."""
    return SessionTokenManager(default_ttl_seconds=2)


def test_issue_token_success(token_manager: SessionTokenManager):
    """Arrange, Act, Assert: Issue token generates valid token with correct metadata."""
    # Arrange
    user_id = "user_42"
    meta = {"role": "admin", "ip": "127.0.0.1"}

    # Act
    token = token_manager.issue_token(user_id=user_id, metadata=meta)

    # Assert
    assert isinstance(token, str)
    assert len(token) >= 32
    session = token_manager.validate_token(token)
    assert session.user_id == user_id
    assert session.metadata["role"] == "admin"


def test_issue_token_empty_user_raises_error(token_manager: SessionTokenManager):
    """Arrange, Act, Assert: Empty user_id must raise InvalidTokenFormatError."""
    # Arrange
    empty_user = "   "

    # Act & Assert
    with pytest.raises(InvalidTokenFormatError):
        token_manager.issue_token(user_id=empty_user)


def test_validate_token_constant_time_comparison(token_manager: SessionTokenManager):
    """Verify that tampering even a single byte rejects token safely."""
    # Arrange
    valid_token = token_manager.issue_token("alice")
    tampered_token = valid_token[:-1] + ("0" if valid_token[-1] != "0" else "1")

    # Act & Assert
    with pytest.raises(TokenNotFoundError):
        token_manager.validate_token(tampered_token)


def test_validate_token_exceeding_max_length(token_manager: SessionTokenManager):
    """Enforce boundary length checks to prevent buffer/memory exhaustion."""
    # Arrange
    oversized_token = "A" * 200

    # Act & Assert
    with pytest.raises(InvalidTokenFormatError):
        token_manager.validate_token(oversized_token)


def test_token_expiration(token_manager: SessionTokenManager):
    """Verify expired token raises TokenExpiredError and gets cleaned up."""
    # Arrange
    token = token_manager.issue_token("bob")

    # Act
    time.sleep(2.1)

    # Assert
    with pytest.raises(TokenExpiredError):
        token_manager.validate_token(token)


def test_revoke_token(token_manager: SessionTokenManager):
    """Verify revoked token cannot be validated."""
    # Arrange
    token = token_manager.issue_token("charlie")
    assert token_manager.validate_token(token) is not None

    # Act
    token_manager.revoke_token(token)

    # Assert
    with pytest.raises(TokenNotFoundError):
        token_manager.validate_token(token)
'''
}
