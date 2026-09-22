---
name: security_owasp
title: OWASP Secure Coding & Vulnerability Audit Standards
version: 1.2.0
target_agents:
  - reviewer
  - developer
description: Industry-grade security rules for Python backend systems to prevent OWASP Top 10 vulnerabilities, timing attacks, data leaks, and insecure data handling.
tags:
  - security
  - owasp
  - cryptography
  - backend
---

# Secure Coding & Vulnerability Audit Guidelines

You must adhere to and audit against the following security requirements:

## 1. Cryptographic Security & Timing Attack Prevention
- **Constant-Time Comparison**: NEVER use standard equality operators (`==`, `!=`) for comparing cryptographic tokens, API keys, hashes, or passwords. ALWAYS use `hmac.compare_digest(a, b)` or `secrets.compare_digest(a, b)`.
- **Cryptographic Randomness**: NEVER use `random` for security tokens, session IDs, or nonces. Use `secrets.token_urlsafe()` or `secrets.token_hex()`.
- **Hashing**: Use modern salted algorithms (e.g. `argon2`, `bcrypt`, or `hashlib.pbkdf2_hmac` / SHA-256 with salt) for secrets; never raw MD5 or plain SHA-1.

## 2. Input Validation & Type Safety
- **Strict Boundary Checks**: Enforce length limits, valid characters, and expected ranges before processing any payload.
- **Fail-Closed**: If validation fails, immediately raise specific exceptions and terminate execution; never attempt best-effort continuation on malformed inputs.
- **No Direct Shell / Code Execution**: Ban `eval()`, `exec()`, `pickle.loads()` on untrusted input, and `shell=True` in `subprocess`.

## 3. Data Sanitization & Information Leakage
- **Exception Sanitization**: Do not expose raw internal tracebacks, database schema details, or server paths in client-facing error responses.
- **Secret Masking**: Passwords, bearer tokens, and private keys must be scrubbed/masked from log outputs (use structured redaction).

## 4. Rate Limiting & Resource Exhaustion (DoS)
- Include checks for request frequency, maximum payload size, and bounded loop iterations to prevent CPU or memory exhaustion.
