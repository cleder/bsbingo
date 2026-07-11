<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Data Model: Django project with PostgreSQL backend](#data-model-django-project-with-postgresql-backend)
  - [Entity 1: Database Configuration](#entity-1-database-configuration)
  - [Entity 2: Migration Workflow](#entity-2-migration-workflow)
  - [Entity 3: Developer Environment](#entity-3-developer-environment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Data Model: Django project with PostgreSQL backend

**Feature**: `001-django-postgresql-backend` | **Date**: 2026-07-11

The spec's Key Entities for this feature are configuration and process concepts, not Django ORM models — this feature adds no new database tables.
They are represented below as schema/process tables instead of field/relationship entity diagrams.

## Entity 1: Database Configuration

Environment-variable contract consumed by `config.settings.base` (see D1/D3 in `research.md`).
This contract is already fixed by existing k8s manifests and CI — this feature makes Django settings consume it, not redesign it.

| Env var | Required | Consumed by | Source (local / CI / sandbox-prod) | Example |
|---|---|---|---|---|
| `DATABASE_URL` | Yes (canonical) | `config.settings.base` DSN parser | `secrets-config` Secret (local) / job env (CI) / CloudNativePG `postgres-app` secret key `uri` (sandbox/prod) | `postgresql://bsbingo:***@postgres/bsbingo` |
| `POSTGRES_HOST` | No (fallback; also used by `pg_isready` initContainer) | parser fallback; k8s initContainer probe | literal `postgres` (local/CI) / CloudNativePG `postgres-app` secret key `host` (sandbox/prod) | `postgres` |
| `POSTGRES_PORT` | No (defaults to 5432) | parser fallback | CI job env only; implicit elsewhere | `5432` |
| `POSTGRES_DB` | No (fallback) | parser fallback | `app-config` ConfigMap | `bsbingo` |
| `POSTGRES_USER` | No (fallback) | parser fallback | `app-config` ConfigMap | `bsbingo` |
| `POSTGRES_PASSWORD` | No (fallback) | parser fallback | `secrets-config` Secret (local) / CI job env | (generated) |
| `DJANGO_SECRET_KEY` | Yes | `config.settings.base` `SECRET_KEY` | `secrets-config` Secret / generated | (generated) |
| `DJANGO_SETTINGS_MODULE` | Yes (defaults to `config.settings.local` at the entrypoints) | `manage.py`, `config/wsgi.py`, `config/asgi.py` | `app-config` ConfigMap (`config.settings.local` base value; sandbox/prod overlay to `config.settings.production`) | `config.settings.production` |

**Validation rules**:

- At least one of `DATABASE_URL` or a complete discrete `POSTGRES_*` set MUST be present
  and parseable at settings-import time, in every environment including `test` — else
  `django.core.exceptions.ImproperlyConfigured` is raised immediately (D3).
- `DATABASES["default"]["ENGINE"]` is always `django.db.backends.postgresql` — there is
  no code path that produces `django.db.backends.sqlite3`.

## Entity 2: Migration Workflow

| Trigger | Command | Runner | Success signal |
|---|---|---|---|
| Deploy (sandbox/production) | `python manage.py migrate` | `backend-migration` initContainer (`k8s/base/django.yaml`), runs after `check-db-ready` (`pg_isready`) | Pod's main container starts; schema present in the CloudNativePG-managed database |
| Local development | `python manage.py migrate` | Run manually via `make shell-backend` (execs into the running backend pod) | Command exits 0; schema present in the local `postgres` StatefulSet's database |
| CI test run | Implicit — `pytest-django` creates/migrates `test_bsbingo` automatically | `pytest --ds=config.settings.test` against the `postgres:17` CI service container | Test session starts without migration errors |

No new schema artifacts are introduced by this feature — only contrib (`admin`, `auth`, `sessions`, etc.) and `social_django` migrations apply, since the `bingo` app remains out of `INSTALLED_APPS` (D8).

## Entity 3: Developer Environment

| Prerequisite | Step | Produces |
|---|---|---|
| `kind`, `kubectl`, `tilt`, `uv` installed | `make setup` | Local `kind` cluster context |
| `.envrc` present (`cp -n .envrc.example .envrc`), `direnv` + 1Password configured | `direnv allow` | `DATABASE_URL`, `POSTGRES_*`, `DJANGO_SECRET_KEY` exported into the shell |
| Cluster context ready | `tilt up` | Cluster running, including the `postgres:17` StatefulSet (`k8s/local/postgres.yaml`) and the backend Deployment pointed at `config.settings.local` |
| Cluster running | `make shell-backend` → `python manage.py migrate` / `createsuperuser` | Schema applied to the local PostgreSQL instance; admin user available |

This maps directly to SC-002 ("no more than two manual setup steps beyond installing dependencies"): `direnv allow` and `tilt up` are the two manual steps once prerequisites (`make setup`, dependency installs) are done.
