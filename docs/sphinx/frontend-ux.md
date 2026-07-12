<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Frontend polish & mobile-first UX](#frontend-polish--mobile-first-ux)
  - [What changed](#what-changed)
  - [`frontend/` project layout](#frontend-project-layout)
  - [Known constraints](#known-constraints)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Frontend polish & mobile-first UX

Presentation-layer setup notes for the `bingo` app's polished UX (feature `003-frontend-polish`).
See [`specs/003-frontend-polish/`](../../specs/003-frontend-polish/) for the full spec, UI contract, and task breakdown.
This feature adds no new routes, models, or gameplay rules — see [gameplay](gameplay.md) for those.

## What changed

The four existing screens (create, share, join, board) were restyled with a shared `backend/bingo/static/bingo/css/bingo.css` stylesheet (mobile-first, rounded corners, soft shadows, a visible `:focus-visible` outline on every interactive element) and HTMX attributes for instant tap feedback:

- `hx-indicator`/`hx-disabled-elt="this"` on each board cell apply a pending state
  synchronously on tap, independent of network latency (FR-010, SC-002).
- `hx-swap="outerHTML transition:true"` animates the mark/unmark transition (FR-008).
- Completing a line delivers out-of-band swaps for the *entire* board (not just the
  winning line) plus the winner banner, so every cell becomes read-only the instant
  the game ends (FR-016), with the winning line highlighted via a `data-winning-line`
  attribute.
- The winner overlay dismisses via a pure CSS checkbox/label toggle — no custom JS.
- A light/dark theme toggle button (top-right, every screen) sets `data-theme` on
  `<html>`, overriding the OS's `prefers-color-scheme` default; the choice persists
  in `localStorage`, and a tiny inline boot script in `base.html` applies it before
  first paint to avoid a flash of the wrong theme.

There are two pieces of custom client-side code, both small TypeScript modules with 100% test coverage (`fast-check` property tests), compiled to `frontend/dist/*.js` and served through Django's `STATICFILES_DIRS`:

- `frontend/src/copy-link.ts` — wires the "Copy Link" button to the Clipboard API.
- `frontend/src/theme-toggle.ts` — wires the light/dark toggle button and persists
  the choice.

## `frontend/` project layout

A separate Node project, dev-tooling only (not part of the deployed Django runtime):

```text
frontend/
├── src/copy-link.ts          # the one custom TS module
├── tests/unit/                # fast-check property tests (c8, 100% coverage gate)
├── e2e/                       # Playwright specs, one per user story
│   └── support/
│       ├── game-flow.ts       # createGame()/joinGame() UI-driven helpers
│       └── global-setup.ts    # migrates + seeds buzzwords before the suite runs
└── playwright.config.ts       # mobile + desktop projects; starts the Django dev server
```

Run locally:

```sh
cd frontend
npm install
npm run test:unit   # TypeScript unit/property tests, 100% coverage gate
npm run e2e         # full end-to-end suite (starts its own Django dev server)
```

See [`specs/003-frontend-polish/quickstart.md`](../../specs/003-frontend-polish/quickstart.md) for the complete validation walkthrough, and
[`specs/003-frontend-polish/contracts/ui-contract.md`](../../specs/003-frontend-polish/contracts/ui-contract.md)
for the stable `data-testid` anchors templates and specs both rely on.

## Known constraints

- The active buzzword pool is global (admin-managed), not scoped per game — there is
  no player-facing way to reach the "no buzzwords available" state, so
  `frontend/e2e/dead-ends.spec.ts` drives it via a small `set_buzzwords_active`
  management command instead of the UI, and runs that one scenario on a single
  project to avoid racing the shared pool across parallel projects.
- `npm run e2e`'s `webServer` runs Django with `config.settings.test`, which sets
  `DEBUG=False`; it therefore needs `DJANGO_ALLOWED_HOSTS` set and `runserver
  --insecure` to serve static files at all (both already wired into
  `playwright.config.ts`).
