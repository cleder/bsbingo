<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Contracts: Routes Affected by Buzzword Categories](#contracts-routes-affected-by-buzzword-categories)
  - [Unchanged route, changed behavior: `GET/POST /` (`bingo:create_game`)](#unchanged-route-changed-behavior-getpost--bingocreate_game)
  - [Unchanged route, changed data source: `GET/POST /game/<uuid:game_id>/join/` (`bingo:join_game`)](#unchanged-route-changed-data-source-getpost-gameuuidgame_idjoin-bingojoin_game)
  - [Unchanged routes](#unchanged-routes)
  - [Admin-only surface (no new routes, Django admin only)](#admin-only-surface-no-new-routes-django-admin-only)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contracts: Routes Affected by Buzzword Categories

This feature is server-rendered (Django + HTMX), not a JSON API — "contracts" here describe the HTTP routes/fragments affected, mirroring how `002-buzzword-bingo-game` documented its endpoints.

## Unchanged route, changed behavior: `GET/POST /` (`bingo:create_game`)

- **GET**: now renders the category checklist (all active `Category` rows) alongside the game-name field.
  The buzzword checklist section is initially empty/unfiltered pending a category selection, or shows all active buzzwords if categories are optional to skip (FR-008).
- **New partial**: `POST /game/create/buzzwords/` (HTMX fragment endpoint) — accepts selected category IDs, returns the `partials/_buzzword_choices.html` fragment listing active buzzwords tagged with at least one selected category (FR-007), or all active buzzwords if no category is selected (FR-008).
- **POST** (final submit): now requires both `name` and at least one selected buzzword ID (`buzzword_pool`).
  Validation failure (zero buzzwords selected) redisplays the form with a validation error (FR-012) instead of creating the `Game`.
  On success, creates the `Game` row and populates `Game.buzzword_pool` from the selection, same response shape as today (share screen with join link).

## Unchanged route, changed data source: `GET/POST /game/<uuid:game_id>/join/` (`bingo:join_game`)

- Behavior and template are otherwise unchanged.
  The only change is the board-generation pool source: `game.buzzword_pool.filter(active=True)` instead of `Buzzword.objects.filter(active=True)` (see [data-model.md](../data-model.md)).
  The existing `insufficient_pool` error path is unchanged and now scoped per-game.

## Unchanged routes

- `GET /board/<uuid:board_id>/` (`bingo:view_board`) — no change.
- `POST /board/<uuid:board_id>/cell/<uuid:cell_id>/toggle/` (`bingo:toggle_cell`) — no change.

## Admin-only surface (no new routes, Django admin only)

- `Category` gains a standard `ModelAdmin` registration (list/search/filter by `active`, actions to bulk activate/deactivate — mirrors `BuzzwordAdmin`'s `make_active`/`make_inactive` actions).
  Hard delete is disabled (`has_delete_permission` returns `False`, delete action excluded) — deactivation is the only removal path (FR-003/FR-010, research.md Decision R6).
- `BuzzwordAdmin`'s change form gains a `categories` field (required, `filter_horizontal` widget) and a `list_filter` entry for `categories`.
