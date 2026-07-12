<!--
Sync Impact Report:
- Version change: 1.1.1 -> 1.2.0
- Modified principles: Completed Principle V — Strong Typing & Safe Types (the v1.1.1
  Sync Impact Report claimed this principle was added, but the Core Principles body
  only ever contained I-IV; this amendment actually drafts and inserts the missing
  section rather than just updating metadata).
- Added sections: Principle V full text (Strong Typing & Safe Types); a Technology &
  Constraints line naming `pyrefly`/`ty` as the enforced static typing toolchain.
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/tasks-template.md (✅ already includes a strict-typing setup
    task — no change needed)
  - .specify/templates/plan-template.md (✅ verified — Constitution Check is filled
    dynamically per plan run, no static typing-specific text required)
  - .specify/templates/spec-template.md (✅ already includes an "illegal states
    unrepresentable through strict static typing" requirement — no change needed)
- Follow-up TODOs:
  - Wire `pyrefly`/`ty` strict-mode enforcement into CI (`.github/workflows/main.yaml`)
    — not yet implemented in any feature branch as of this amendment.
  - Add developer-facing onboarding documentation for the static typing toolchain.
- Note: this amendment corrects a governance drift where v1.1.1's own changelog
  claimed work that was never actually merged into the ratified body — surfaced by
  `/speckit-analyze` finding C2 on feature 001-django-postgresql-backend.
-->

# Bullshit Bingo Constitution

<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. Strict Test-Driven Development

<!-- Example: I. Library-First -->
TDD is mandatory.
Tests must be written before implementation.
Backend uses pytest with hypothesis for property-based testing.
Frontend uses playwright with fast-check. 100% test coverage required for custom TypeScript.
<!-- Example: Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries -->

### II. Separation of Concerns & Modularity

<!-- Example: II. CLI Interface -->
View logic, business logic, and database access must be strictly separated.
Modules must be small and serve a single purpose.
<!-- Example: Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats -->

### III. Documentation First

<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
Documentation is a first-class citizen.
All functions require docstrings explaining "why" and "when" (not "what").
User and developer documentation must be kept up-to-date in Sphinx.
<!-- Example: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced -->

### IV. Functional Programming Patterns

<!-- Example: IV. Integration Testing -->
We prefer functional programming patterns.
<!-- Example: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas -->

### V. Strong Typing & Safe Types

All Python code MUST be fully type-annotated; untyped function signatures and untyped module-level values are not permitted.
Static type checking MUST be enforced with `pyrefly` and `ty` in their strictest available settings, run in CI, failing the build on any error.
Prefer precise, narrow types (enums, `NewType`, `TypedDict`, dataclasses with `Final`/`Literal` fields) over `Any`, untyped `dict`/`list`, or stringly-typed values — illegal states MUST be unrepresentable in the type system rather than guarded against only at runtime.
Any `# type: ignore` or equivalent suppression MUST carry an inline comment explaining why the suppression is necessary.

## Technology & Constraints

<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->

The Application is written in `Python` and uses `Django` as the backend framework.
Authentication uses `python-social-auth` for identity integration and social login flows.
The frontend is built with `HTMX`.
Do not introduce any other JavaScript frameworks or libraries; if custom code has to be written for the frontend, it must be written with TypeScript and have 100% test coverage.
The documentation is built with `MyST` and `Sphinx`.
Static typing is enforced with `pyrefly` and `ty`, run in their strictest settings.
<!-- Example: Technology stack requirements, compliance standards, deployment policies, etc. -->

## Development Workflow

<!-- Example: Development Workflow, Review Process, Quality Gates, etc. -->

When a task requires refactoring of existing code, do the refactor first in a dedicated step.
<!-- Example: Code review requirements, testing gates, deployment approval process, etc. -->

## Governance

<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

This constitution supersedes all other practices.
Amendments require a version bump and documentation.
All PRs must verify compliance.
<!-- Example: All PRs/reviews must verify compliance; Complexity must be justified; Use [GUIDANCE_FILE] for runtime development guidance -->

**Version**: 1.2.0 | **Ratified**: 2025-12-10 | **Last Amended**: 2026-07-11
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
