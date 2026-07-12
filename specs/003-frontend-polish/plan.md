<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Implementation Plan: Frontend Polish & Mobile-First UX](#implementation-plan-frontend-polish--mobile-first-ux)
  - [Summary](#summary)
  - [Technical Context](#technical-context)
  - [Constitution Check](#constitution-check)
  - [Project Structure](#project-structure)
    - [Documentation (this feature)](#documentation-this-feature)
    - [Source Code (repository root)](#source-code-repository-root)
  - [Complexity Tracking](#complexity-tracking)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Implementation Plan: Frontend Polish & Mobile-First UX

**Branch**: `003-frontend-polish` | **Date**: 2026-07-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-frontend-polish/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command.
See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Polish the existing create/share/join/board screens built in `002-buzzword-bingo-game` to match the supplied UX specification — mobile-first, zero-training, fast-and-fun — without introducing any new gameplay rules, models, migrations, or routes.
The work is presentation-layer: restyle the four existing templates and two partials (CSS: responsive 5×5 square-cell grid, rounded corners/soft shadows/spacing, marked/unmarked/free-space cell states, winner overlay, finished-game and empty-state messaging), add HTMX loading/disable/transition attributes for instant tap feedback (FR-010) and smooth mark/unmark animation (FR-008), and add exactly one small, fully typed TypeScript module for the one interaction the platform cannot do declaratively — the "Copy Link" clipboard action (FR-003) — per the constitution's allowance for custom frontend code ("must be written with TypeScript and have 100% test coverage").
A new `frontend/` Node project hosts that TypeScript module, its fast-check property tests, and a Playwright end-to-end suite that drives a live Django server through the four prioritized user journeys (FR-020/SC-007), satisfying the constitution's "Frontend uses playwright with fast-check" testing principle.

## Technical Context

**Language/Version**: Python 3.14 (existing, unchanged) for the Django side; TypeScript (strict mode) for one new client-side module; Node.js LTS as the dev-time runtime for the frontend tooling (not part of the deployed Django runtime).
**Primary Dependencies**: No new Python dependencies — reuses Django ≥6.0.7, `django-htmx`, and the existing `bingo` app.
New `frontend/` Node project depends on `@playwright/test` and `fast-check` (constitution Principle I).
**Storage**: PostgreSQL, unchanged — no new models, fields, or migrations (spec Assumptions: no new domain entities).
**Testing**: Existing pytest + `pytest-django` + `hypothesis` suite, unchanged in scope (already covers the routes/domain logic being restyled here) + new `@playwright/test` end-to-end specs (browser-driven, run against a live Django server) covering the four user stories and named edge/empty states + new `@playwright/test`-run unit/property tests (using `fast-check`) for the TypeScript copy-link module, written before that module's implementation.
**Target Platform**: Same Linux/ASGI server as 002; browsers are evergreen mobile Chrome/Safari and desktop Chrome/Firefox/Safari — Playwright's project matrix covers at minimum one mobile viewport (≤430px) and one desktop viewport (SC-004).
**Project Type**: Web application.
Existing single Django project (`backend/`) gains no new apps; a new, narrowly scoped `frontend/` Node project is added solely to host the one TypeScript module and the Playwright test suite — this is not a SPA and introduces no page-rendering JS framework, per the constitution's "do not introduce any other JavaScript frameworks or libraries" constraint.
**Performance Goals**: SC-002 — visible tap feedback in under 100ms, achieved via an HTMX-driven loading class/attribute applied synchronously on click (independent of network latency); inherits 002's existing <500ms server-round-trip budget for the toggle endpoint (unchanged).
**Constraints**: No new JavaScript framework/library (constitution); the one custom script MUST be TypeScript with 100% test coverage (constitution); no live/real-time push to other players — they learn a game finished on their own next server interaction (spec Assumption); accessibility target WCAG 2.1 AA (spec Assumption); zero new Django models/migrations/routes (spec Assumptions).
**Scale/Scope**: 4 existing templates + 2 partials restyled (no new templates), 1 new CSS stylesheet, 1 new TypeScript module (~1 exported function) plus its unit tests, 1 new `frontend/` Node project (package.json, tsconfig.json, playwright.config.ts, `e2e/` specs, `src/` + `tests/` for the TS module), and at most small, additive `bingo/views.py` context changes to expose already-existing model state (e.g., whether the current board belongs to the game's winner) to templates — no new Django app, model, migration, or URL.

## Constitution Check

*GATE: Must pass before Phase 0 research.*
*Re-check after Phase 1 design.*

| Principle | Verdict | Rationale |
|---|---|---|
| I. Strict Test-Driven Development | PASS | Existing pytest/hypothesis coverage for `domain.py` and the 4 routes is untouched by this presentation-only feature. The new TypeScript copy-link module gets `fast-check` property tests written before its implementation; the new Playwright e2e specs are written to encode this spec's Acceptance Scenarios and are expected to fail against the current unstyled templates before the polish work lands (red before green). |
| II. Separation of Concerns & Modularity | PASS | This feature touches templates, CSS, HTMX attributes, and one isolated TS module only; `bingo/domain.py`'s pure win-detection/board-generation functions are untouched. Any `views.py` context additions stay limited to exposing state the models already carry (e.g., `game.winner_id == board.player_id`) — no new business logic moves into views or templates. |
| III. Documentation First | PASS (mitigated, same approach as 001/002) | This feature's UX/testing setup is mirrored into `docs/sphinx/` alongside the existing mkdocs pages, following the same mitigation 001 and 002 used for the repo-wide mkdocs-vs-Sphinx gap. |
| IV. Functional Programming Patterns | PASS | The one custom TS module is a pure-ish function over its input (a link string in, a clipboard side-effect and success/failure result out) with no client-side class or state machine — straightforward to property-test with `fast-check`. |
| V. Strong Typing & Safe Types | PASS | Python side is unchanged (already enforced by strict `pyrefly`/`ty`). The new TS module is written under `"strict": true`, with no `any` and no untyped exports, extending the constitution's "illegal states unrepresentable" intent to the one piece of new frontend code. |
| Technology & Constraints | PASS | Server-rendered Django + HTMX remain the only page-rendering technology; the sole new client-side code is the one TypeScript module the constitution explicitly permits for cases HTMX/CSS alone can't cover (clipboard access). No other JS framework or library is introduced. The `python-social-auth` requirement is unaffected — it governs staff/admin login, not this player-facing feature. |
| Governance (refactor-first workflow) | N/A | This feature restyles existing templates and adds new, isolated frontend tooling; there is no legacy behavior in this area that needs a dedicated refactor step first. |

No Complexity Tracking entries are required — this design does not add complexity beyond the spec's needs.

## Project Structure

### Documentation (this feature)

```text
specs/003-frontend-polish/
├── plan.md               # This file (/speckit.plan command output)
├── research.md           # Phase 0 output (/speckit.plan command)
├── data-model.md         # Phase 1 output (/speckit.plan command)
├── quickstart.md         # Phase 1 output (/speckit.plan command)
├── contracts/            # Phase 1 output (/speckit.plan command)
│   └── ui-contract.md    # Stable selectors/roles shared by templates and Playwright specs
└── tasks.md              # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── bingo/
│   ├── views.py                    # small, additive context changes only (e.g., is_winner flag)
│   ├── static/bingo/
│   │   └── css/
│   │       └── bingo.css           # new: board/cell/overlay/typography styling (FR-006–FR-009, FR-019)
│   └── templates/bingo/
│       ├── base.html               # new: <link> to bingo.css, viewport meta, HTMX loading config
│       ├── home.html               # restyled: autofocus, inline errors, share-link confirmation UI
│       ├── join.html               # restyled: autofocus, inline errors, finished/empty-pool messaging
│       ├── board.html               # restyled: game/player header, win-condition reminder, finished
│       │                            # banner for all participants, winner overlay markup
│       └── partials/
│           ├── _square.html         # + hx-indicator / hx-disabled-elt / hx-swap transition (FR-008, FR-010)
│           └── _winner_banner.html   # restyled: celebratory overlay markup (FR-015)
└── tests/
    ├── unit/test_domain.py          # unchanged
    └── integration/test_bingo_views.py  # extended: assert new template context flags render correctly

frontend/                            # new: Node project, dev-time only, not part of the Django runtime
├── package.json                     # @playwright/test, fast-check, typescript
├── tsconfig.json                    # "strict": true
├── playwright.config.ts             # webServer: starts the Django dev server; mobile + desktop projects
├── src/
│   └── copy-link.ts                 # the one custom TS module (FR-003)
├── tests/
│   └── unit/copy-link.spec.ts       # fast-check property tests for copy-link.ts, written first
└── e2e/
    ├── create-and-share.spec.ts     # User Story 1
    ├── join.spec.ts                 # User Story 2
    ├── play-and-win.spec.ts         # User Story 3 (incl. double-tap, overlay dismissal)
    └── dead-ends.spec.ts            # User Story 4 (finished/empty/not-found states)

docs/
└── sphinx/
    └── frontend-ux.md               # new: mirrors the polished UX/testing setup into the Sphinx source
```

**Structure Decision**: Web application layout, extending 002's single Django project (`backend/`) with a new, narrowly scoped `frontend/` Node project for tooling only (the one TS module + its tests + the Playwright e2e suite) — not a second page-rendering frontend.
`backend/bingo/static/bingo/css/bingo.css` is new; the compiled output of `frontend/src/copy-link.ts` is served to the browser via Django's `STATICFILES_DIRS` pointing at the TypeScript compiler's output directory (decision detail in `research.md`), so the script is authored once in `frontend/` and served once by Django — no duplicated/checked-in build artifacts.
No other feature's files are touched; no new Django app, model, migration, or URL is introduced.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Not applicable — this design introduces no complexity beyond what the spec requires; no violations require justification.
