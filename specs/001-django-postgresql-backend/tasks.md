---

description: "Task list template for feature implementation"
---

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Tasks: Django project with PostgreSQL backend](#tasks-django-project-with-postgresql-backend)
  - [Format: `[ID] [P?] [Story] Description`](#format-id-p-story-description)
  - [Path Conventions](#path-conventions)
  - [Phase 1: Setup](#phase-1-setup)
  - [Phase 2: Foundational (Blocking Prerequisites)](#phase-2-foundational-blocking-prerequisites)
  - [Phase 3: User Story 1 - PostgreSQL production backend (Priority: P1) 🎯 MVP](#phase-3-user-story-1---postgresql-production-backend-priority-p1--mvp)
    - [Tests for User Story 1 (MANDATORY) ⚠️](#tests-for-user-story-1-mandatory-)
    - [Implementation for User Story 1](#implementation-for-user-story-1)
  - [Phase 4: User Story 2 - Local developer PostgreSQL support (Priority: P2)](#phase-4-user-story-2---local-developer-postgresql-support-priority-p2)
    - [Tests for User Story 2 (MANDATORY) ⚠️](#tests-for-user-story-2-mandatory-)
    - [Implementation for User Story 2](#implementation-for-user-story-2)
  - [Phase 5: User Story 3 - Test database compatibility (Priority: P3)](#phase-5-user-story-3---test-database-compatibility-priority-p3)
    - [Tests for User Story 3 (MANDATORY) ⚠️](#tests-for-user-story-3-mandatory-)
    - [Implementation for User Story 3](#implementation-for-user-story-3)
  - [Phase 6: Polish & Cross-Cutting Concerns](#phase-6-polish--cross-cutting-concerns)
  - [Dependencies & Execution Order](#dependencies--execution-order)
    - [Phase Dependencies](#phase-dependencies)
    - [User Story Dependencies](#user-story-dependencies)
    - [Within Each User Story](#within-each-user-story)
    - [Parallel Opportunities](#parallel-opportunities)
  - [Parallel Example: Foundational Phase](#parallel-example-foundational-phase)
  - [Parallel Example: User Story 1](#parallel-example-user-story-1)
  - [Implementation Strategy](#implementation-strategy)
    - [MVP First (User Story 1 Only)](#mvp-first-user-story-1-only)
    - [Incremental Delivery](#incremental-delivery)
  - [Notes](#notes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Tasks: Django project with PostgreSQL backend

**Input**: Design documents from `/specs/001-django-postgresql-backend/` **Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/database-config.md, quickstart.md

**Tests**: Tests are MANDATORY.
TDD is strictly enforced per the project constitution (Principle I).
Tests must be written and fail before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are exact, under `backend/` (this feature touches backend configuration only — see plan.md Structure Decision)

## Path Conventions

- **Web app**: `backend/` (Django) + `frontend/` (untouched by this feature)
- Settings package: `backend/config/settings/{base,local,production,test}.py`
- Tests: `backend/tests/unit/`, `backend/tests/integration/`
- Docs: `docs/*.md` (mkdocs-material, existing repo tooling) + `docs/sphinx/` (new minimal Sphinx/MyST scaffold, see T002 — added per `/speckit-analyze` finding C1 to satisfy constitution Principle III for this feature's own documentation, without migrating the repo's existing mkdocs tree)

---

## Phase 1: Setup

**Purpose**: Confirm the project is ready for settings work; scaffold the minimal Sphinx docs target this feature needs.

- [X] T001 Verify the existing `backend/config/` package scaffold (`config/__init__.py`, `config/settings/__init__.py`) and confirm `uv sync` succeeds against `backend/pyproject.toml` with no new dependencies required (`psycopg[binary,pool]` already covers the DB driver and DSN parsing — research.md D1/D10)
- [X] T002 [P] Scaffold a minimal Sphinx + MyST documentation source under `docs/sphinx/` (`conf.py` using `myst-parser`, an `index.md` toctree stub) so this feature's PostgreSQL setup documentation can be published via Sphinx, satisfying constitution Principle III (Documentation First) for this feature's own docs without migrating the repo's existing mkdocs-material tree (`/speckit-analyze` finding C1)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared `config.settings.base` module (DB parser, fail-fast check, shared Django config) and repoint the entrypoints that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Write failing unit tests for the `DATABASE_URL`/`POSTGRES_*` config parser and the `ImproperlyConfigured` fail-fast behavior (hypothesis property-based cases: valid DSN, missing vars, malformed DSN) in `backend/tests/unit/test_database_config.py`
- [X] T004 Migrate shared settings content from `backend/bsbingo/settings.py` into `backend/config/settings/base.py` (INSTALLED_APPS incl. `social_django`, MIDDLEWARE, TEMPLATES, AUTH_PASSWORD_VALIDATORS, i18n, static files, social-auth config) — dedicated refactor-first step per constitution Governance
- [X] T005 Implement the pure `DATABASE_URL`/`POSTGRES_*` parser and `ImproperlyConfigured` fail-fast check in `backend/config/settings/base.py`, wiring `DATABASES["default"]` (always `ENGINE=django.db.backends.postgresql`, never sqlite3) — makes T003 pass (depends on T004)
- [X] T006 [P] Create `backend/config/urls.py` (moved from `backend/bsbingo/urls.py`) and set `ROOT_URLCONF="config.urls"` in `backend/config/settings/base.py` (depends on T005)
- [X] T007 [P] Create `backend/config/wsgi.py` exposing `config.wsgi.application`, defaulting `DJANGO_SETTINGS_MODULE` to `config.settings.local` (depends on T005)
- [X] T008 [P] Create `backend/config/asgi.py` exposing `config.asgi:application` (required — `k8s/sandbox/kustomization.yaml` already invokes it via daphne), defaulting `DJANGO_SETTINGS_MODULE` to `config.settings.local` (depends on T005)
- [X] T009 [P] Repoint `backend/manage.py` to default `DJANGO_SETTINGS_MODULE` to `config.settings.local` (depends on T005)
- [X] T010 [P] Add `[tool.pytest.ini_options]` with `DJANGO_SETTINGS_MODULE = "config.settings.test"` to `backend/pyproject.toml` (research.md D6)

**Checkpoint**: Foundation ready — `config.settings.base` (with the parser and fail-fast check), and `config/{urls,wsgi,asgi}.py` all exist and `manage.py` is repointed.
User story implementation can now begin.

---

## Phase 3: User Story 1 - PostgreSQL production backend (Priority: P1) 🎯 MVP

**Goal**: The Django application uses PostgreSQL in production, with migrations applying successfully.

**Independent Test**: Deploy the application using production settings and verify that the database connection is PostgreSQL and migrations apply successfully.

### Tests for User Story 1 (MANDATORY) ⚠️

- [X] T011 [P] [US1] Write integration test asserting `config.settings.production` yields `DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"` and `DEBUG=False` in `backend/tests/integration/test_production_settings.py`

### Implementation for User Story 1

- [X] T012 [US1] Create `backend/config/settings/production.py` (`DEBUG=False`, SSL redirect/HSTS/secure-cookie hardening, strict `ALLOWED_HOSTS`) importing from `base` — makes T011 pass (depends on T005)
- [X] T013 [US1] Validate quickstart.md Scenario A: run `python manage.py migrate` under `config.settings.production` against a real PostgreSQL instance and confirm the schema is created successfully within SC-001's 10-minute bound
- [X] T014 [P] [US1] Document production PostgreSQL setup steps, including the required connection env vars (host/port/db/user/password), in `docs/deployment.md` (FR-002, FR-007)
- [X] T015 [P] [US1] Mirror the production PostgreSQL setup steps from T014 into a new Sphinx/MyST page in `docs/sphinx/` (constitution Principle III — depends on T002, T014)

**Checkpoint**: User Story 1 is fully functional and testable independently — this is the MVP.

---

## Phase 4: User Story 2 - Local developer PostgreSQL support (Priority: P2)

**Goal**: A documented local development workflow runs the Django app against PostgreSQL.

**Independent Test**: Follow the local setup instructions and confirm the app starts, connects, and runs migrations against PostgreSQL.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T016 [P] [US2] Write integration test asserting `config.settings.local` yields `DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"` and `DEBUG=True` in `backend/tests/integration/test_local_settings.py`

### Implementation for User Story 2

- [X] T017 [US2] Create `backend/config/settings/local.py` (`DEBUG=True`, dev conveniences, still Postgres) importing from `base` — makes T016 pass (depends on T005)
- [X] T018 [US2] Validate quickstart.md Scenario B: `make setup` → `direnv allow` → `tilt up` → `make shell-backend` → `python manage.py migrate` against the local PostgreSQL StatefulSet, confirming no more than two manual steps beyond installing dependencies (SC-002)
- [X] T019 [P] [US2] Document local developer PostgreSQL setup steps, including the required connection env vars (host/port/db/user/password) and a note to delete any pre-existing local `backend/db.sqlite3` file left over from before this change, in `docs/development.md` (FR-002, FR-007)
- [X] T020 [P] [US2] Mirror the local developer PostgreSQL setup steps from T019 into a new Sphinx/MyST page in `docs/sphinx/` (constitution Principle III — depends on T002, T019)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Test database compatibility (Priority: P3)

**Goal**: The backend test suite runs against PostgreSQL (or a PostgreSQL-compatible test DB) only — never SQLite.

**Independent Test**: Run the backend test suite using PostgreSQL-backed test settings and confirm no database-related failures occur.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T021 [P] [US3] Write test asserting `settings.DATABASES["default"]["ENGINE"].endswith("postgresql")` under `config.settings.test` in `backend/tests/unit/test_test_settings.py`

### Implementation for User Story 3

- [X] T022 [US3] Create `backend/config/settings/test.py` (imports `base`, Postgres-only, fast password hashers) — makes T021 pass (depends on T005, T010)
- [X] T023 [US3] Fix the Makefile's `CI=true` `backend-test` branch to use `uv`/`pyproject.toml` instead of the stale `requirements/*.txt` + `scafman/` path (research.md D9 — required for SC-003)
- [X] T024 [P] [US3] Bump `actions/setup-python` from `"3.10"` to `"3.14"` in `.github/workflows/main.yaml` to match `.python-version` (research.md D9)
- [X] T025 [P] [US3] Fix CI's misleading `POSTGRES_HOST=postgres` env var (rely on `DATABASE_URL` as canonical, per D1) in `.github/workflows/main.yaml` so it matches the service-container topology (research.md D9)
- [X] T026 [US3] Validate quickstart.md Scenario C: run `CI=true make backend-test` and `make backend-test` locally, confirming the full suite passes against PostgreSQL only (SC-003), including the T003 hypothesis-based parser tests

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final fail-fast validation and the legacy-cleanup refactor step, once all three settings modules are proven to work.

- [X] T027 Validate quickstart.md Scenario D: confirm `ImproperlyConfigured` is raised when `DATABASE_URL`/`POSTGRES_*` are unset, confirm a psycopg `OperationalError` surfaces promptly on an invalid host during `migrate`, and confirm `db.sqlite3` is never created, across all three settings modules
- [X] T028 Remove legacy `backend/bsbingo/settings.py`, `bsbingo/wsgi.py`, `bsbingo/asgi.py`, `bsbingo/urls.py`, and `backend/db.sqlite3` now that `config.settings.*` is verified working across all three stories (research.md D7 step 3; satisfies SC-004) — depends on T013, T018, T026
- [X] T029 [P] Grep the repo for remaining SQLite references (Django settings, k8s manifests, `.envrc`) to confirm SC-004 ("no configuration continues to rely on SQLite") is fully satisfied after T028

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately (T001, T002 both parallelizable)
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion; can proceed in parallel or in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: T027 can run once Foundational + any story is done; T028 depends on T013, T018, and T026 (all three stories verified working); T029 depends on T028

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependency on other stories; its Sphinx doc task (T015) depends on the T002 scaffold from Setup
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — independent of US1; its Sphinx doc task (T020) depends on the T002 scaffold from Setup
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — independent of US1/US2; reuses the T003 parser tests written in Foundational

### Within Each User Story

- Tests (T011/T016/T021) MUST be written and FAIL before their corresponding settings module (T012/T017/T022) is implemented
- Settings module before validation task before mkdocs documentation task before Sphinx mirror task

### Parallel Opportunities

- Setup: T001 and T002 can run in parallel
- Within Foundational: T006, T007, T008, T009, T010 (different files) can run in parallel once T005 is done
- Once Foundational completes, US1 (T011-T015), US2 (T016-T020), and US3 (T021-T026) can proceed in parallel if staffed
- Within each story, the `[P]`-marked test and documentation tasks can run in parallel with each other

---

## Parallel Example: Foundational Phase

```bash
# After T005 (parser + fail-fast check) is done, launch together:
Task: "Create backend/config/urls.py and set ROOT_URLCONF"
Task: "Create backend/config/wsgi.py"
Task: "Create backend/config/asgi.py"
Task: "Repoint backend/manage.py"
Task: "Add [tool.pytest.ini_options] to backend/pyproject.toml"
```

## Parallel Example: User Story 1

```bash
Task: "Write integration test for config.settings.production in backend/tests/integration/test_production_settings.py"
# (T012 depends on T005, runs after Foundational; T014 docs task can run in parallel with T012/T013)
Task: "Document production PostgreSQL setup steps in docs/deployment.md"
# (T015 depends on T002 + T014)
Task: "Mirror production setup steps into docs/sphinx/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run quickstart.md Scenario A independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add US1 → validate independently → MVP
3. Add US2 → validate independently
4. Add US3 → validate independently
5. Phase 6: fail-fast validation (T027), legacy cleanup (T028), final SC-004 confirmation (T029)

---

## Notes

- `[P]` tasks touch different files with no unmet dependencies
- `[Story]` label maps each task to its user story for traceability
- Constitution's Strong Typing (Principle V) status is being resolved via a separate `/speckit-constitution` amendment (per `/speckit-analyze` finding C2); once ratified, a follow-up task should wire `pyrefly`/`ty` strict-mode CI enforcement — not included here since it wasn't part of the ratified constitution at the time this task list was generated
- Constitution's Documentation-First Sphinx requirement (finding C1) is addressed for this feature's own docs via T002/T015/T020; the repo's broader mkdocs-vs-Sphinx tooling question for pre-existing docs remains a separate, out-of-scope decision
- Legacy settings removal (T028) is intentionally sequenced last, after all three stories are verified, per the constitution's refactor-first guidance and research.md D7
