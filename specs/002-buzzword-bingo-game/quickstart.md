<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Quickstart: Validating the Buzzword Bingo Game](#quickstart-validating-the-buzzword-bingo-game)
  - [Prerequisites](#prerequisites)
  - [Scenario A: Create a game and share it — US1 / SC-001](#scenario-a-create-a-game-and-share-it--us1--sc-001)
  - [Scenario B: Join a game and receive a personal board — US2 / SC-002](#scenario-b-join-a-game-and-receive-a-personal-board--us2--sc-002)
  - [Scenario C: Play a board to bingo and see the winner — US3 / SC-003/SC-005](#scenario-c-play-a-board-to-bingo-and-see-the-winner--us3--sc-003sc-005)
  - [Scenario D: Manage buzzwords through Django admin — US4 / SC-007](#scenario-d-manage-buzzwords-through-django-admin--us4--sc-007)
  - [Scenario E: Insufficient buzzword pool — Edge Case / FR-016](#scenario-e-insufficient-buzzword-pool--edge-case--fr-016)
  - [Open items to confirm during `/speckit-tasks`](#open-items-to-confirm-during-speckit-tasks)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Quickstart: Validating the Buzzword Bingo Game

**Feature**: `002-buzzword-bingo-game`

These scenarios validate the feature end-to-end once implemented.
They reuse the local dev workflow established by `001-django-postgresql-backend` (`make setup`, `direnv allow`, `tilt up`, `make shell-backend`).
See [data-model.md](./data-model.md) for the schema and [contracts/](./contracts/) for the endpoint/admin interfaces this must honor.

## Prerequisites

- Local dev environment running per `001-django-postgresql-backend`'s quickstart (PostgreSQL reachable, migrations applied).
- At least 25 active `Buzzword` rows seeded (via Django admin or `manage.py shell`) — required before any game can be joined (FR-016).
- A Django admin/staff superuser (`python manage.py createsuperuser`) to manage buzzwords.

## Scenario A: Create a game and share it — US1 / SC-001

- Visit `/` and submit a game name (e.g. "Sprint Planning").
- **Expected**: A new `Game` is created with `status=active`; the page shows a shareable join URL `/game/<uuid>/join/` (FR-001/FR-002).
  Total time from form load to seeing the link: under 1 minute (SC-001).
- Submit the form again with a blank name.
- **Expected**: The form re-renders with a validation error; no second `Game` is created (per the spec's clarification on blank required fields).

## Scenario B: Join a game and receive a personal board — US2 / SC-002

- Open the join URL from Scenario A in two different browser sessions, submitting two different participant names (one of them reusing the same name twice is also valid — FR-004).
- **Expected**: Each submission creates its own `Player` and `Board` with 25 `BoardSquare`s (FR-006/FR-007), redirecting to a distinct `/board/<uuid>/` URL each time, in under 10 seconds (SC-002).
  The two boards' non-center squares are not required to be identical in arrangement (SC-006).
- Attempt to join with a blank display name.
- **Expected**: The join form re-renders with a validation error; no `Player`/`Board` is created.

## Scenario C: Play a board to bingo and see the winner — US3 / SC-003/SC-005

- On one player's board, click squares (HTMX `POST` to the toggle endpoint) to complete an entire row, column, or diagonal.
- **Expected**: Each click updates only the clicked square without a full page reload; upon the line-completing click, the game transitions to `finished`, and a winner banner fragment is delivered in the same response (no refresh needed) (FR-008/FR-009/FR-010, SC-003).
- From a second player's board in the same now-finished game, attempt to toggle a square.
- **Expected**: The request is rejected; that board's state is unchanged (FR-011, SC-005).
- Attempt to `POST` a toggle for a `cell_id` that doesn't belong to that `board_id` (or doesn't exist at all).
- **Expected**: `404` (FR-013, SC-005).

## Scenario D: Manage buzzwords through Django admin — US4 / SC-007

- Log into `/admin/` as a staff user.
- Add a new `Buzzword`; deactivate an existing one.
- **Expected**: Completing add/edit/deactivate takes under 30 seconds each (SC-007); a board generated *after* deactivation never includes the deactivated word, while boards generated *before* deactivation are unaffected (FR-014).
- Open the `Game`/`Player` admin views for the finished game from Scenario C.
- **Expected**: The game's `status=finished` and `winner` are visible (FR-015).

## Scenario E: Insufficient buzzword pool — Edge Case / FR-016

- Deactivate buzzwords until fewer than 25 remain active.
- Attempt to join an active game.
- **Expected**: The join attempt is declined with an explanatory message; no `Player`/`Board`/`BoardSquare` is created ([research.md](./research.md) D3).

## Open items to confirm during `/speckit-tasks`

- Exact copy/wording for the "game finished" and "insufficient buzzwords" user-facing messages (a content detail, not a functional gap).
- Whether a lightweight load-test script is added to mechanically verify SC-004 (100 concurrent participants, <500ms per toggle), or whether that's validated manually/via a follow-up feature.
