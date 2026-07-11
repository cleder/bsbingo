<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Quickstart: Validating the PostgreSQL backend](#quickstart-validating-the-postgresql-backend)
  - [Prerequisites](#prerequisites)
  - [Scenario A: Production settings connect and migrate — US1 / SC-001](#scenario-a-production-settings-connect-and-migrate--us1--sc-001)
  - [Scenario B: Local developer workflow — US2 / SC-002](#scenario-b-local-developer-workflow--us2--sc-002)
  - [Scenario C: Test suite runs against PostgreSQL only — US3 / SC-003](#scenario-c-test-suite-runs-against-postgresql-only--us3--sc-003)
  - [Scenario D: Fail-fast behavior — edge cases / FR-006](#scenario-d-fail-fast-behavior--edge-cases--fr-006)
  - [Open items to confirm during `/speckit-tasks`](#open-items-to-confirm-during-speckit-tasks)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Quickstart: Validating the PostgreSQL backend

**Feature**: `001-django-postgresql-backend`

These scenarios validate the feature end-to-end once implemented.
They reuse existing Makefile/Tiltfile entrypoints rather than inventing new commands.
See [data-model.md](./data-model.md) for the full env-var contract and [contracts/database-config.md](./contracts/database-config.md) for the interface this must honor.

## Prerequisites

- `kind`, `kubectl`, `tilt`, `uv` installed
- `.envrc` configured from `.envrc.example` (direnv + 1Password) for local scenarios
- Repo dependencies installed (`uv sync` / `make setup`)

## Scenario A: Production settings connect and migrate — US1 / SC-001

- Set `DJANGO_SETTINGS_MODULE=config.settings.production` with a valid `DATABASE_URL`
  pointing at a reachable PostgreSQL instance.
- Run `python manage.py migrate` from `backend/`.
- **Expected**: `DATABASES["default"]["ENGINE"]` is `django.db.backends.postgresql`;
  migrations apply successfully; no `db.sqlite3` file is created; total time under 10
  minutes (SC-001).
- Optional: `python manage.py check --deploy` to confirm production hardening.

## Scenario B: Local developer workflow — US2 / SC-002

- `make setup` — provisions the local `kind` cluster context.
- `direnv allow` — exports `DATABASE_URL`, `POSTGRES_*`, `DJANGO_SECRET_KEY`.
- `tilt up` — brings up the cluster, including the `postgres:17` StatefulSet and the
  backend Deployment running under `config.settings.local`.
- `make shell-backend` → `python manage.py migrate` (and `createsuperuser` if needed).
- **Expected**: the app connects to PostgreSQL, not SQLite; no more than the two manual
  steps above (`direnv allow`, `tilt up`) were needed beyond installing dependencies
  (SC-002).

## Scenario C: Test suite runs against PostgreSQL only — US3 / SC-003

- CI: the `postgres:17` job service container is already configured
  (`.github/workflows/main.yaml`); run `CI=true make backend-test`.
- Locally: with the Tilt-managed `postgres` service reachable, run `make backend-test`
  (equivalently `pytest --ds=config.settings.test` from `backend/`).
- **Expected**: all tests pass against a real PostgreSQL test database
  (`test_bsbingo`); no SQLite is used at any point; include at least one
  `hypothesis`-based property test of the `DATABASE_URL` parser and one assertion that
  `settings.DATABASES["default"]["ENGINE"].endswith("postgresql")`.

## Scenario D: Fail-fast behavior — edge cases / FR-006

- Unset `DATABASE_URL` and all `POSTGRES_*` env vars, then attempt to import Django settings (e.g. `python manage.py check`).
  **Expected**: `django.core.exceptions.ImproperlyConfigured` is raised immediately, naming the missing variable(s) — the process does not silently fall back to SQLite.
- Set `DATABASE_URL` to an unreachable host, then run `python manage.py migrate`.
  **Expected**: a psycopg `OperationalError` surfaces promptly (no silent hang, no SQLite fallback).
- Across all four scenarios above: confirm `db.sqlite3` is never created anywhere in `backend/`.

## Open items to confirm during `/speckit-tasks`

- Is `make backend-test` the intended command for a host-run (non-in-cluster) developer,
  or is all local test execution expected to happen via `kubectl exec`/`make
  shell-backend`?
- Is `make shell-backend` the sole supported way to run `manage.py` commands locally, or
  should a host-run dev mode also be supported (affects whether `manage.py`'s default
  `DJANGO_SETTINGS_MODULE` matters for anyone besides CI)?
- Confirm whether `tilt up` alone brings up a fully migrated, ready-to-use local
  environment, or whether an explicit first-time `migrate`/`createsuperuser` step must be
  documented as part of onboarding.
