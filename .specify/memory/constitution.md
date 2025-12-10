<!--
Sync Impact Report:
- Version change: 0.0.0 -> 1.0.0 (Initial adoption)
- Modified principles: Defined Principles I-IV based on project requirements.
- Added sections: Technology & Constraints, Development Workflow.
- Removed sections: Unused Principle 5 placeholder.
- Templates requiring updates:
  - .specify/templates/tasks-template.md (✅ updated to enforce TDD)
  - .specify/templates/plan-template.md (✅ verified)
  - .specify/templates/spec-template.md (✅ verified)
- Follow-up TODOs: None.
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

## Technology & Constraints

<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->

The Application is written in `Python` and uses `Django` as the backend framework.
The frontend is built with `HTMX`.
Do not introduce any other JavaScript frameworks or libraries; if custom code has to be written for the frontend, it must be written with TypeScript and have 100% test coverage.
The documentation is built with `MyST` and `Sphinx`.
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

**Version**: 1.0.0 | **Ratified**: 2025-12-10 | **Last Amended**: 2025-12-10
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
