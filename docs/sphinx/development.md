<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [PostgreSQL configuration (local development)](#postgresql-configuration-local-development)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# PostgreSQL configuration (local development)

The Django backend runs against PostgreSQL only -- there is no SQLite fallback, even locally.
`tilt up` brings up a `postgres:17` StatefulSet (`k8s/local/postgres.yaml`) alongside the backend, which is configured via `config.settings.local` (`DJANGO_SETTINGS_MODULE` is set to this automatically by the base `app-config` ConfigMap).
The connection details are supplied by the following environment variables, already exported by `.envrc` once you've run `cp -n .envrc.example .envrc` and `direnv allow`:

| Env var | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Yes (canonical) | Full DSN, e.g. `postgresql://bsbingo:<password>@postgres/bsbingo`. |
| `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | No | Only consulted as a fallback if `DATABASE_URL` is unset. |

If PostgreSQL is unreachable or these variables are missing, the app fails fast with an explicit `ImproperlyConfigured` error rather than silently using a local file.

If you have a `backend/db.sqlite3` file left over from before this project moved to PostgreSQL, delete it -- it is no longer used or read by any settings module.
