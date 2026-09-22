---
name: clean_architecture
title: Clean Architecture & SOLID Engineering Standards
version: 1.1.0
target_agents:
  - developer
  - reviewer
description: Architectural and software craftsmanship principles for production-grade Python services, emphasizing SOLID, modularity, type hints, and separation of concerns.
tags:
  - clean_code
  - solid
  - typing
  - architecture
---

# Clean Architecture & SOLID Principles

You must design and implement software following these principles:

## 1. Single Responsibility & Interface Segregation
- Each class or module must have one and only one reason to change.
- Separate business logic (domain service) from transport/protocol layers (HTTP/CLI) and storage implementations (in-memory, Redis, DB).
- Prefer small, focused interfaces/protocols over monolithic god-classes.

## 2. Dependency Inversion & Testability
- High-level business logic must not depend directly on low-level infrastructure details. Both should depend on abstractions (e.g. `Protocol` or `ABC`).
- Inject dependencies explicitly via constructors (`__init__`) rather than hardcoding global instances or singletons.

## 3. Strict Type Annotations & Data Contracts
- Use explicit Python type hints everywhere (arguments, return types, attributes).
- Use `Pydantic` models or `@dataclass(frozen=True)` for domain data structures and Data Transfer Objects (DTOs).
- Avoid untyped `dict` or generic `Any` for business data representations.

## 4. Robust Error Handling & Predictable Control Flow
- Define custom domain exception hierarchies (e.g. `AppError`, `ValidationError`, `NotFoundError`).
- Never catch generic `Exception` silently or with empty `pass` blocks.
- Keep methods concise, readable, and self-documenting with clean docstrings.
