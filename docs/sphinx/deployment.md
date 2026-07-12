<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [PostgreSQL configuration (production)](#postgresql-configuration-production)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# PostgreSQL configuration (production)

The Django backend uses PostgreSQL as its only database backend in every non-test environment (`config.settings.production`, selected via the `DJANGO_SETTINGS_MODULE` env var).
There is no SQLite fallback: if PostgreSQL is missing or misconfigured, the application fails fast with an explicit `django.core.exceptions.ImproperlyConfigured` error at startup rather than silently falling back to a local file-based database.

Sandbox and production get their database connection from the [CloudNativePG](https://cloudnative-pg.io/)-managed cluster (`k8s/sandbox/postgres.cnpg.yaml`), via the auto-generated `postgres-app` Secret.
The following environment variables are consumed by `config.settings.base`:

| Env var | Required | Source | Notes |
|---|---|---|---|
| `DATABASE_URL` | Yes (canonical) | `postgres-app` Secret key `uri` | Full DSN; always present in sandbox/production, so this is the source Django actually relies on there. |
| `POSTGRES_HOST` | No (fallback) | `postgres-app` Secret key `host` | Only used as a fallback if `DATABASE_URL` is absent; also used by the `check-db-ready` initContainer's `pg_isready` probe. |
| `POSTGRES_PORT` | No (fallback, defaults to 5432) | — | |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | No (fallback) | `app-config` ConfigMap / `secrets-config` Secret | Discrete connection pieces; not required when `DATABASE_URL` is present. |
| `DJANGO_SECRET_KEY` | Yes | `secrets-config` Secret | |
| `DJANGO_SETTINGS_MODULE` | Yes | `app-config` ConfigMap (`config.settings.production` in the sandbox/production overlay) | |

Migrations run automatically via the `backend-migration` initContainer (`python manage.py migrate`) after the `check-db-ready` initContainer confirms PostgreSQL is reachable.
No manual migration step is required for a standard deploy.

To run a migration manually (e.g. for debugging), exec into a running backend pod and run:

```sh
python manage.py migrate
```
