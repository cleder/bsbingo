<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Contract: Database Configuration Env Vars](#contract-database-configuration-env-vars)
  - [Interface](#interface)
  - [Out of scope for this contract](#out-of-scope-for-this-contract)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contract: Database Configuration Env Vars

**Feature**: `001-django-postgresql-backend`

This feature introduces no new HTTP/API endpoints — it is purely infrastructure/config wiring, so no OpenAPI-style contract applies.
The one genuine external interface this feature owns is the environment-variable contract between the existing Kubernetes manifests / CI configuration and Django settings.
That contract is documented here as the stable "API" this feature must honor without breaking either side.

This contract is **consumed, not designed, by this feature** — the env var names and sources already exist in `k8s/base/app.configmap.yaml`, `k8s/local/secrets.yaml`, `k8s/sandbox/postgres.cnpg.yaml`, and `.github/workflows/main.yaml`.
See [data-model.md](../data-model.md) Entity 1 for the full table with sources and examples.

## Interface

Django settings (`config.settings.base`, imported by every leaf: `local`/`production`/ `test`) MUST:

1. Read `DATABASE_URL` as the canonical connection string when present, and build
   `DATABASES["default"]` from it with `ENGINE=django.db.backends.postgresql`.
2. Fall back to discrete `POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_DB`/`POSTGRES_USER`/
   `POSTGRES_PASSWORD` only when `DATABASE_URL` is absent (local-dev convenience path).
3. Raise `django.core.exceptions.ImproperlyConfigured` at settings-import time — in every environment, including `test` — if neither source yields a complete, parseable PostgreSQL configuration.
   No code path may produce `ENGINE=django.db.backends.sqlite3`.
4. Never require k8s manifests, Secrets, or CI workflow files to add new env vars beyond
   what's listed in `data-model.md` Entity 1 — any new requirement discovered during
   implementation must be treated as a change to this contract, not a silent addition.

## Out of scope for this contract

- `/healthz` and `/readiness` HTTP endpoints — referenced by k8s probes but not yet implemented in Django.
  A future feature may extend this contract to include a DB-connectivity check on `/readiness`; not part of this feature.
- Any Dockerfile / image-build contract — `./backend` has no Dockerfile yet; unrelated to
  database configuration.
