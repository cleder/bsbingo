<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Implementation Plan: Buzzword Bingo Game](#implementation-plan-buzzword-bingo-game)
  - [Summary](#summary)
  - [Technical Context](#technical-context)
  - [Constitution Check](#constitution-check)
  - [Project Structure](#project-structure)
    - [Documentation (this feature)](#documentation-this-feature)
    - [Source Code (repository root)](#source-code-repository-root)
  - [Complexity Tracking](#complexity-tracking)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Implementation Plan: Buzzword Bingo Game

**Branch**: `002-buzzword-bingo-game` | **Date**: 2026-07-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-buzzword-bingo-game/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command.
See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build the core Buzzword Bingo gameplay on top of the already-scaffolded `bingo` Django app (currently an empty stub, not yet in `INSTALLED_APPS`) and the PostgreSQL backend wired in `001-django-postgresql-backend`.
The feature adds five models (`Buzzword`, `Game`, `Player`, `Board`, `BoardSquare`), four capability-URL routes (create game, join game, view board, HTMX cell toggle), server-rendered Django templates enhanced with HTMX partial swaps (no full page reloads), and Django admin registrations for buzzword/game/player/board management.
Game/board access is purely capability-based (unguessable UUID URLs) — there is no user login for players, consistent with the spec's explicit exclusion of accounts/authentication.
Win detection and board generation are implemented as pure, fully typed functions in a dedicated `bingo/domain.py` module, kept separate from views and Django ORM models per the constitution's separation-of-concerns and functional-programming principles.

## Technical Context

**Language/Version**: Python 3.14 (per repo-root `pyproject.toml` `requires-python`) **Primary Dependencies**: Django ≥6.0.7, `django-htmx` ≥1.27.0 (already a dependency, not yet wired into `INSTALLED_APPS`/`MIDDLEWARE`), `psycopg[binary,pool]` ≥3.3.4 (already configured by 001) **Storage**: PostgreSQL (already wired via `config.settings.{base,local,production,test}` from 001); this feature adds the first real application models and the first migration for the `bingo` app **Testing**: pytest + `pytest-django` + `hypothesis` (property-based tests for board generation and win detection), Django test client for endpoint/HTMX-fragment integration tests **Target Platform**: Linux server (Kubernetes), served via the existing ASGI entrypoint (`config.asgi:application`) **Project Type**: Single Django project (`backend/`) with server-rendered templates enhanced by HTMX; there is no separate `frontend/` project — none exists in the repo and the constitution requires HTMX rather than a JS framework **Performance Goals**: SC-004 — a single game supports ≥100 simultaneous participants, each cell-toggle request completing in under 500ms **Constraints**: No user accounts/authentication for players (FR-003); access to a game/board is controlled solely by possession of its unguessable UUID URL; finished games must reject all further mutations (FR-011); illegal states must be unrepresentable via strict typing and explicit domain types (FR-017, constitution Principle V) **Scale/Scope**: One Django app (`bingo`), 5 models, 1 migration, 4 HTTP routes, ~5 templates + 2 HTMX partials, admin registrations for all 5 models, a pure `domain.py` module for board generation and win detection

## Constitution Check

*GATE: Must pass before Phase 0 research.*
*Re-check after Phase 1 design.*

| Principle | Verdict | Rationale |
|---|---|---|
| I. Strict Test-Driven Development | PASS | Board generation (random word selection, no duplicates) and win detection (row/column/diagonal check) are pure functions in `domain.py`, ideal for hypothesis property-based tests written before implementation; endpoint behavior (join, toggle, admin) gets pytest-django integration tests written before the views. |
| II. Separation of Concerns & Modularity | PASS | `domain.py` holds board-generation and win-detection logic with no Django ORM or view imports; `views.py` stays thin (fetch/validate → call domain function → persist → render fragment); `models.py` holds only schema and state-transition-safe persistence helpers (e.g. the atomic conditional "finish game" update). |
| III. Documentation First | PASS (mitigated, same approach as 001 finding C1) | The repo's served docs are mkdocs-material, while the constitution mandates Sphinx/MyST. Following 001's precedent, this feature mirrors its player/admin setup notes into `docs/sphinx/` alongside the mkdocs equivalent, satisfying the MUST for this feature's own new documentation. The repo-wide mkdocs-vs-Sphinx question remains a separate, already-tracked gap. |
| IV. Functional Programming Patterns | PASS | Win detection (`has_bingo(marked_positions) -> bool`) and word selection (`select_random_words(pool, k, rng) -> list[...]`) are pure functions over immutable inputs, not stateful objects. |
| V. Strong Typing & Safe Types | PASS, with a carried-forward CONCERN | `GameStatus` is a `django.db.models.TextChoices` enum (not a raw string) for FR-017; board positions and winning lines in `domain.py` use `Final`/`frozenset[int]`/`NewType` rather than bare ints where it matters for correctness. Django ORM attributes themselves remain only partially checkable by `pyrefly`/`ty` without a Django type-stub plugin (no `django-stubs` in this repo) — this is the same repo-wide gap 001 flagged (CI enforcement not yet wired); new pure code in `domain.py` is fully type-annotated regardless of whether CI enforces it yet. |
| Technology & Constraints | PASS | Uses only Django + HTMX (both already dependencies); no new JS framework introduced. The constitution's `python-social-auth` requirement covers staff/admin sign-in to Django admin, not player-facing access — this feature's players deliberately have no accounts, per its own spec scope, and does not touch the social-auth wiring. |
| Governance (refactor-first workflow) | N/A | `bingo/` is an empty stub (no legacy behavior to preserve), so no dedicated refactor step is needed before adding models/views. |

No Complexity Tracking entries are required — this design does not add complexity beyond the spec's needs.

## Project Structure

### Documentation (this feature)

```text
specs/002-buzzword-bingo-game/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md         # Phase 1 output (/speckit.plan command)
├── quickstart.md         # Phase 1 output (/speckit.plan command)
├── contracts/            # Phase 1 output (/speckit.plan command)
└── tasks.md              # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── bingo/                         # existing stub app — this feature builds it out
│   ├── __init__.py
│   ├── apps.py                    # existing — no change needed
│   ├── models.py                  # new: Buzzword, Game, GameStatus, Player, Board, BoardSquare
│   ├── domain.py                  # new: pure board-generation + win-detection functions
│   ├── forms.py                   # new: game-name / display-name validation (non-blank, FR-001/003)
│   ├── views.py                   # new: create game, join game, view board, toggle cell
│   ├── urls.py                    # new: the 4 routes, included from config.urls
│   ├── admin.py                   # new: ModelAdmin registrations for all 5 models
│   ├── migrations/
│   │   └── 0001_initial.py        # new: first migration for this app
│   └── templates/bingo/
│       ├── home.html              # create-game form + generated join link
│       ├── join.html               # join form
│       ├── board.html              # 5×5 board + winner banner region
│       └── partials/
│           ├── _square.html        # single-square HTMX swap fragment
│           └── _winner_banner.html # out-of-band winner-announcement fragment
├── config/
│   ├── settings/base.py           # add "bingo" and "django_htmx" to INSTALLED_APPS,
│   │                               # "django_htmx.middleware.HtmxMiddleware" to MIDDLEWARE
│   └── urls.py                    # add include("bingo.urls")
└── tests/
    ├── unit/
    │   └── test_domain.py         # hypothesis property tests for board generation + win detection
    └── integration/
        └── test_bingo_views.py    # pytest-django tests for the 4 routes + admin registrations

docs/
├── deployment.md, development.md  # existing mkdocs pages (unchanged by this feature)
└── sphinx/
    └── gameplay.md                 # new: mirrors player/admin flow docs into the Sphinx source
```

**Structure Decision**: Single Django project layout (`backend/` only — no `frontend/` exists or is needed).
This feature builds out the existing `bingo` app stub in place: models, a pure `domain.py` module, thin views, forms, URLs, admin, templates, and one migration.
`config/settings/base.py` gains two `INSTALLED_APPS`/`MIDDLEWARE` entries (`bingo`, `django_htmx`) and `config/urls.py` gains one `include()`; no other feature's files are touched.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Not applicable — this design introduces no complexity beyond what the spec requires; no violations require justification.
