<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Implementation Plan: Buzzword Categories](#implementation-plan-buzzword-categories)
  - [Summary](#summary)
  - [Technical Context](#technical-context)
  - [Constitution Check](#constitution-check)
  - [Project Structure](#project-structure)
    - [Documentation (this feature)](#documentation-this-feature)
    - [Source Code (repository root)](#source-code-repository-root)
  - [Complexity Tracking](#complexity-tracking)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Implementation Plan: Buzzword Categories

**Branch**: `004-buzzword-categories` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-buzzword-categories/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command.
See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a `Category` model with a mandatory many-to-many relationship to the existing `Buzzword` model (every buzzword requires at least one category; a category can tag many buzzwords), and change game creation from its current single-step "name only" form into a flow where the creator first filters by category, then selects the specific buzzwords for that game (at least one required), and that selection is persisted as the game's own buzzword pool.
Board generation at join time draws only from the created game's pool instead of the global active-buzzword set, preserving the existing insufficient-pool handling.
Category management is exposed the same way `Buzzword` already is: through Django admin, no new user roles, and deactivate-only — hard deletion of a category is never offered, closing off any path to a buzzword being silently stranded with zero categories.

## Technical Context

**Language/Version**: Python 3.14 (per repo-root `pyproject.toml`) **Primary Dependencies**: Django ≥6.0.7, `django-htmx` (already wired in `002-buzzword-bingo-game`), no new dependencies **Storage**: PostgreSQL, via the existing `bingo` app models/migrations **Testing**: pytest + `pytest-django` + `hypothesis` for domain/model-level tests, Django test client for view/HTMX-fragment integration tests, existing Playwright e2e suite in `frontend/e2e/` extended for the new creation-flow screens **Target Platform**: Linux server (Kubernetes), same ASGI entrypoint as the rest of `bingo` **Project Type**: Single Django project (`backend/`); `frontend/` remains limited to small, 100%-covered TypeScript enhancements per the constitution, no new JS framework **Performance Goals**: No new performance targets beyond the existing SC-001 (category filter interaction completes in <10s, a UI responsiveness bound, not a load target) **Constraints**: A `Buzzword` MUST NOT exist with zero categories (FR-001); a `Game` MUST NOT be created with zero buzzwords selected (FR-012); deactivating/removing a category MUST NOT corrupt existing buzzwords, games, or boards (FR-009/FR-010); illegal states unrepresentable via strict typing (constitution Principle V) **Scale/Scope**: One new model (`Category`), one new M2M (`Buzzword.categories`), one new M2M (`Game.buzzword_pool`), admin registration for `Category`, `BuzzwordAdmin` updated for the mandatory M2M, game-creation view/form/template reworked into a two-part category→buzzword selection step, `join_game` updated to draw from `game.buzzword_pool` instead of the global active pool, one new migration

## Constitution Check

*GATE: Must pass before Phase 0 research.*
*Re-check after Phase 1 design.*

| Principle | Verdict | Rationale |
|---|---|---|
| I. Strict Test-Driven Development | PASS | New model invariants (mandatory category, `m2m_changed` guard against removing the last category) and the updated `select_random_words` call site (drawing from `game.buzzword_pool` instead of the global pool) get pytest-django/hypothesis tests written before implementation, mirroring 002's approach. |
| II. Separation of Concerns & Modularity | PASS | `domain.py` stays untouched (word-selection/win-detection logic is pool-agnostic — it already accepts an arbitrary `pool: Sequence[T]`); only the call site in `views.py` changes which queryset it passes in. `models.py` gains schema + the M2M-guard signal; forms/admin stay the presentation/validation layer. |
| III. Documentation First | PASS (same mitigation as 001/002) | New Sphinx-mirrored notes added under `docs/sphinx/` for the category concept and updated creation flow, alongside the existing mkdocs docs. |
| IV. Functional Programming Patterns | PASS | No new stateful abstractions; category filtering is a pure queryset-narrowing operation (`Buzzword.objects.filter(categories__in=selected, active=True).distinct()`), and the "at least one buzzword selected" check is a pure predicate over submitted form data. |
| V. Strong Typing & Safe Types | PASS | `Category` and the new M2M relations are fully type-annotated; the "must select ≥1 buzzword" and "must have ≥1 category" rules are enforced as `forms.ModelMultipleChoiceField` validation (rejecting an empty selection) rather than only checked ad hoc, keeping the illegal state (zero-category buzzword, zero-buzzword game) unrepresentable at the point of entry. Django ORM's inherent M2M looseness (no DB-level "at least one" constraint) is mitigated with an `m2m_changed` signal guard, documented as a deliberate, narrow exception since Django has no declarative way to express a minimum-cardinality M2M constraint. |
| Technology & Constraints | PASS | Pure Django + HTMX; no new JS framework. Any new interactive category/buzzword checklist behavior beyond server-rendered HTMX swaps is written in TypeScript with 100% coverage, consistent with existing `frontend/src/*.ts` modules. |
| Governance (refactor-first workflow) | CONCERN, mitigated | `create_game`/`join_game` in `views.py` and `bingo/home.html` are existing, working code (not a stub) — this feature refactors them to add a selection step. Per the constitution's "refactor first, in a dedicated step" rule, the plan's task breakdown MUST do the `create_game` restructuring (extracting the buzzword-selection concern) as its own preparatory step before adding new category-filter behavior on top, not interleaved. |

No Complexity Tracking entries are required beyond the one documented governance mitigation above; the `m2m_changed` guard is the only deliberate deviation from "constraints expressed purely declaratively," and it is justified because Django's ORM has no built-in minimum-cardinality M2M validator.

## Project Structure

### Documentation (this feature)

```text
specs/004-buzzword-categories/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md         # Phase 1 output (/speckit.plan command)
├── contracts/             # Phase 1 output (/speckit.plan command)
│   └── routes.md          # Updated/added bingo app routes for this feature
├── checklists/
│   └── requirements.md
└── tasks.md               # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── bingo/
│   ├── models.py                  # +Category, +Buzzword.categories (M2M), +Game.buzzword_pool (M2M),
│   │                               #  +m2m_changed guard against a buzzword losing its last category
│   ├── forms.py                   # +CategoryFilterForm (multi-select, optional),
│   │                               #  +BuzzwordPoolForm (ModelMultipleChoiceField, required, ≥1)
│   ├── views.py                   # create_game reworked into a category-filter + buzzword-selection
│   │                               #  step before Game creation; join_game reads game.buzzword_pool
│   │                               #  instead of the global active-Buzzword queryset
│   ├── admin.py                   # +CategoryAdmin (create/rename/deactivate, mirrors BuzzwordAdmin);
│   │                               #  BuzzwordAdmin gains a `categories` field/filter, form-level
│   │                               #  validation requiring ≥1 category
│   ├── migrations/
│   │   └── 0003_category_buzzword_categories_game_buzzword_pool.py  # new
│   └── templates/bingo/
│       ├── home.html               # extended: category checklist → buzzword checklist → submit
│       └── partials/
│           └── _buzzword_choices.html  # new: HTMX-swapped buzzword checklist filtered by category
└── tests/
    ├── unit/
    │   └── test_models.py          # category-cardinality guard, M2M behavior (existing file extended)
    └── integration/
        └── test_bingo_views.py     # create_game (category filter + mandatory selection),
                                     # join_game (pool now sourced from game.buzzword_pool)

frontend/
└── src/
    └── buzzword-picker.ts          # new, only if plain HTMX swaps are insufficient for
                                     # select-all/clear-selection UX; 100% unit-test coverage required

docs/
└── sphinx/
    └── categories.md               # new: category concept + updated creation-flow docs
```

**Structure Decision**: Continues the single Django project layout established in `002-buzzword-bingo-game` (`backend/` only).
This feature is additive to the existing `bingo` app — one new model, two new M2M relations, one new migration — plus a refactor of the existing `create_game`/`join_game` views and `home.html` template to add the category→buzzword selection step.
No new app, no new project, no `frontend/` framework change.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `m2m_changed` signal guard on `Buzzword.categories` | Django's ORM has no declarative "minimum cardinality" validator for M2M fields; FR-001 requires a buzzword to never exist with zero categories, including when categories are removed after creation, not just at initial save | Relying on form-level validation alone (`ModelMultipleChoiceField(required=True)`) only covers the admin/creation UI path — it does not stop a category being unassigned later via the Django shell, a bulk admin action, or a future API, so a signal-level guard is the only way to make the illegal state unrepresentable everywhere |
