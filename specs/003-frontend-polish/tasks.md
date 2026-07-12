<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Tasks: Frontend Polish & Mobile-First UX](#tasks-frontend-polish--mobile-first-ux)
  - [Format: `[ID] [P?] [Story] Description`](#format-id-p-story-description)
  - [Path Conventions](#path-conventions)
  - [Phase 1: Setup (Shared Infrastructure)](#phase-1-setup-shared-infrastructure)
  - [Phase 2: Foundational (Blocking Prerequisites)](#phase-2-foundational-blocking-prerequisites)
  - [Phase 3: User Story 1 - Create a game and share it in seconds (Priority: P1) 🎯 MVP](#phase-3-user-story-1---create-a-game-and-share-it-in-seconds-priority-p1--mvp)
    - [Tests for User Story 1 (MANDATORY) ⚠️](#tests-for-user-story-1-mandatory-)
    - [Implementation for User Story 1](#implementation-for-user-story-1)
  - [Phase 4: User Story 2 - Join with almost no friction (Priority: P2)](#phase-4-user-story-2---join-with-almost-no-friction-priority-p2)
    - [Tests for User Story 2 (MANDATORY) ⚠️](#tests-for-user-story-2-mandatory-)
    - [Implementation for User Story 2](#implementation-for-user-story-2)
  - [Phase 5: User Story 3 - Play the board and feel the win (Priority: P3)](#phase-5-user-story-3---play-the-board-and-feel-the-win-priority-p3)
    - [Tests for User Story 3 (MANDATORY) ⚠️](#tests-for-user-story-3-mandatory-)
    - [Implementation for User Story 3](#implementation-for-user-story-3)
  - [Phase 6: User Story 4 - Never hit a dead end (Priority: P4)](#phase-6-user-story-4---never-hit-a-dead-end-priority-p4)
    - [Tests for User Story 4 (MANDATORY) ⚠️](#tests-for-user-story-4-mandatory-)
    - [Implementation for User Story 4](#implementation-for-user-story-4)
  - [Phase 7: Polish & Cross-Cutting Concerns](#phase-7-polish--cross-cutting-concerns)
  - [Dependencies & Execution Order](#dependencies--execution-order)
    - [Phase Dependencies](#phase-dependencies)
    - [Within Each User Story](#within-each-user-story)
    - [Parallel Opportunities](#parallel-opportunities)
  - [Parallel Example: User Story 3](#parallel-example-user-story-3)
  - [Implementation Strategy](#implementation-strategy)
    - [MVP First (User Story 1 Only)](#mvp-first-user-story-1-only)
    - [Incremental Delivery](#incremental-delivery)
    - [Parallel Team Strategy](#parallel-team-strategy)
  - [Notes](#notes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Tasks: Frontend Polish & Mobile-First UX

**Input**: Design documents from `/specs/003-frontend-polish/` **Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-contract.md, quickstart.md

**Tests**: Tests are MANDATORY.
TDD is strictly enforced (constitution Principle I; also explicitly required by this feature's FR-020/SC-007).
Every e2e spec and unit/property test below must be written first and observed to fail against the current unstyled templates / nonexistent module before its implementation task.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Existing single Django project at `backend/` (unchanged from 002) plus a new, narrowly scoped Node project at `frontend/` (Playwright specs + the one TypeScript module — see [plan.md](./plan.md) Structure Decision).
No other feature's files are touched.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Stand up the new `frontend/` Node project and wire its build output into Django's static files, so every later story has somewhere to add specs/styles.

- [ ] T001 Create `frontend/package.json` (name `bsbingo-frontend`, private, devDependencies `@playwright/test`, `fast-check`, `typescript`, `c8`) with npm scripts `"test:unit": "c8 --all --src src --100 playwright test tests/unit"`, `"e2e": "playwright test e2e"`, and `"build": "tsc"`
- [ ] T001a [P] Configure `c8`'s coverage config (`.c8rc.json` or a `"c8"` key in `frontend/package.json`) to instrument `frontend/src/**` and fail the run below 100% line/branch/function coverage, satisfying the constitution's "100% test coverage required for custom TypeScript" (Principle I) — `npm run test:unit` (T001) must exit non-zero on any shortfall
- [ ] T002 [P] Create `frontend/tsconfig.json` (`"strict": true`, `"target": "ES2022"`, `"module": "ES2022"`, `"outDir": "dist"`, `"rootDir": "src"`)
- [ ] T003 [P] Create `frontend/playwright.config.ts`: a `mobile` project (viewport ≤430px, e.g. Playwright's `Pixel 7` device) and a `desktop` project (Chromium, viewport ≥700px), a `webServer` entry that runs `uv run backend/manage.py runserver` with env `DJANGO_SETTINGS_MODULE=config.settings.test` **and `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`** (required because `config.settings.test` sets `DEBUG=False`, so Django's dev-only localhost allowance does not apply and `ALLOWED_HOSTS` — empty by default in `base.py` — must be set explicitly or every request gets rejected with `DisallowedHost`), and a matching `baseURL` (research.md decision)
- [ ] T004 [P] Add `frontend/node_modules/`, `frontend/dist/`, and `frontend/test-results/` to `.gitignore`
- [ ] T005 Run `npm install` inside `frontend/` to generate `frontend/package-lock.json`
- [ ] T006 [P] Add an entry for `frontend/dist` to `STATICFILES_DIRS` in `backend/config/settings/base.py` (research.md decision — serves the compiled `copy-link.js` via `{% static %}` without checking in a build artifact)
- [ ] T007 [P] Add a `<meta name="viewport" content="width=device-width, initial-scale=1">` tag and a `<link rel="stylesheet" href="{% static 'bingo/css/bingo.css' %}">` to `backend/bingo/templates/bingo/base.html`, and create the (initially empty) `backend/bingo/static/bingo/css/bingo.css`

**Checkpoint**: `frontend/` project scaffolded and installable; Django is wired to serve its future CSS/JS output.
No behavior has changed yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared styling, domain logic, and test infrastructure every user story phase below depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T008 [P] Add shared visual-language base styles to `backend/bingo/static/bingo/css/bingo.css`: a minimal CSS reset, typography scale, spacing scale, rounded-corner/soft-shadow tokens (custom properties), and a visible `:focus-visible` outline style used on every screen (FR-011, FR-013, FR-019)
- [ ] T009 [P] Write a hypothesis property test for a new `winning_lines(marked: frozenset[int]) -> frozenset[int]` domain function in `backend/tests/unit/test_domain.py` (asserts the returned set is exactly the union of every fully marked line, and is empty when no line is complete) — must fail (function doesn't exist yet)
- [ ] T010 Implement `winning_lines(marked: frozenset[int]) -> frozenset[int]` in `backend/bingo/domain.py`, alongside the existing `has_bingo`/`WINNING_LINES` (depends on T009)
- [ ] T011 Extend `_BoardContext`/`_SquareContext` in `backend/bingo/views.py` with an `is_winner: bool` / `winning_positions: frozenset[int]` computation (via `winning_lines()`, only meaningful when `game.status == GameStatus.FINISHED`), threaded through `view_board` and `toggle_cell` so both the initial render and the winning-toggle response can mark which squares are part of the completed line (depends on T010)
- [ ] T012 [P] Create a shared Playwright helper `frontend/e2e/support/game-flow.ts` exporting `createGame(page, name): Promise<{ joinUrl: string }>` and `joinGame(page, joinUrl, playerName): Promise<void>`, driven entirely through the UI (no direct DB access) — used by every e2e spec below

**Checkpoint**: Shared styling tokens, the winning-line domain function, view context, and e2e test helper all exist.
User story implementation can now begin.

---

## Phase 3: User Story 1 - Create a game and share it in seconds (Priority: P1) 🎯 MVP

**Goal**: An organizer can create a game on their phone and get back a shareable link with a one-tap copy action, with no dead time or confusion.

**Independent Test**: Open the home page on a mobile viewport, type a game name, submit, and confirm a shareable link appears with a working "Copy Link" action — independent of join/board polish.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Write `frontend/e2e/create-and-share.spec.ts` (both `mobile` and `desktop` projects) covering Acceptance Scenarios 1-4: autofocus on load, Enter-key submission, inline validation error on a blank/whitespace name, and the post-creation share screen (`data-testid="share-link"`, working `data-testid="copy-link-button"`, `data-testid="create-another-game"`) per contracts/ui-contract.md; include one keyboard-only scenario (Tab to the name field, type, submit with Enter — no `.click()` calls) per FR-011 — must fail against the current `home.html`
- [ ] T014 [P] [US1] Write `frontend/tests/unit/copy-link.spec.ts`: fast-check property tests asserting that, for any arbitrary non-empty string passed in, the module calls a (mocked) `navigator.clipboard.writeText` with exactly that string and resolves to a success result — must fail (module doesn't exist yet)

### Implementation for User Story 1

- [ ] T015 [US1] Implement `frontend/src/copy-link.ts`: a small typed function that reads the share link from a `data-share-link` attribute, calls `navigator.clipboard.writeText`, shows a success state on the triggering button, and falls back to leaving the link text selectable if the Clipboard API is unavailable (spec Assumptions) — depends on T014
- [ ] T016 [US1] Restyle `backend/bingo/templates/bingo/home.html` per contracts/ui-contract.md: `autofocus` + `data-testid="game-name-input"` on the name field, `data-testid="create-game-submit"` on the button, an inline `role="alert"` error region next to the field, and — when a game was just created — a share block with `data-testid="share-link"`, a `data-testid="copy-link-button"` wired to `{% static 'bingo/dist/copy-link.js' %}` (via a `type="module"` `<script>` include in `base.html` or a page-specific block), and `data-testid="create-another-game"` linking back to a blank form
- [ ] T017 [P] [US1] Add create-game/share-screen styles to `bingo.css`: form layout, ≥44×44px touch targets (FR-012), share-link/copy-button presentation (builds on T008's shared tokens)
- [ ] T018 [US1] Extend `backend/tests/integration/test_bingo_views.py`'s `create_game` tests to assert the new `data-testid` anchors and inline-error markup render correctly (Django-level regression alongside the e2e check)

**Checkpoint**: User Story 1 is fully functional and independently testable — `npm run e2e -- create-and-share` passes on both projects.

---

## Phase 4: User Story 2 - Join with almost no friction (Priority: P2)

**Goal**: A participant can go from tapping a join link to typing their name to landing on their own board with minimal friction.

**Independent Test**: Open a valid join link on a mobile viewport, enter a name, and confirm the player lands on their own board within a few seconds — independent of how the board itself looks.

### Tests for User Story 2 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T019 [P] [US2] Write `frontend/e2e/join.spec.ts` (both projects), using `createGame` from `game-flow.ts`, covering Acceptance Scenarios 1-3: game name visible + autofocus on load, Enter-key submission, inline validation error on a blank/whitespace name without losing the game-name context on screen, one keyboard-only scenario (Tab to the name field, submit with Enter) per FR-011, and an SC-001 timing assertion (wall-clock from opening the join link through successfully marking the player's first non-free square is under 10 seconds) — must fail against the current `join.html`

### Implementation for User Story 2

- [ ] T020 [US2] Restyle `backend/bingo/templates/bingo/join.html` per contracts/ui-contract.md: `autofocus` + `data-testid="player-name-input"`, `data-testid="join-game-submit"`, and an inline `role="alert"` error region that keeps the game name heading visible above it
- [ ] T021 [P] [US2] Add join-screen styles to `bingo.css` (reuses T008's shared tokens; adds join-form-specific layout, with the name input and submit button sized to ≥44×44px touch targets — FR-012)
- [ ] T022 [US2] Extend `backend/tests/integration/test_bingo_views.py`'s `join_game` tests to assert the new markup anchors

**Checkpoint**: User Stories 1 AND 2 both independently functional.

---

## Phase 5: User Story 3 - Play the board and feel the win (Priority: P3)

**Goal**: Marking a square feels instant, and completing a line triggers an unmistakable, celebratory win moment with the winning line highlighted.

**Independent Test**: Open an existing board, tap several cells and confirm instant visual feedback, then complete a winning line and confirm the celebratory overlay, the highlighted line, and (after dismissing) a read-only board underneath.

### Tests for User Story 3 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US3] Write `frontend/e2e/play-and-win.spec.ts` (both projects), using `createGame`/`joinGame` from `game-flow.ts`, covering Acceptance Scenarios 1-5: tap → pending → marked transition, unmark, free-space cell never responds to taps, a rapid double-tap on the same cell only fires one toggle, and completing a line shows the overlay + highlighted line, then dismissing it reveals a read-only board with the line still highlighted; include an SC-002 timing assertion (the cell's pending indicator/disabled state is applied synchronously on click, asserted before awaiting the HTMX response, budgeted under 100ms) and one keyboard-only scenario (Tab to a cell and activate it with Enter/Space) per FR-011 — must fail against the current unstyled `board.html`

### Implementation for User Story 3

- [ ] T024 [US3] Restyle `backend/bingo/templates/bingo/board.html`: header block with `data-testid="game-name"`, `data-testid="player-name"`, and the win-condition reminder text (FR-005); `role="grid"` on the board container; wrap the whole board with `data-testid="board-readonly"` and (for non-winners) a finished-game notice naming the winner, both driven by the `is_winner`/`winning_positions` context from T011
- [ ] T025 [US3] Update `backend/bingo/templates/bingo/partials/_square.html`: `role="gridcell"` + `data-testid="cell-{{ square.position }}"` on every cell; `hx-indicator` and `hx-disabled-elt="this"` for instant pending feedback and double-tap prevention (FR-010); `hx-swap="outerHTML transition:true"` for the mark/unmark animation (FR-008); omit `hx-post`/button semantics entirely for the center free-space cell, rendering it instead as a non-interactive element with `data-testid="free-space"` (FR-009); add `data-testid="winning-line"` when the square's position is in `winning_positions`
- [ ] T026 [US3] Restyle `backend/bingo/templates/bingo/partials/_winner_banner.html` into the celebratory overlay: `data-testid="winner-overlay"` container shown only when the viewer is the winner, and a `data-testid="celebrate-dismiss"` control that closes the overlay via pure CSS/HTML (e.g. a checkbox- or `<details>`-driven toggle — no custom JS needed) to reveal the board underneath
- [ ] T027 [US3] Add board/cell/overlay styles to `bingo.css`: the fixed 5×5 responsive square-cell grid (centered, max-width 700px on desktop; full-width with square cells on mobile — FR-006/FR-007), unmarked/marked/free/winning-line visual states with a 150-200ms transition (FR-008/FR-009), each cell sized to ≥44×44px even at the narrowest supported width (FR-012), and the overlay's presentation
- [ ] T028 [US3] Extend `backend/tests/integration/test_bingo_views.py` to assert that a finished board's response marks the correct squares via `winning_positions`, and that `backend/tests/unit/test_domain.py`'s new `winning_lines()` tests (T009) pass against the implementation (T010)

**Checkpoint**: User Stories 1-3 independently functional — the core, repeated gameplay loop and its emotional payoff are complete.

---

## Phase 6: User Story 4 - Never hit a dead end (Priority: P4)

**Goal**: Stale links, finished games, an empty buzzword pool, and bad URLs all produce a clear, friendly explanation instead of a blank page or technical error.

**Independent Test**: Visit a nonexistent board link, a nonexistent game link, a join link for a finished game, and (with an emptied buzzword pool) a fresh join attempt — confirm each shows its own specific message.

### Tests for User Story 4 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US4] Write `frontend/e2e/dead-ends.spec.ts` (both projects) covering Acceptance Scenarios 1-4: a non-winning participant's board shows the finished notice and is read-only (reuses T024's markup — this spec is the independent-test check for it), a join link for a finished game shows a finished message instead of a form, an emptied buzzword pool shows its own message, and a nonexistent game/board link shows a not-found message

### Implementation for User Story 4

- [ ] T030 [US4] Add `data-testid="game-finished-notice"` and `data-testid="no-buzzwords-notice"` markup to `join.html`'s existing `finished`/`insufficient_pool` template branches (the underlying logic already exists in `views.py`'s `join_game` — this is markup/styling only)
- [ ] T031 [P] [US4] Add a `backend/bingo/templates/404.html` override with `data-testid="not-found-notice"` and a friendly "not found" message (FR-018), styled consistently with the rest of the app
- [ ] T032 [P] [US4] Add empty-state/finished-state styles to `bingo.css`
- [ ] T033 [US4] Extend `backend/tests/integration/test_bingo_views.py` to assert the not-found/finished/no-buzzwords markup renders correctly

**Checkpoint**: All four user stories independently functional — full spec coverage achieved.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that span every user story.

- [ ] T034 [P] Mirror the polished UX/testing setup into `docs/sphinx/frontend-ux.md` (constitution Documentation-First mitigation, per plan.md)
- [ ] T035 [P] Add a `frontend-e2e` job to `.github/workflows/main.yaml`: set up Node, `npm ci` in `frontend/`, `npx playwright install --with-deps`, then `npm run test:unit` (fails the build below 100% coverage per T001a) and `npm run e2e` with `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` set for the `webServer`-spawned Django process (see T003) — wires FR-020/SC-007's completion gate, and the constitution's 100%-coverage requirement, into CI
- [ ] T036 Run `specs/003-frontend-polish/quickstart.md` end-to-end locally and confirm every step passes
- [ ] T037 [P] Keyboard-only and screen-reader pass across all four screens (Tab order, focus visibility, ARIA roles/labels on the grid/cells/status regions) per FR-011/FR-014, using contracts/ui-contract.md's anchors as the checklist; file follow-ups for any gap found
- [ ] T038 [P] Manual color-contrast audit of `bingo.css`'s palette against WCAG 2.1 AA (FR-013); adjust colors as needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational only
- **User Story 2 (Phase 4)**: Depends on Foundational only (independently testable, though it naturally follows US1 in a real playthrough since it needs a game to join)
- **User Story 3 (Phase 5)**: Depends on Foundational only (its e2e spec creates its own game/board via `game-flow.ts`, though it naturally follows US2 in a real playthrough)
- **User Story 4 (Phase 6)**: Depends on Foundational, and reuses US3's finished/read-only board markup (T024) for its own Acceptance Scenario 1 — implement after US3
- **Polish (Phase 7)**: Depends on all four user stories being complete

### Within Each User Story

- Tests are written first and must fail before implementation (constitution Principle I; FR-020)
- Domain function changes (T009-T010) before the view wiring that uses them (T011)
- The TypeScript module's tests (T014) before its implementation (T015)
- Template/markup changes before their story-specific CSS
- Django integration-test updates last, as a regression net alongside the e2e spec

### Parallel Opportunities

- T002-T004 (Setup) touch different files and can run in parallel; T005 depends on T001-T004 existing; T006-T007 touch Django files independent of the frontend/ scaffold and can run in parallel with it
- T008 (shared CSS), T009 (domain test), and T012 (e2e helper) are independent files and can run in parallel within Foundational; T010 depends on T009, T011 depends on T010
- All `[P]`-marked test tasks within a story can run in parallel (different files)
- Once Foundational (Phase 2) is complete, US1 and US2 can proceed fully in parallel (different templates, no shared state); US3 can also start in parallel since it only depends on Foundational, though it naturally lands after US1/US2 are stable in a real playthrough; US4 should follow US3 since it reuses US3's finished-board markup

---

## Parallel Example: User Story 3

```bash
# Launch the test for User Story 3 (single spec file, but independent of other stories' tests):
Task: "Write frontend/e2e/play-and-win.spec.ts covering tap feedback, animation, free-space, double-tap, overlay, and dismissal"

# Once T024-T026 (templates) are done, these can proceed in parallel:
Task: "Add board/cell/overlay styles to bingo.css (T027)"
Task: "Extend backend/tests/integration/test_bingo_views.py for winning_positions markup (T028)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run `npm run e2e -- create-and-share` and confirm it passes independently
5. Deploy/demo if ready — an organizer can already create and share a polished game link

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo (core gameplay loop complete)
5. Add User Story 4 → Test independently → Deploy/Demo (no more dead ends)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3 (then hands off finished-board markup to whoever picks up US4)
3. Stories complete and integrate independently, with US4 landing last since it depends on US3's read-only board markup

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No new Django app, model, migration, or URL is introduced anywhere in this task list (spec Assumptions) — every implementation task touches an existing template/partial/view, `domain.py`, `bingo.css`, or the new `frontend/` project
- Verify each e2e/unit test fails before implementing the task(s) that make it pass
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- SC-005 (human usability observation) is a directional goal, not a task — per the spec's Clarifications, it is not gated by any task here
