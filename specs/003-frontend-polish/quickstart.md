<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Quickstart: Validating Frontend Polish & Mobile-First UX](#quickstart-validating-frontend-polish--mobile-first-ux)
  - [1. Backend regression (unchanged behavior)](#1-backend-regression-unchanged-behavior)
  - [2. TypeScript module: unit/property tests](#2-typescript-module-unitproperty-tests)
  - [3. End-to-end validation (the completion gate — FR-020/SC-007)](#3-end-to-end-validation-the-completion-gate--fr-020sc-007)
  - [4. Manual sanity pass (optional, not a completion gate)](#4-manual-sanity-pass-optional-not-a-completion-gate)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Quickstart: Validating Frontend Polish & Mobile-First UX

Prerequisites: this feature builds on `002-buzzword-bingo-game`, already runnable per that feature's own quickstart.
The steps below additionally assume the `frontend/` Node project described in `plan.md`/`research.md` exists (Node LTS + `npm install` run once inside `frontend/`).

## 1. Backend regression (unchanged behavior)

```sh
uv run pytest
```

Expected: existing `tests/unit/test_domain.py` and `tests/integration/test_bingo_views.py` still pass unmodified — this feature does not change win detection, board generation, or route behavior, only presentation.

## 2. TypeScript module: unit/property tests

```sh
cd frontend
npm run test:unit   # runs tests/unit/copy-link.spec.ts under @playwright/test, using fast-check
```

Expected: `copy-link.ts`'s clipboard-write behavior passes its fast-check property tests (arbitrary non-empty link strings round-trip through the mocked `navigator.clipboard.writeText`), and its typecheck (`tsc --noEmit`) is clean under `"strict": true`.

## 3. End-to-end validation (the completion gate — FR-020/SC-007)

```sh
cd frontend
npm run e2e   # playwright test; starts the Django dev server per playwright.config.ts's webServer
```

This runs all four spec files against both the mobile and desktop Playwright projects (research.md).
Each corresponds directly to one prioritized user story:

| Spec | Validates | Spec section |
|---|---|---|
| `e2e/create-and-share.spec.ts` | Autofocus, Enter-to-submit, inline validation, share-link + working "Copy Link" | User Story 1 |
| `e2e/join.spec.ts` | Autofocus, Enter-to-submit, inline validation, landing on own board | User Story 2 |
| `e2e/play-and-win.spec.ts` | Instant tap feedback, mark/unmark animation, free-space non-interactivity, double-tap absorption, winning overlay + line highlight, overlay dismissal to a read-only board | User Story 3 |
| `e2e/dead-ends.spec.ts` | Finished-game notice for non-winners, join-a-finished-game message, no-buzzwords message, not-found message | User Story 4 |

Expected: all specs pass on both projects.
A failing spec here means a corresponding Acceptance Scenario in `spec.md` is not yet satisfied — this suite is the feature's own definition of done (FR-020), separate from and prerequisite to `SC-005`'s directional human-usability goal (which this suite does not and cannot check — see Clarifications).

## 4. Manual sanity pass (optional, not a completion gate)

1. `uv run backend/manage.py runserver`
2. Open the home page on an actual phone (or a narrow emulated viewport, ≥320px) — confirm the create-game field is focused, the layout fits one-handed, and touch targets feel comfortably tappable.
3. Create a game, tap "Copy Link", paste it in a new tab, join with a name, and mark squares until a bingo — confirm the celebratory overlay and highlighted line appear, then dismiss it and confirm the board underneath is read-only with the line still highlighted.
4. Open the same game's join link in a third tab after it has finished — confirm the "already finished" message appears instead of a join form.

This manual pass is a sanity check for genuinely subjective feel (does it *feel* fast and fun); it does not replace the automated suite in step 3 as the completion gate.
