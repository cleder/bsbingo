<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Implementation Plan: Django project with PostgreSQL backend](#implementation-plan-django-project-with-postgresql-backend)
  - [Summary](#summary)
  - [Technical Context](#technical-context)
  - [Constitution Check](#constitution-check)
  - [Project Structure](#project-structure)
    - [Documentation (this feature)](#documentation-this-feature)
    - [Source Code (repository root)](#source-code-repository-root)
  - [Complexity Tracking](#complexity-tracking)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Implementation Plan: Django project with PostgreSQL backend

**Branch**: `001-django-postgresql-backend` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-django-postgresql-backend/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command.
See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Wire the existing Django scaffold to use PostgreSQL as the only supported database backend in every environment (production, local development, and tests), with no SQLite fallback and fail-fast behavior when Postgres configuration is missing or invalid.
The repo already has a `sixfeetup/scaf-fullstack-template` k8s/CI contract (`DATABASE_URL`, `POSTGRES_*` env vars, `config.settings.{local,production}` module names) that must be consumed as-is.
The approach: build out the stubbed `config.settings.{base,local,production,test}` package with a pure `DATABASE_URL` parser (reusing the already-installed `psycopg` driver, no new dependency), retire the legacy SQLite-based `bsbingo.settings` module as a dedicated refactor step, and reconcile the stale Makefile/CI test-running path so PostgreSQL-only tests actually run in CI.

## Technical Context

**Language/Version**: Python 3.14 (per `.python-version` / `pyproject.toml` `requires-python`) **Primary Dependencies**: Django ≥6.0.7, `psycopg[binary,pool]` ≥3.3.4 (psycopg3 — DB driver and DSN parser), `social-auth-app-django`, `django-htmx`; dependency management via `uv` **Storage**: PostgreSQL 17 in every environment — `postgres:17` StatefulSet locally (kind/Tilt), CloudNativePG-managed cluster in sandbox/production, `postgres:17` service container in CI.
SQLite is prohibited everywhere, including the test database.
**Testing**: pytest + `pytest-django` + `hypothesis[django]` (property-based), run against a real PostgreSQL test database; `deptry` for dependency hygiene **Target Platform**: Linux server on Kubernetes (kind + Tilt locally; CloudNativePG in sandbox/production), served via Daphne/ASGI (`config.asgi:application`) **Project Type**: Web application (separate `backend/` and `frontend/`); this feature touches backend configuration only **Performance Goals**: Not performance-driven; bounded by SC-001 (prod startup + migrate under 10 minutes) **Constraints**: Must fail fast with an explicit configuration/connection error if PostgreSQL is missing or misconfigured in any non-test environment (FR-006); must never fall back to SQLite, including for tests (FR-001/003/005); must consume the existing k8s/CI env-var contract without redesigning it **Scale/Scope**: Small and self-contained — a Django settings package (~5 modules), `manage.py`/`wsgi`/`asgi` entrypoint rewiring, and CI/Makefile reconciliation.
No new ORM models, no new INSTALLED_APPS entries.

## Constitution Check

*GATE: Must pass before Phase 0 research.*
*Re-check after Phase 1 design.*

| Principle | Verdict | Rationale |
|---|---|---|
| I. Strict Test-Driven Development | PASS | The `DATABASE_URL` parser is a pure function, well-suited to hypothesis property-based tests written before implementation; the test suite itself runs against real PostgreSQL per FR-005. |
| II. Separation of Concerns & Modularity | PASS | `config.settings.base/local/production/test` keeps environment concerns isolated; DB-URL parsing lives in one small, single-purpose helper, not spread across views/business logic. |
| III. Documentation First | PASS (mitigated, per `/speckit-analyze` finding C1) | Constitution mandates docs be kept in Sphinx, while the repo's actual doc tooling is `mkdocs-material` (`Makefile` `docs`/`serve-docs` targets) — a pre-existing, repo-wide mismatch. For this feature specifically, `tasks.md` T002 scaffolds a minimal Sphinx/MyST doc source, and T015/T020 mirror this feature's production/local PostgreSQL setup docs into it, so this feature's own documentation satisfies the MUST. The broader repo-wide mkdocs-vs-Sphinx question for pre-existing docs remains a separate, out-of-scope decision. |
| IV. Functional Programming Patterns | PASS | Environment → `DATABASES` dict is modeled as a pure function rather than a stateful config object or new dependency. |
| V. Strong Typing & Safe Types | CONCERN (ratified; enforcement not yet in this feature's tasks) | Constitution v1.2.0 now ratifies Principle V (full type annotations; `pyrefly`/`ty` strict-mode CI enforcement) — resolved via `/speckit-constitution` per `/speckit-analyze` finding C2. `tasks.md` for this feature predates the amendment and does not yet include a `pyrefly`/`ty` CI-wiring task; that CI enforcement is still a repo-wide outstanding item (constitution Sync Impact Report), not blocking this specific feature, but new code in this feature (the DATABASE_URL parser, settings modules) should be written fully type-annotated regardless of whether CI enforces it yet. |
| Technology & Constraints | PASS | Stays within Python/Django/`python-social-auth`; introduces no new JavaScript frameworks or dependencies. |
| Governance (refactor-first workflow) | PASS, with required sequencing | Removing the legacy `bsbingo.settings`/`wsgi`/`asgi`/`urls` modules is planned as a dedicated refactor step performed *after* the new `config.settings.*` modules are verified working, per "refactor first" guidance. |

No Complexity Tracking entries are required — this design does not add complexity beyond the spec's needs.
Both constitution rows above surfaced as findings during `/speckit-analyze` (C1, C2) and have since been resolved: III is mitigated within this feature's own scope (Sphinx mirror docs added to `tasks.md`); V was ratified via a `/speckit-constitution` amendment (v1.1.1 → v1.2.0) that completed the principle text the prior changelog had only claimed to add.
Repo-wide `pyrefly`/`ty` CI enforcement remains a outstanding item tracked in the constitution's own Sync Impact Report, not a blocker for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/001-django-postgresql-backend/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── manage.py                     # repointed default: DJANGO_SETTINGS_MODULE=config.settings.local
├── config/
│   ├── settings/
│   │   ├── __init__.py           # already stubbed
│   │   ├── base.py               # shared settings + DATABASE_URL parser + fail-fast check
│   │   ├── local.py               # DEBUG=True, dev conveniences, still Postgres
│   │   ├── production.py         # security hardening, strict ALLOWED_HOSTS
│   │   └── test.py               # pytest-django target, still Postgres, never SQLite
│   ├── wsgi.py                   # new — repoints WSGI entrypoint
│   ├── asgi.py                   # new — required, gunicorn+uvicorn invoke config.asgi:application
│   └── urls.py                   # new — moved from bsbingo/urls.py
├── bsbingo/                      # legacy scaffold — settings/wsgi/asgi/urls removed as a
│   └── …                         # dedicated refactor step once config.settings.* is verified
├── bingo/                        # existing scaffolded app, out of scope for this feature
└── pyproject.toml                # add [tool.pytest.ini_options] DJANGO_SETTINGS_MODULE=config.settings.test

frontend/                          # untouched by this feature

k8s/, Makefile, .github/workflows/main.yaml
                                    # consumed as-is (env-var contract already fixed);
                                    # Makefile CI branch + CI Python version reconciled
                                    # as a task (needed for SC-003), not redesigned
```

**Structure Decision**: Web application layout (existing `backend/` + `frontend/` split).
This feature only touches `backend/`: it builds out the already-stubbed `config.settings.{base,local,production,test}` package, adds `config/wsgi.py`, `config/asgi.py`, and `config/urls.py`, repoints `manage.py`, and retires the legacy `bsbingo.settings`/`wsgi`/`asgi`/`urls` modules and `db.sqlite3` once the new modules are verified.
The `bingo` app and `/healthz`/`/readiness` health-check routes remain out of scope (adjacent gaps, not part of this feature).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Not applicable — this design introduces no complexity beyond what the spec requires; no violations require justification. (The two Documentation-First / Strong-Typing CONCERNNs above are pre-existing repo-wide gaps, not violations introduced by this feature.)
