<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Research: Django project with PostgreSQL backend](#research-django-project-with-postgresql-backend)
  - [D1 — Parse `DATABASE_URL` with psycopg3; no new URL-parsing dependency](#d1--parse-database_url-with-psycopg3-no-new-url-parsing-dependency)
  - [D2 — Settings split: thin environment leaves over a shared base](#d2--settings-split-thin-environment-leaves-over-a-shared-base)
  - [D3 — Fail-fast is universal, including `test`, raised at import time](#d3--fail-fast-is-universal-including-test-raised-at-import-time)
  - [D4 — Entrypoints default to `config.settings.local`](#d4--entrypoints-default-to-configsettingslocal)
  - [D5 — Local dev selection uses existing mechanisms only](#d5--local-dev-selection-uses-existing-mechanisms-only)
  - [D6 — Test settings wire pytest-django to real PostgreSQL](#d6--test-settings-wire-pytest-django-to-real-postgresql)
  - [D7 — Retire the legacy `bsbingo` settings module as a dedicated refactor step](#d7--retire-the-legacy-bsbingo-settings-module-as-a-dedicated-refactor-step)
  - [D8 — Migration workflow stays standard; no new migrations authored](#d8--migration-workflow-stays-standard-no-new-migrations-authored)
  - [D9 — CI/Makefile reconciliation is required to validate this feature](#d9--cimakefile-reconciliation-is-required-to-validate-this-feature)
  - [D10 — No new runtime dependency](#d10--no-new-runtime-dependency)
  - [Flags recorded for visibility (not fixed as part of this planning step)](#flags-recorded-for-visibility-not-fixed-as-part-of-this-planning-step)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Research: Django project with PostgreSQL backend

**Feature**: `001-django-postgresql-backend` | **Date**: 2026-07-11

This document resolves the technical unknowns for wiring PostgreSQL as the sole Django database backend, grounded in the existing repo state (a `sixfeetup/scaf-fullstack-template` copier scaffold whose k8s manifests, Makefile, and CI already assume a `config.settings.{base,local,production,test}` package and a `DATABASE_URL`/`POSTGRES_*` env-var contract that don't exist in Django settings yet).

## D1 — Parse `DATABASE_URL` with psycopg3; no new URL-parsing dependency

- **Decision**: In `config/settings/base.py`, a small pure function reads `DATABASE_URL` and builds Django's `DATABASES["default"]` dict (`ENGINE=django.db.backends.postgresql`), parsing the DSN via `psycopg.conninfo.conninfo_to_dict()`.
  Discrete `POSTGRES_*` vars are consulted only as a local-dev fallback when `DATABASE_URL` is absent.
- **Rationale**: Sandbox/production only expose `host` and `uri` via the CloudNativePG `postgres-app` secret (confirmed in `k8s/sandbox/kustomization.yaml` patches) — no discrete `POSTGRES_PASSWORD`/`USER`/`DB` keys are wired there — so `DATABASE_URL` must be canonical.
  `psycopg[binary,pool]>=3.3.4` is already a dependency and ships a DSN parser, so no new library is needed.
  A pure `env -> dict` function is trivially hypothesis-testable, satisfying the TDD and Functional Programming principles.
- **Alternatives considered**: `dj-database-url` / `django-environ` / `python-decouple`
  (new dependencies, redundant with psycopg3's parser); hand-rolled `urllib.parse`
  (re-implements what psycopg already provides and risks mishandling DSN edge cases).

## D2 — Settings split: thin environment leaves over a shared base

- **Decision**: `base.py` carries everything shared — migrated content from the legacy
  `bsbingo/settings.py` (INSTALLED_APPS incl. `social_django`, MIDDLEWARE, TEMPLATES,
  AUTH_PASSWORD_VALIDATORS, i18n, static files, social-auth config), plus
  `SECRET_KEY`/`ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` from env, `WSGI_APPLICATION=
  "config.wsgi.application"`, `ROOT_URLCONF="config.urls"`, and the `DATABASES` dict from
  D1. `local.py`/`production.py`/`test.py` are thin leaves (`from .base import *`) that
  only override environment-specific values (`DEBUG`, security hardening, host
  restrictions). `config/asgi.py` exposing `config.asgi:application` is required — k8s
  sandbox invokes it directly via gunicorn with an uvicorn worker
  (`k8s/sandbox/kustomization.yaml`:
  `["config.asgi:application", "-k", "uvicorn_worker.UvicornWorker", "--bind", "0.0.0.0:8000"]`,
  replacing an earlier `daphne` command that referenced a dependency the project never
  actually installed).
- **Rationale**: Single source of DB truth plus fail-fast logic in one place; leaves stay
  thin and match the `DJANGO_SETTINGS_MODULE` values already baked into the base
  ConfigMap (`config.settings.local`) and sandbox/production overlay
  (`config.settings.production`).
- **Alternatives considered**: A monolithic settings module with `if ENVIRONMENT`
  branches (rejected — muddies separation of concerns and makes the fail-fast guarantee
  harder to reason about for every entrypoint).

## D3 — Fail-fast is universal, including `test`, raised at import time

- **Decision**: `base.py` raises `django.core.exceptions.ImproperlyConfigured` at import time if neither `DATABASE_URL` nor a complete discrete `POSTGRES_*` set is present/parseable, naming the missing variable(s) explicitly.
  Because the parser only ever emits `ENGINE=django.db.backends.postgresql`, SQLite is structurally unreachable.
  This applies to `config.settings.test` as well — the spec forbids SQLite in tests too.
  Connection-time failures (e.g. an unreachable host) surface naturally as psycopg `OperationalError` on first DB access or during `migrate`; the k8s `pg_isready` initContainer already handles wait-for-db, so Django itself does not need retry logic.
- **Rationale**: FR-006 and its clarification require an explicit failure, not a silent
  SQLite fallback, in every non-test environment; extending this to `test` closes the
  loophole the spec explicitly closes.
- **Alternatives considered**: Lazy validation at first query (rejected — later failure,
  worse developer experience); allowing SQLite when `DATABASE_URL` is unset (rejected —
  violates FR-001/003/005/006 directly).

## D4 — Entrypoints default to `config.settings.local`

- **Decision**: `manage.py`, `config/wsgi.py`, and `config/asgi.py` each call
  `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")`.
- **Rationale**: `local` is itself Postgres-only (per D2/D3), so defaulting to it is safe
  — it never silently permits SQLite. k8s and CI always set `DJANGO_SETTINGS_MODULE`
  explicitly anyway (base ConfigMap sets `config.settings.local`; sandbox/production
  overlay to `config.settings.production`), so the default only matters for bare
  host-run commands, where it gives developers a zero-config default without weakening
  the fail-fast guarantee.
- **Alternatives considered**: No default / hard-require the env var (rejected — worse
  local ergonomics for no added safety, since the real risk — SQLite fallback — is
  already closed off by D3); keep defaulting to the legacy `bsbingo.settings` (rejected —
  that module is exactly the SQLite scaffold this feature retires).

## D5 — Local dev selection uses existing mechanisms only

- **Decision**: Local environment selection continues to flow from the base ConfigMap (`DJANGO_SETTINGS_MODULE=config.settings.local` inside the kind/Tilt cluster) and `.envrc` (direnv + 1Password) for `DATABASE_URL`/secrets.
  No new selection mechanism is introduced.
- **Rationale**: The k8s/env-var contract is explicitly out of scope to redesign per the
  spec's framing ("scope the work to Django/PostgreSQL backend wiring and compatibility
  validation, not scaffold creation").
- **Alternatives considered**: A new `ENVIRONMENT`-based switch shim (rejected —
  redundant with what already exists).

## D6 — Test settings wire pytest-django to real PostgreSQL

- **Decision**: Add `[tool.pytest.ini_options]` with `DJANGO_SETTINGS_MODULE = "config.settings.test"` to `backend/pyproject.toml` (the Makefile's existing `--ds=config.settings.test` flag still works and takes precedence when passed).
  CI's `postgres:17` service container supplies `DATABASE_URL`; local test runs require the Tilt-managed `postgres` StatefulSet to be reachable (documented in quickstart.md).
  Django's built-in `test_<db>` creation/teardown is used as-is — no SQLite test runner, no separate ephemeral-Postgres fixture library needed.
- **Rationale**: FR-005 requires PostgreSQL-only test execution; reusing the same
  `DATABASE_URL` parsing path (D1) across CI and local keeps one code path to reason
  about instead of two.
- **Alternatives considered**: SQLite test database (forbidden by spec); a separate
  ephemeral-Postgres test fixture library (unnecessary — CI's service container and the
  local Tilt-managed Postgres already exist).

## D7 — Retire the legacy `bsbingo` settings module as a dedicated refactor step

- **Decision**: In scope for this feature, sequenced as a dedicated step per the
  constitution's refactor-first workflow guidance: (1) migrate all non-DB content from
  `bsbingo/settings.py` into `config/settings/base.py`; (2) create
  `config/{wsgi,asgi,urls}.py` (urls moved from `bsbingo/urls.py`), repoint
  `ROOT_URLCONF`/`WSGI_APPLICATION`; (3) only once the new modules are verified working,
  delete `backend/bsbingo/settings.py`, `bsbingo/wsgi.py`, `bsbingo/asgi.py`,
  `bsbingo/urls.py`, and `db.sqlite3`.
- **Rationale**: Leaving the legacy SQLite settings file in place after this feature
  would directly contradict SC-004 ("No deployment manifests or environment
  configuration continue to rely on SQLite for the default runtime backend") and invite
  accidental use.
- **Alternatives considered**: Keeping the legacy file "deprecated" but present (rejected
  — SC-004 requires it gone, and a dead SQLite config path is a footgun); a minimal
  variant that only adds `config.settings`/`config.asgi` while keeping `bsbingo.urls`/
  `bsbingo.wsgi` (rejected — leaves an inconsistent mix the k8s manifests have already
  resolved toward `config.*`).

## D8 — Migration workflow stays standard; no new migrations authored

- **Decision**: `python manage.py migrate` — already invoked by the `backend-migration` initContainer in `k8s/base/django.yaml`, and runnable locally via `make shell-backend`.
  Only built-in/contrib and `social_django` migrations apply.
  No new migrations are authored as part of this feature; the `bingo` app remains out of `INSTALLED_APPS` and out of scope.
- **Rationale**: FR-004 only requires that existing migration support works against
  PostgreSQL — satisfied by contrib/`social_django` migrations running cleanly.
- **Alternatives considered**: Authoring an initial `bingo` app migration (out of scope
  — belongs to a separate feature).

## D9 — CI/Makefile reconciliation is required to validate this feature

- **Decision**: Flag as a needed follow-up task (for `/speckit-tasks`, not fixed in this planning step): the Makefile's `CI=true` branch of `backend-test` is stale — it references `backend/requirements/{base,production,tests}.txt`, a `scafman/` directory, and `--ds=config.settings.test`, none of which exist in this uv/pyproject-managed repo (leftovers from the `sixfeetup/scaf-fullstack-template` copier scaffold).
  Additionally, `.github/workflows/main.yaml` pins `actions/setup-python` to `"3.10"` while the repo actually requires `3.14` (`.python-version`, `pyproject.toml`).
  Both need fixing for SC-003 (test suite passes with PostgreSQL-backed configuration) to be verifiable in CI at all.
- **Rationale**: Without a working CI test path, this feature's own acceptance criteria
  cannot be automatically validated — this is not optional cleanup, it blocks SC-003.
- **Alternatives considered**: Leaving the CI branch stale / treating it as out of scope
  (rejected — it directly blocks verifying this feature's success criteria).

## D10 — No new runtime dependency

- **Decision**: Add nothing new to `pyproject.toml`. `psycopg[binary,pool]` already
  covers both the DB driver and DSN parsing; `pytest-django`/`hypothesis[django]` are
  already present for testing.
- **Rationale**: Keeps the dependency footprint minimal and favors the constitution's
  preference for functional, in-repo pure logic over adding a config-parsing library.

## Flags recorded for visibility (not fixed as part of this planning step)

- ~~**Duplicate FR-005 numbering** in `spec.md`~~ — **Resolved**: the documentation
  requirement was renumbered to **FR-007** (found and fixed during `/speckit-analyze`).
- **CNPG secret exposes only `host` + `uri`** for sandbox/production, confirming D1's
  premise that Django must not depend on discrete `POSTGRES_*` values in those
  environments.
- **No `Dockerfile`** exists for `./backend` even though CI's `build-backend-image` job and k8s manifests (`image: backend:latest`) expect one.
  This is an adjacent gap that blocks a different CI job (image build), not the Postgres-wiring or test-running paths this feature covers — not scoped into this feature.
- **`/healthz` and `/readiness`** routes are referenced by k8s liveness/readiness probes in `k8s/base/django.yaml` (NULLed out locally) but are not implemented anywhere in Django.
  Out of scope for this feature; a natural follow-up would make `/readiness` perform a DB-connectivity check, but that is an explicit scope decision for a future feature, not this one.
- **CI's `POSTGRES_HOST=postgres`** does not resolve inside the CI service-container topology (where the service is reachable at `localhost`).
  This is harmless once `DATABASE_URL` (which correctly points at `localhost:5432` in CI) is treated as canonical per D1, but is worth noting as an existing CI inconsistency.
- **Documentation tooling mismatch** (constitution mandates Sphinx/MyST; repo uses
  `mkdocs-material`) and **strong-typing CI enforcement** (`pyrefly`/`ty` not yet wired)
  are both pre-existing, repo-wide gaps unrelated to this feature — carried as
  Constitution Check CONCERNNs in `plan.md`, not resolved here.
