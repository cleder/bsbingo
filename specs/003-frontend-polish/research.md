<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Phase 0 Research: Frontend Polish & Mobile-First UX](#phase-0-research-frontend-polish--mobile-first-ux)
  - [Decision: How Playwright and the one TypeScript module are hosted](#decision-how-playwright-and-the-one-typescript-module-are-hosted)
  - [Decision: Serving the compiled TypeScript to the browser](#decision-serving-the-compiled-typescript-to-the-browser)
  - [Decision: Running Playwright against a live Django server](#decision-running-playwright-against-a-live-django-server)
  - [Decision: Mobile + desktop coverage in Playwright](#decision-mobile--desktop-coverage-in-playwright)
  - [Non-decisions (explicitly out of scope for this research)](#non-decisions-explicitly-out-of-scope-for-this-research)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Phase 0 Research: Frontend Polish & Mobile-First UX

No `NEEDS CLARIFICATION` markers remained in the Technical Context after `/speckit-clarify` — all three clarifications raised there (SC-005's completion status, double-tap handling, winner-overlay dismissal) were already folded into `spec.md`.
This document instead records the technical decisions needed to turn that spec into a buildable plan.

## Decision: How Playwright and the one TypeScript module are hosted

- **Decision**: Add a single new `frontend/` directory at the repo root as a plain Node/TypeScript project (`package.json`, `tsconfig.json`, `playwright.config.ts`).
  It holds exactly two things: the one custom TS module (`src/copy-link.ts`) the constitution permits, and all Playwright artifacts (`e2e/` browser specs, `tests/unit/` fast-check specs for the module).
  It has no bundler, no page-rendering framework, and produces no HTML — Django keeps rendering every page.
- **Rationale**: The constitution mandates "Frontend uses playwright with fast-check" and permits custom TypeScript "if custom code has to be written for the frontend," but also forbids introducing any other JS framework/library.
  A minimal Node project satisfies both: it's the natural home for `@playwright/test` (which is a Node-only tool) and keeps the TS module's tests colocated with the tool the constitution says to test it with, without pulling a framework into the pages themselves.
  The repo's `Makefile` already has (unused) `compile-frontend`/`init-frontend-dependencies` targets that reference a `frontend/package.json`, left over from the project's copier scaffold (`copier__create_nextjs_frontend: false`) — this plan reuses that expected location rather than inventing a new one.
- **Alternatives considered**:
  - *Author the TS module inside `backend/bingo/static/` and test it with a browser-only Playwright component test*: rejected — Playwright component testing needs a supported framework adapter and adds machinery for a single function; a plain Node unit test is simpler and still uses `@playwright/test` as the runner.
  - *Use Vitest/Jest for the module's unit tests instead of `@playwright/test`*: rejected — the constitution names Playwright specifically as the test tool; introducing a second JS test runner adds a dependency the constitution doesn't call for.
  - *Skip TypeScript and inline a `<script>` in `base.html`*: rejected — the constitution requires custom frontend code to be TypeScript with 100% test coverage; an inline untyped script can't be unit-tested or type-checked.

**Correction (found by `/speckit-analyze`, finding D1)**: the constitution's "100% test coverage required for custom TypeScript" is a measured, enforced number, not just "tests exist." `frontend/package.json`'s `test:unit` script MUST run under a coverage tool (`c8`, instrumenting `frontend/src/**`) configured to fail below 100% line/branch/function coverage, and CI (tasks.md T035) MUST run that script as part of the gate — see tasks.md T001a.

## Decision: Serving the compiled TypeScript to the browser

- **Decision**: `tsc` compiles `frontend/src/copy-link.ts` to `frontend/dist/copy-link.js` (plain ES module, no bundler needed for one file).
  Django's `STATICFILES_DIRS` (in `config/settings/base.py`) gains an entry pointing at `frontend/dist/`, so `{% static "copy-link.js" %}` serves the compiled file directly — no build artifact is checked into `backend/`, and no duplication between "source of truth" and "what ships."
- **Rationale**: Keeps the TypeScript source and its tests in one place (`frontend/`) while letting Django's existing static-file pipeline (already used for nothing yet, since 002 shipped no static assets) serve the output unmodified.
  Avoids inventing a second static-asset pipeline or a copy-on-build step that could drift.
- **Alternatives considered**:
  - *Check the compiled `.js` into `backend/bingo/static/bingo/js/`*: rejected — creates a generated file that must be manually kept in sync with the TS source, inviting drift.
  - *Serve the `.ts` file directly and rely on browser-native TS execution*: rejected — no evergreen browser executes TypeScript directly; a compile step is unavoidable.

## Decision: Running Playwright against a live Django server

- **Decision**: `playwright.config.ts`'s `webServer` option starts the Django dev server (`uv run backend/manage.py runserver`) against `config.settings.test` (SQLite/lightweight settings already used by the pytest suite, per `pyproject.toml`'s `DJANGO_SETTINGS_MODULE = "config.settings.test"`), with a `baseURL` matching that server.
  Each e2e spec creates its own game/board through the real UI (no direct DB fixtures), matching how a real user would reach that state, per Independent Test descriptions in the spec.
- **Correction (found by `/speckit-analyze`, finding F1)**: `config.settings.test` sets `DEBUG = False`.
  Django only auto-allows `localhost`/`127.0.0.1` when `DEBUG = True`; with `DEBUG = False` and `ALLOWED_HOSTS` empty by default (`base.py`), every request from Playwright would be rejected with `DisallowedHost`.
  Existing pytest-django tests never hit this because Django's in-process test client patches `ALLOWED_HOSTS` to include `'testserver'` — a real `runserver` process gets no such patch.
  The `webServer` command MUST therefore also set `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` in its environment (see tasks.md T003/T035).
- **Rationale**: Reusing the existing `config.settings.test` settings module means the e2e suite needs no new settings file and no production-like database dependency (Postgres) to run locally or in CI.
  Driving state through the UI (rather than seeding via the ORM) keeps every e2e spec an honest end-to-end check of the exact flows FR-020/SC-007 require.
- **Alternatives considered**:
  - *Point Playwright at the same Postgres service CI already runs for `backend-test`*: deferred, not rejected — acceptable as a later CI hardening step if `config.settings.test`'s SQLite backing ever diverges meaningfully from Postgres behavior for this feature's purposes; not needed for the UI-only changes in this feature.
  - *Mock the backend entirely (e.g., a static HTML fixture server)*: rejected — would not exercise the real HTMX round-trips this feature depends on (FR-008, FR-010, FR-015).

## Decision: Mobile + desktop coverage in Playwright

- **Decision**: `playwright.config.ts` defines two projects: a mobile viewport (Playwright's built-in `Pixel 7` or similar device descriptor, ≤430px per SC-004) and a desktop Chromium viewport at the design's max board width.
  All four `e2e/` spec files run under both projects.
- **Rationale**: SC-004 explicitly calls out the 320-430px mobile range and the desktop max-width behavior; running the same specs under both projects is the direct automated check for "the board remains fully usable... across representative mobile widths... and on desktop."
- **Alternatives considered**: *Single desktop-only project with manual mobile spot-checks*: rejected — mobile is the primary target per the spec's Design Principles ("Mobile First"), so it must be part of the automated gate (FR-020), not a manual afterthought.

## Non-decisions (explicitly out of scope for this research)

- Visual design tokens (exact color palette, font family) are an implementation detail for the CSS itself, not a planning-level decision — left to the implementation/tasks phase.
- SC-005 (human usability observation) requires no tooling decision here — per the `/speckit-clarify` resolution, it is a directional goal, not part of this feature's automated completion gate.
