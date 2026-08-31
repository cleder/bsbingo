<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Tasks: Buzzword Categories](#tasks-buzzword-categories)
  - [Format: `[ID] [P?] [Story] Description`](#format-id-p-story-description)
  - [Path Conventions](#path-conventions)
  - [Phase 1: Setup](#phase-1-setup)
  - [Phase 2: Foundational (Blocking Prerequisites)](#phase-2-foundational-blocking-prerequisites)
  - [Phase 3: User Story 1 - Filter buzzwords by category when creating a game (Priority: P1) 🎯 MVP](#phase-3-user-story-1---filter-buzzwords-by-category-when-creating-a-game-priority-p1--mvp)
    - [Tests for User Story 1 (MANDATORY) ⚠️](#tests-for-user-story-1-mandatory-)
    - [Implementation for User Story 1](#implementation-for-user-story-1)
  - [Phase 4: User Story 2 - Manage categories on buzzwords (Priority: P2)](#phase-4-user-story-2---manage-categories-on-buzzwords-priority-p2)
    - [Tests for User Story 2 (MANDATORY) ⚠️](#tests-for-user-story-2-mandatory-)
    - [Implementation for User Story 2](#implementation-for-user-story-2)
  - [Phase 5: User Story 3 - Browse and manage the category list (Priority: P3)](#phase-5-user-story-3---browse-and-manage-the-category-list-priority-p3)
    - [Tests for User Story 3 (MANDATORY) ⚠️](#tests-for-user-story-3-mandatory-)
    - [Implementation for User Story 3](#implementation-for-user-story-3)
  - [Phase 6: Polish & Cross-Cutting Concerns](#phase-6-polish--cross-cutting-concerns)
  - [Dependencies & Execution Order](#dependencies--execution-order)
    - [Phase Dependencies](#phase-dependencies)
    - [User Story Dependencies](#user-story-dependencies)
    - [Within Each User Story](#within-each-user-story)
    - [Parallel Opportunities](#parallel-opportunities)
  - [Parallel Example: User Story 1](#parallel-example-user-story-1)
  - [Implementation Strategy](#implementation-strategy)
    - [MVP First (User Story 1 Only)](#mvp-first-user-story-1-only)
    - [Incremental Delivery](#incremental-delivery)
    - [Parallel Team Strategy](#parallel-team-strategy)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Tasks: Buzzword Categories

**Input**: Design documents from `/specs/004-buzzword-categories/` **Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/routes.md](./contracts/routes.md), [quickstart.md](./quickstart.md)

**Tests**: Tests are MANDATORY (constitution Principle I — Strict TDD).
Every test task below MUST be written and MUST fail before its corresponding implementation task begins.

**Organization**: Tasks are grouped by user story (from spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Maps the task to US1/US2/US3 from spec.md
- All file paths are relative to the repository root

## Path Conventions

Single Django project — all paths under `backend/bingo/` and `backend/tests/`, per [plan.md](./plan.md)'s Project Structure.

---

## Phase 1: Setup

**Purpose**: Confirm a clean baseline before touching shared model/view code

- [ ] T001 Run the existing backend test suite (`cd backend && pytest`) to confirm a green baseline before any changes in this feature

**Checkpoint**: Baseline confirmed green — safe to start foundational changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared schema, invariants, and the refactor-first preparation that every user story depends on.
No user story work may begin until this phase is complete (constitution's refactor-first rule: the `create_game`/`join_game` restructuring MUST land as its own step before category-filter behavior is layered on).

**⚠️ CRITICAL**: All user stories depend on this phase.

- [ ] T002 [P] Write failing unit tests for the `Category` model (name required, case-insensitive uniqueness per FR-005, `active` defaults to `True`, ordering by `name`) in backend/tests/unit/test_models.py
- [ ] T003 [P] Write failing unit tests for `Buzzword.categories` (a buzzword MUST have ≥1 category to save; the `m2m_changed` guard rejects removing a buzzword's last remaining category via `.remove()`/`.clear()`) in backend/tests/unit/test_models.py
- [ ] T004 [P] Write failing unit tests for `Game.buzzword_pool` (M2M to `Buzzword`, empty by default, assignable) in backend/tests/unit/test_models.py
- [ ] T005 Add the `Category` model in backend/bingo/models.py (`id` UUID PK, `name` CharField, `active` BooleanField, `created_at`, `Meta.ordering = ("name",)`, `UniqueConstraint` on `Lower("name")` per research.md Decision R4) — makes T002 pass
- [ ] T006 Add `Buzzword.categories = ManyToManyField(Category, related_name="buzzwords")` in backend/bingo/models.py — schema half of T003
- [ ] T007 Add an `m2m_changed` receiver on `Buzzword.categories` (`pre_remove`/`pre_clear`) in backend/bingo/models.py that raises if the change would leave a buzzword with zero categories, per research.md Decision R1 — makes T003 fully pass (depends on T006)
- [ ] T008 Add `Game.buzzword_pool = ManyToManyField(Buzzword, related_name="games")` in backend/bingo/models.py — makes T004 pass
- [ ] T009 Generate the migration for `Category`, `Buzzword.categories`, and `Game.buzzword_pool` via `python manage.py makemigrations bingo` and review the output file in backend/bingo/migrations/ (depends on T005, T006, T008)
- [ ] T010 [Refactor-first] Refactor `join_game` in backend/bingo/views.py to source its buzzword pool from `game.buzzword_pool.filter(active=True)` instead of the global `Buzzword.objects.filter(active=True)` (depends on T008, T009)
- [ ] T011 [Refactor-first] Refactor `create_game` in backend/bingo/views.py to populate the new `Game.buzzword_pool` with every currently active buzzword at creation time (no category/selection UI yet — preserves today's observable behavior while wiring the new field), per the constitution's refactor-first rule (depends on T010)
- [ ] T012 Write/update an integration test in backend/tests/integration/test_bingo_views.py asserting `create_game` → `join_game` still produces boards identically to prior behavior now that the pool is sourced from `Game.buzzword_pool` (depends on T010, T011)

**Checkpoint**: Schema, invariants, and the buzzword-pool refactor are in place and covered by passing tests — user story work can now begin.

---

## Phase 3: User Story 1 - Filter buzzwords by category when creating a game (Priority: P1) 🎯 MVP

**Goal**: A game creator selects one or more categories during game creation and is offered only buzzwords tagged with at least one selected category; selecting none still offers all active buzzwords; at least one buzzword must be selected to proceed.

**Independent Test**: Create buzzwords tagged with different categories, start game creation, select a category, and confirm only matching buzzwords are offered; confirm submitting with zero buzzwords selected is rejected.

### Tests for User Story 1 (MANDATORY) ⚠️

> Write these tests FIRST, ensure they FAIL before implementation

- [ ] T013 [P] [US1] Integration test: selecting a category during game creation narrows the offered buzzwords to only those tagged with it (Acceptance Scenario 1) in backend/tests/integration/test_bingo_views.py
- [ ] T014 [P] [US1] Integration test: a buzzword tagged with two categories appears when either category is selected individually (Acceptance Scenario 2) in backend/tests/integration/test_bingo_views.py
- [ ] T015 [P] [US1] Integration test: selecting no category still offers all active buzzwords (Acceptance Scenario 3 / FR-008) in backend/tests/integration/test_bingo_views.py
- [ ] T016 [P] [US1] Integration test: submitting game creation with zero buzzwords selected is rejected with a validation error and no `Game` is created (Acceptance Scenario 4 / FR-012) in backend/tests/integration/test_bingo_views.py
- [ ] T017 [P] [US1] Integration test: selecting a category with zero active buzzwords shows an empty state, not an error (edge case) in backend/tests/integration/test_bingo_views.py

### Implementation for User Story 1

- [ ] T018 [P] [US1] Add `CategoryFilterForm` (optional multi-select of active categories) and `BuzzwordPoolForm` (`ModelMultipleChoiceField(required=True)` over active buzzwords) in backend/bingo/forms.py
- [ ] T019 [US1] Add an HTMX fragment view (e.g. `buzzword_choices`) in backend/bingo/views.py that accepts selected category IDs and returns the filtered/unfiltered active-buzzword checklist fragment (depends on T018)
- [ ] T020 [US1] Wire the new fragment route in backend/bingo/urls.py (e.g. `game/create/buzzwords/`)
- [ ] T021 [P] [US1] Create backend/bingo/templates/bingo/partials/_buzzword_choices.html rendering the (possibly empty) buzzword checklist
- [ ] T022 [US1] Update `create_game` in backend/bingo/views.py to render the category checklist, validate the submitted `BuzzwordPoolForm` (rejecting zero selections per FR-012), and populate `Game.buzzword_pool` from the validated selection on success (depends on T018, T019)
- [ ] T023 [US1] Update backend/bingo/templates/bingo/home.html with the category checklist, the HTMX-swapped buzzword checklist target, and validation error display for zero-buzzwords-selected (depends on T021, T022)

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - Manage categories on buzzwords (Priority: P2)

**Goal**: An administrator assigns/removes categories on a buzzword and creates categories as needed, without affecting other buzzwords or existing boards.

**Independent Test**: Create a category, assign it to a buzzword via the admin interface, confirm it persists, then remove/change it independently of other buzzwords.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T024 [P] [US2] Integration test: assigning a category to an existing buzzword via the admin change form persists and lists the buzzword under that category (Acceptance Scenario 1) in backend/tests/integration/test_bingo_views.py
- [ ] T025 [P] [US2] Integration test: removing one of a buzzword's multiple categories leaves the others intact and does not affect existing boards (Acceptance Scenario 2) in backend/tests/integration/test_bingo_views.py
- [ ] T026 [P] [US2] Integration test: attempting to save a buzzword admin form with zero categories selected is rejected (edge case / FR-001) in backend/tests/integration/test_bingo_views.py
- [ ] T027 [P] [US2] Integration test: `CategoryAdmin` offers no delete action/permission for any category, referenced or not — only deactivation is available (Acceptance Scenario 3 / FR-003 / FR-010) in backend/tests/integration/test_bingo_views.py

### Implementation for User Story 2

- [ ] T028 [US2] Update `BuzzwordAdmin` in backend/bingo/admin.py: add a required `categories` field (`filter_horizontal` widget) and a `list_filter` entry for `categories`
- [ ] T029 [US2] Register `Category` in backend/bingo/admin.py with a `CategoryAdmin` mirroring `BuzzwordAdmin` (list/search/filter by `active`, `make_active`/`make_inactive` bulk actions); override `has_delete_permission` to return `False` and exclude the bulk "delete selected" action, per research.md Decision R6 — makes T027 pass

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Browse and manage the category list (Priority: P3)

**Goal**: An administrator browses, creates, renames, and deactivates categories, mirroring existing buzzword management.

**Independent Test**: Create, rename, and deactivate a category through the admin interface; confirm the changes are reflected in the category list and in game-creation filtering.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T030 [P] [US3] Integration test: creating a category with a unique name via admin makes it appear in the category list and selectable during game creation (Acceptance Scenario 1) in backend/tests/integration/test_bingo_views.py
- [ ] T031 [P] [US3] Integration test: deactivating a category removes it from the game-creation category checklist while leaving already-tagged buzzwords unaffected (Acceptance Scenario 2) in backend/tests/integration/test_bingo_views.py
- [ ] T032 [P] [US3] Integration test: creating a category with a name that duplicates an existing one (case-insensitively) is rejected with a validation error (edge case / FR-005) in backend/tests/integration/test_bingo_views.py

### Implementation for User Story 3

- [ ] T033 [US3] Ensure `CategoryFilterForm` (backend/bingo/forms.py) and the category-checklist rendering in `create_game`/home.html only offer `active=True` categories (depends on Phase 3, T018/T023) — makes T031 pass
- [ ] T034 [US3] Confirm/adjust `CategoryAdmin` (backend/bingo/admin.py) rename/deactivate flows surface the case-insensitive uniqueness validation error from the model constraint (depends on T029) — makes T032 pass

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation across all stories

- [ ] T035 [P] Add docs/sphinx/categories.md documenting the category concept and the updated game-creation flow, per plan.md's Documentation First mitigation
- [ ] T036 Run the [quickstart.md](./quickstart.md) validation scenarios end-to-end against a local dev environment
- [ ] T037 Run the full backend test suite (`cd backend && pytest`) and confirm all tests pass with no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (schema + refactor-first step)
- **User Story 1 (Phase 3)**: Depends on Foundational only
- **User Story 2 (Phase 4)**: Depends on Foundational only — independently testable from US1, though realistically exercised after US1's model work lands
- **User Story 3 (Phase 5)**: Depends on Foundational and reuses US1's category-checklist rendering (T018/T023) and US2's `CategoryAdmin` (T029) for its own validation checks
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on US2/US3 — independently testable once Foundational is done
- **User Story 2 (P2)**: No dependencies on US1/US3 — independently testable once Foundational is done
- **User Story 3 (P3)**: Builds on US1's category-checklist UI and US2's `CategoryAdmin`, but its own acceptance scenarios are independently verifiable

### Within Each User Story

- Tests MUST be written and FAIL before implementation begins
- Models/forms before views before templates
- Story complete before moving to the next priority (if working sequentially)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (only one exists here)
- T002, T003, T004 (foundational tests) can run in parallel — different assertions, same file, write together before any model code
- Once Foundational (Phase 2) completes, US1 and US2 can be implemented in parallel by different developers; US3 should follow since it depends on artifacts from both
- All [P]-marked test tasks within a story can run in parallel
- T018 and T021 (form vs. template) can run in parallel within US1

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Integration test: category selection narrows offered buzzwords in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: multi-category buzzword appears under either category in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: no category selected offers all active buzzwords in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: zero buzzwords selected is rejected in backend/tests/integration/test_bingo_views.py"
Task: "Integration test: category with zero active buzzwords shows empty state in backend/tests/integration/test_bingo_views.py"

# Launch independent implementation pieces together:
Task: "Add CategoryFilterForm and BuzzwordPoolForm in backend/bingo/forms.py"
Task: "Create backend/bingo/templates/bingo/partials/_buzzword_choices.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (schema + refactor-first step — CRITICAL, blocks everything)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm category filtering + mandatory buzzword selection work end-to-end
5. Deploy/demo if ready — US1 alone delivers the feature's core value

### Incremental Delivery

1. Setup + Foundational → schema and refactor-first step land, existing behavior unchanged
2. Add US1 → test independently → deploy/demo (MVP: category filtering at game creation)
3. Add US2 → test independently → deploy/demo (admins can manage buzzword↔category assignments)
4. Add US3 → test independently → deploy/demo (full category list CRUD/lifecycle)
5. Polish → docs + full regression pass

### Parallel Team Strategy

With multiple developers, once Foundational (Phase 2) is done:

- Developer A: User Story 1 (game-creation category filter)
- Developer B: User Story 2 (buzzword admin category management)
- Developer C: starts User Story 3 once A and B's shared pieces (T018/T023, T029) are available
