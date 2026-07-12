---

description: "Task list template for feature implementation"
---

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Tasks: Buzzword Bingo Game](#tasks-buzzword-bingo-game)
  - [Format: `[ID] [P?] [Story] Description`](#format-id-p-story-description)
  - [Path Conventions](#path-conventions)
  - [Phase 1: Setup (Shared Infrastructure)](#phase-1-setup-shared-infrastructure)
  - [Phase 2: Foundational (Blocking Prerequisites)](#phase-2-foundational-blocking-prerequisites)
  - [Phase 3: User Story 1 - Create a game and share it (Priority: P1) 🎯 MVP](#phase-3-user-story-1---create-a-game-and-share-it-priority-p1--mvp)
    - [Tests for User Story 1 (MANDATORY) ⚠️](#tests-for-user-story-1-mandatory-)
    - [Implementation for User Story 1](#implementation-for-user-story-1)
  - [Phase 4: User Story 2 - Join a game and receive a personal board (Priority: P2)](#phase-4-user-story-2---join-a-game-and-receive-a-personal-board-priority-p2)
    - [Tests for User Story 2 (MANDATORY) ⚠️](#tests-for-user-story-2-mandatory-)
    - [Implementation for User Story 2](#implementation-for-user-story-2)
  - [Phase 5: User Story 3 - Play the board and detect a winner (Priority: P3)](#phase-5-user-story-3---play-the-board-and-detect-a-winner-priority-p3)
    - [Tests for User Story 3 (MANDATORY) ⚠️](#tests-for-user-story-3-mandatory-)
    - [Implementation for User Story 3](#implementation-for-user-story-3)
  - [Phase 6: User Story 4 - Manage the buzzword pool (Priority: P4)](#phase-6-user-story-4---manage-the-buzzword-pool-priority-p4)
    - [Tests for User Story 4 (MANDATORY) ⚠️](#tests-for-user-story-4-mandatory-)
    - [Implementation for User Story 4](#implementation-for-user-story-4)
  - [Phase 7: Polish & Cross-Cutting Concerns](#phase-7-polish--cross-cutting-concerns)
  - [Dependencies & Execution Order](#dependencies--execution-order)
    - [Phase Dependencies](#phase-dependencies)
    - [Within Each User Story](#within-each-user-story)
    - [Parallel Opportunities](#parallel-opportunities)
  - [Parallel Example: User Story 2](#parallel-example-user-story-2)
  - [Implementation Strategy](#implementation-strategy)
    - [MVP First (User Story 1 Only)](#mvp-first-user-story-1-only)
    - [Incremental Delivery](#incremental-delivery)
    - [Parallel Team Strategy](#parallel-team-strategy)
  - [Notes](#notes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Tasks: Buzzword Bingo Game

**Input**: Design documents from `/specs/002-buzzword-bingo-game/` **Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are MANDATORY.
TDD is strictly enforced (constitution Principle I).
Tests must be written and fail before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single Django project — all paths are under `backend/` (no separate `frontend/` exists or is needed; see [plan.md](./plan.md) Structure Decision).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Wire the existing `bingo` app stub and `django-htmx` dependency into the project so the app is reachable at all.

- [X] T001 Add `"bingo"` and `"django_htmx"` to `INSTALLED_APPS`, and `"django_htmx.middleware.HtmxMiddleware"` to `MIDDLEWARE`, in `backend/config/settings/base.py` (research.md D7)
- [X] T002 [P] Create `backend/bingo/urls.py` with `app_name = "bingo"` and an initially-empty `urlpatterns` list, ready for each story to append its own route
- [X] T003 Add `path("", include("bingo.urls"))` to `urlpatterns` in `backend/config/urls.py` (depends on T002)

**Checkpoint**: App is installed and routable; no gameplay behavior yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schema and routing scaffold that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create `GameStatus` (`TextChoices`: `ACTIVE`, `FINISHED`) and the `Buzzword`, `Game`, `Player`, `Board`, `BoardSquare` models in `backend/bingo/models.py` per data-model.md Entities 1-5 (UUID primary keys, `Buzzword.text` unique, `BoardSquare` position validators 0-24, `unique_together=("board","position")`, `Game.winner` FK to `Player` with `on_delete=SET_NULL`)
- [X] T005 Generate the initial migration for the models in T004 by running `manage.py makemigrations bingo` (never hand-write the migration file in `backend/bingo/migrations/0001_initial.py`)

**Checkpoint**: Schema exists and migrates cleanly; app has a URLconf ready for routes.
User story implementation can now begin.

---

## Phase 3: User Story 1 - Create a game and share it (Priority: P1) 🎯 MVP

**Goal**: A visitor can create a game from the homepage and receive a shareable join link.

**Independent Test**: Submit a game name on `/` and confirm a `Game(status=active)` is created and its join link is shown; submitting a blank name creates nothing and shows a validation error.

### Tests for User Story 1 (MANDATORY) ⚠️

> Write these tests FIRST; confirm they FAIL before implementing T008-T011.

- [X] T006 [P] [US1] Integration test: `POST /` with a valid name creates an active `Game` and the response shows its join URL `/game/<id>/join/`, in `backend/tests/integration/test_bingo_views.py`
- [X] T007 [P] [US1] Integration test: `POST /` with a blank/whitespace-only name re-renders the form with a validation error and creates no `Game`, in `backend/tests/integration/test_bingo_views.py`

### Implementation for User Story 1

- [X] T008 [US1] Create `GameNameForm` (non-blank validation, FR-001) in `backend/bingo/forms.py`
- [X] T009 [US1] Implement the create-game view (`GET` renders the form; `POST` validates via `GameNameForm` and creates the `Game`, or re-renders with errors) in `backend/bingo/views.py`
- [X] T010 [US1] Add `path("", views.create_game, name="create_game")` to `backend/bingo/urls.py`
- [X] T011 [US1] Create `backend/bingo/templates/bingo/home.html` (create-game form; on success, shows the shareable join link)

**Checkpoint**: User Story 1 is fully functional and testable independently — a game can be created and shared.

---

## Phase 4: User Story 2 - Join a game and receive a personal board (Priority: P2)

**Goal**: A participant can join an active game by name and receive their own randomly generated 5×5 board.

**Independent Test**: Open a join link for an active game, submit a display name, and confirm a new `Player`, `Board`, and 25 `BoardSquare`s are created and the participant is redirected to their board; joining a finished game, joining with a blank name, or joining when fewer than 25 active buzzwords exist must each be rejected without creating any of those records.

### Tests for User Story 2 (MANDATORY) ⚠️

> Write these tests FIRST; confirm they FAIL before implementing T018-T022.

- [X] T012 [P] [US2] Integration test: joining an active game creates a `Player`, a `Board`, and 25 `BoardSquare`s (center marked and buzzword-free) and redirects to `/board/<id>/`, in `backend/tests/integration/test_bingo_views.py` (FR-006/FR-007)
- [X] T012a [P] [US2] Integration test: `GET /game/<uuid:game_id>/join/` with a nonexistent or malformed `game_id` returns 404, in `backend/tests/integration/test_bingo_views.py` (FR-013)
- [X] T013 [P] [US2] Integration test: two participants joining with the same display name each get their own independent `Player`/`Board`, in `backend/tests/integration/test_bingo_views.py` (FR-004)
- [X] T014 [P] [US2] Integration test: joining a finished game creates no `Player`/`Board`/`BoardSquare` and shows a "no longer accepting participants" message, in `backend/tests/integration/test_bingo_views.py` (FR-005)
- [X] T015 [P] [US2] Integration test: joining with a blank/whitespace-only display name re-renders the form with a validation error and creates nothing, in `backend/tests/integration/test_bingo_views.py` (FR-003)
- [X] T016 [P] [US2] Integration test: joining when fewer than 25 active `Buzzword`s exist is declined with an explanatory message and creates nothing, in `backend/tests/integration/test_bingo_views.py` (FR-016)
- [X] T017 [P] [US2] Property test: `select_random_words` always returns `k` distinct items drawn only from the given pool, and raises `InsufficientBuzzwordPoolError` when `len(pool) < k`, in `backend/tests/unit/test_domain.py` (research.md D3)

### Implementation for User Story 2

- [X] T018 [US2] Implement `select_random_words(pool, k, rng)` and `InsufficientBuzzwordPoolError` in `backend/bingo/domain.py` (research.md D3)
- [X] T019 [US2] Create `DisplayNameForm` (non-blank validation, FR-003) in `backend/bingo/forms.py`
- [X] T020 [US2] Implement the join-game view — `GET` renders the join form or the "finished"/"insufficient buzzwords" states; `POST` validates the name, calls `select_random_words` against active `Buzzword`s, and atomically creates the `Player`, `Board`, and 25 `BoardSquare`s (position 12 unmarked-buzzword-free and pre-marked) — in `backend/bingo/views.py` (depends on T004, T018, T019)
- [X] T021 [US2] Add `path("game/<uuid:game_id>/join/", views.join_game, name="join_game")` to `backend/bingo/urls.py`
- [X] T022 [US2] Create `backend/bingo/templates/bingo/join.html` (join form, "game finished" state, "insufficient buzzwords" state)

**Checkpoint**: User Stories 1 AND 2 both work independently — games can be created, shared, and joined with personal boards.

---

## Phase 5: User Story 3 - Play the board and detect a winner (Priority: P3)

**Goal**: A player can mark/unmark their squares via HTMX, and the system automatically detects and announces a winning line.

**Independent Test**: On a player's board, mark squares to complete a row/column/diagonal and confirm the game finishes and a winner banner is returned in the same response with no full page reload; confirm finished games and cross-board access reject further toggles.

### Tests for User Story 3 (MANDATORY) ⚠️

> Write these tests FIRST; confirm they FAIL before implementing T030-T035.

- [X] T023 [P] [US3] Property tests for `has_bingo`: any fully marked row/column/diagonal returns `True`; marked sets that complete no full line return `False`, in `backend/tests/unit/test_domain.py` (research.md D4)
- [X] T024 [P] [US3] Integration test: toggling a non-winning square updates its `marked` state and the response contains only the updated square fragment, in `backend/tests/integration/test_bingo_views.py` (FR-008/FR-009)
- [X] T025 [P] [US3] Integration test: the toggle that completes a line finishes the `Game`, records the `winner`, and the response includes both the square fragment and the out-of-band winner-banner fragment, in `backend/tests/integration/test_bingo_views.py` (FR-010)
- [X] T026 [P] [US3] Integration test: toggling any square (by the winner or any other player) after the game has finished is rejected with no state change, in `backend/tests/integration/test_bingo_views.py` (FR-011)
- [X] T027 [P] [US3] Integration test: toggling with a nonexistent or malformed `board_id`/`cell_id`, or a `cell_id` that doesn't belong to that `board_id`, returns 404, in `backend/tests/integration/test_bingo_views.py` (FR-013)
- [X] T027a [P] [US3] Integration test: `GET /board/<uuid:board_id>/` with a nonexistent or malformed `board_id` returns 404, in `backend/tests/integration/test_bingo_views.py` (FR-013)
- [X] T028 [P] [US3] Integration test: toggling the center free square (position 12) is a no-op and remains marked, in `backend/tests/integration/test_bingo_views.py` (research.md D5)
- [X] T029 [P] [US3] Integration test: simulating two near-simultaneous winning toggles on two different boards in the same game — only the first is recorded as `Game.winner`; the second's conditional update affects zero rows, in `backend/tests/integration/test_bingo_views.py` (research.md D6)

### Implementation for User Story 3

- [X] T030 [US3] Implement `WINNING_LINES` and `has_bingo(marked)` in `backend/bingo/domain.py` (research.md D4)
- [X] T031 [US3] Implement the board view (renders the 5×5 grid and an empty/populated winner-banner region) in `backend/bingo/views.py`
- [X] T032 [US3] Implement the toggle-cell view — 404 on missing/mismatched IDs, no-op on the center square, rejection when the game is already finished, otherwise toggles `marked`, runs `has_bingo`, and on a win performs the atomic conditional `Game.objects.filter(pk=game_id, status=ACTIVE).update(status=FINISHED, winner=player)` win-race guard (research.md D6) — in `backend/bingo/views.py` (depends on T004, T030)
- [X] T033 [US3] Add `path("board/<uuid:board_id>/", views.view_board, name="view_board")` and `path("board/<uuid:board_id>/cell/<uuid:cell_id>/toggle/", views.toggle_cell, name="toggle_cell")` to `backend/bingo/urls.py`
- [X] T034 [US3] Create `backend/bingo/templates/bingo/board.html` (5×5 grid referencing the square partial, plus the winner-banner region)
- [X] T035 [US3] Create `backend/bingo/templates/bingo/partials/_square.html` and `backend/bingo/templates/bingo/partials/_winner_banner.html` (the latter rendered with `hx-swap-oob="true"` on a win, per research.md D7)

**Checkpoint**: All three player-facing user stories (US1-US3) are independently functional — the full create → join → play → win loop works end-to-end.

---

## Phase 6: User Story 4 - Manage the buzzword pool (Priority: P4)

**Goal**: An administrator can add, edit, and deactivate buzzwords, and inspect games/players, through Django admin.

**Independent Test**: Add, edit, and deactivate `Buzzword`s through `/admin/` and confirm only active ones appear on boards generated afterward; confirm finished games and their winners are visible in the `Game`/`Player` admin views.

### Tests for User Story 4 (MANDATORY) ⚠️

> Write these tests FIRST; confirm they FAIL before implementing T038-T039.

- [X] T036 [P] [US4] Integration test: an added `Buzzword` becomes eligible for new boards, and a deactivated `Buzzword` is excluded from boards generated afterward (while unaffected on boards generated before deactivation), in `backend/tests/integration/test_bingo_views.py` (FR-014)
- [X] T037 [P] [US4] Integration test: the `Game` and `Player` admin changelists/detail views expose `status`, `winner`, and `game`/`joined_at` for a finished game, in `backend/tests/integration/test_bingo_views.py` (FR-015)

### Implementation for User Story 4

- [X] T038 [US4] Register `BuzzwordAdmin` in `backend/bingo/admin.py` — list display (`text`, `active`, `created_at`), search on `text`, filter on `active`, bulk activate/deactivate actions (contracts/admin-interface.md)
- [X] T039 [P] [US4] Register `GameAdmin`, `PlayerAdmin`, and `BoardAdmin` (with `BoardSquare` as a read-only inline) in `backend/bingo/admin.py` (contracts/admin-interface.md)

**Checkpoint**: All four user stories are independently functional — the buzzword pool is fully manageable through Django admin.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Repo-wide quality gates and documentation that span multiple stories.

- [X] T040 [P] Run `pyrefly check` and `ty check` against `backend/bingo/` and resolve any strict-typing findings (constitution Principle V)
- [X] T041 [P] Add `docs/sphinx/gameplay.md` mirroring the player/admin flow documentation, and add it to the `toctree` in `docs/sphinx/index.md` (constitution Principle III, per plan.md's Documentation First mitigation)
- [X] T042 Execute quickstart.md Scenarios A-E end-to-end against a local dev environment and confirm each's expected outcome
- [X] T043 [P] Review all new public functions/classes in `backend/bingo/` for docstrings explaining "why"/"when" per constitution Principle III
- [X] T044 [P] Add a lightweight load/latency test asserting the toggle-cell endpoint (`POST /board/<id>/cell/<id>/toggle/`) completes in under 500ms under concurrent simulated requests, in `backend/tests/integration/test_bingo_performance.py` (SC-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational only
- **User Story 2 (Phase 4)**: Depends on Foundational only (independently testable, though it naturally follows US1 in a real playthrough since it needs a `Game` to join)
- **User Story 3 (Phase 5)**: Depends on Foundational only (independently testable with a `Board` set up directly via ORM in tests, though it naturally follows US2 in a real playthrough)
- **User Story 4 (Phase 6)**: Depends on Foundational only — fully independent of US1-US3
- **Polish (Phase 7)**: Depends on all four user stories being complete

### Within Each User Story

- Tests are written first and must fail before implementation (constitution Principle I)
- Domain functions before views that call them
- Forms before the views that use them
- Views before the URL routes that expose them
- Routes before templates that link to them

### Parallel Opportunities

- T001/T002 (Setup) touch different files and can run in parallel; T003 depends on T002 (needs `bingo/urls.py` to exist before it can be included)
- All `[P]`-marked tests within a story's test block can run in parallel (different test functions; same file is fine to parallelize authorship of, but coordinate merges)
- T038 and T039 (US4 admin registrations) can run in parallel — different `ModelAdmin` classes in the same file, but no shared state
- Once Foundational (Phase 2) is complete, US1, US2, US3, and US4 can all proceed in parallel if staffed — each is independently testable per its Independent Test statement, even though a manual end-to-end playthrough naturally exercises them in US1→US2→US3 order

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: "Integration test: join creates Player/Board/25 BoardSquares in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: duplicate display names get independent players/boards in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: joining a finished game is rejected in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: blank display name is rejected in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: insufficient buzzword pool is rejected in backend/tests/integration/test_bingo_views.py"
Task: "Property test: select_random_words in backend/tests/unit/test_domain.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm a game can be created and its join link shown
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → demo (MVP: a game can be created and shared)
3. Add User Story 2 → validate independently → demo (participants can join and get boards)
4. Add User Story 3 → validate independently → demo (full play-to-win loop)
5. Add User Story 4 → validate independently → demo (buzzword pool is admin-manageable)
6. Polish (Phase 7)

### Parallel Team Strategy

With multiple developers, once Foundational is done: Developer A takes US1, Developer B takes US2 (using ORM-created `Buzzword` fixtures rather than waiting on US1's UI), Developer C takes US3 (using ORM-created `Board`/`BoardSquare` fixtures), Developer D takes US4 (fully independent of the others).
All four integrate at the Polish phase.

---

## Notes

- `[P]` tasks = different files or independent concerns, no dependencies
- `[Story]` label maps task to specific user story for traceability
- Every user story's tests must fail before its implementation tasks begin (TDD, constitution Principle I)
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- Avoid: vague tasks, same-file conflicts within a single `[P]` batch, cross-story dependencies that break independence
