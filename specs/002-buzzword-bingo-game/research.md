<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Research: Buzzword Bingo Game](#research-buzzword-bingo-game)
  - [D1 — Capability URLs via UUID primary keys, not a separate token field](#d1--capability-urls-via-uuid-primary-keys-not-a-separate-token-field)
  - [D2 — `Buzzword` gets a database-level uniqueness constraint on `text`](#d2--buzzword-gets-a-database-level-uniqueness-constraint-on-text)
  - [D3 — Board generation: reject, don't degrade, when the active pool is too small](#d3--board-generation-reject-dont-degrade-when-the-active-pool-is-too-small)
  - [D4 — Win detection: precomputed line sets over a `frozenset[int]` of marked positions](#d4--win-detection-precomputed-line-sets-over-a-frozensetint-of-marked-positions)
  - [D5 — Center square is a non-toggleable free space, always marked](#d5--center-square-is-a-non-toggleable-free-space-always-marked)
  - [D6 — Exactly one winner race handled with a single conditional UPDATE, not row locking](#d6--exactly-one-winner-race-handled-with-a-single-conditional-update-not-row-locking)
  - [D7 — HTMX wiring: enable `django-htmx`, return partials with an out-of-band winner fragment](#d7--htmx-wiring-enable-django-htmx-return-partials-with-an-out-of-band-winner-fragment)
  - [D8 — No denormalized "marked count" or bitmask field on `Board`](#d8--no-denormalized-marked-count-or-bitmask-field-on-board)
  - [D9 — Admin registrations mirror the spec's four manageable entities plus `Board` for inspection](#d9--admin-registrations-mirror-the-specs-four-manageable-entities-plus-board-for-inspection)
  - [Flags recorded for visibility (not fixed as part of this planning step)](#flags-recorded-for-visibility-not-fixed-as-part-of-this-planning-step)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Research: Buzzword Bingo Game

**Feature**: `002-buzzword-bingo-game` | **Date**: 2026-07-12

This document resolves the design decisions for the core gameplay feature, grounded in the existing repo state: an empty `bingo` app stub (not yet in `INSTALLED_APPS`), the PostgreSQL backend already wired by `001-django-postgresql-backend`, and `django-htmx` already a declared dependency but not yet wired into settings.

## D1 — Capability URLs via UUID primary keys, not a separate token field

- **Decision**: `Game`, `Player`, `Board`, and `BoardSquare` use `UUIDField(primary_key=True, default=uuid4, editable=False)`.
  The Board's UUID *is* its capability URL (`/board/<uuid:board_id>/`); there is no separate "access token" field.
- **Rationale**: The spec's Key Entities describe each of these as "identified by an unguessable link" — using the primary key directly avoids a redundant token column and keeps lookups a single indexed `WHERE id = %s`, matching the URL structure in the source doc (`/board/<board_uuid>/`, `/game/<game_uuid>/join/`).
- **Alternatives considered**: Auto-incrementing integer PK plus a separate random `token` field (rejected — two columns to keep in sync, and sequential integer PKs would leak game/board counts if ever exposed); `secrets.token_urlsafe` opaque strings instead of UUID (rejected — UUID has native Postgres/Django support and a matching URL path converter, no extra validation code needed).

## D2 — `Buzzword` gets a database-level uniqueness constraint on `text`

- **Decision**: `Buzzword.text` is `unique=True`.
- **Rationale**: The spec only requires "no duplicate buzzword on the same board" (FR-006), but a global uniqueness constraint on the pool trivially guarantees that property (selecting *N* distinct `Buzzword` rows can never yield a duplicate word) and prevents administrators from accidentally creating near-duplicate pool entries.
- **Alternatives considered**: No uniqueness constraint, enforcing no-duplicates only at board-generation time via `random.sample` over distinct rows (rejected — still correct, but leaves a data-quality gap in the admin-managed pool that a unique constraint closes automatically).

## D3 — Board generation: reject, don't degrade, when the active pool is too small

- **Decision**: A pure function `select_random_words(pool: Sequence[BuzzwordId], k: int, rng: Random) -> list[BuzzwordId]` raises `InsufficientBuzzwordPoolError` (a small domain exception) when `len(pool) < k`.
  The join view catches this and re-renders the join form with a validation error instead of creating a `Player`/`Board` (per the spec's Assumptions section and FR-016).
- **Rationale**: Keeps the "not enough active buzzwords" business rule inside the pure, hypothesis-testable domain function rather than scattered as a view-level `if` check; the view only needs to translate the exception into a user-facing message.
- **Alternatives considered**: Checking `Buzzword.objects.filter(active=True).count() >= 25` directly in the view before calling the domain function (rejected — duplicates the invariant in two places and is harder to property-test in isolation).

## D4 — Win detection: precomputed line sets over a `frozenset[int]` of marked positions

- **Decision**: `domain.py` defines `WINNING_LINES: Final[tuple[frozenset[int], ...]]` — the 5 rows, 5 columns, and 2 diagonals of a 5×5 grid, each as a `frozenset[int]` of positions 0–24, computed once at import time. `has_bingo(marked: frozenset[int]) -> bool` returns `any(line <= marked for line in WINNING_LINES)`.
- **Rationale**: A pure function over an immutable set is trivially hypothesis-testable (e.g., "any full line ⇒ True", "fewer than 24 marked positions can still win only if they form a complete line") and needs no Django/ORM imports, satisfying the functional-programming and separation-of-concerns principles.
  Checking win status is an O(12) set-containment loop — negligible compared to the DB round-trip.
- **Alternatives considered**: Storing a precomputed line index on each `BoardSquare` and querying `COUNT` per line (rejected — more queries and DB-side logic for no benefit at this scale); a bitmask integer instead of `frozenset[int]` (rejected — a `frozenset[int]` is at least as fast at N=25 and far more readable/testable than manual bit twiddling).

## D5 — Center square is a non-toggleable free space, always marked

- **Decision**: `BoardSquare` at position 12 (the grid center, 0-indexed 5×5) is created with `buzzword=None`, `marked=True`, and the toggle view treats position 12 as a no-op (returns the current, unchanged fragment) rather than a 4xx error.
- **Rationale**: FR-007 requires the center to start marked as a free space; treating a toggle attempt on it as a harmless no-op (rather than an error) keeps the HTMX client code simple — the server always returns *a* valid fragment for any square ID that exists on that board.
- **Alternatives considered**: Rejecting toggle requests on the free square with an error response (rejected — adds a special-case error path in the client for no real benefit, since the square's marked state is a domain invariant, not user error).

## D6 — Exactly one winner race handled with a single conditional UPDATE, not row locking

- **Decision**: When a toggle results in `has_bingo(...) is True`, the view performs `Game.objects.filter(pk=game_id, status=GameStatus.ACTIVE).update(status=GameStatus.FINISHED, winner=player)` inside the same transaction as the square update, and checks the returned row count.
  A count of `1` means this request recorded the win; a count of `0` means another request already finished the game first (per the spec's Assumptions: exactly one winner, first mark wins).
- **Rationale**: A conditional `UPDATE ... WHERE status = 'active'` is atomic at the database level without needing explicit `select_for_update()` locking or `SERIALIZABLE` isolation — Postgres guarantees only one concurrent `UPDATE` can match the `WHERE status = 'active'` predicate and win the row.
  This directly implements the documented tie-break assumption with minimal code.
- **Alternatives considered**: `select_for_update()` on the `Game` row before checking status (rejected — extra explicit locking for no benefit over a conditional update); optimistic concurrency via a version column (rejected — over-engineered for a single boolean-ish state transition).

## D7 — HTMX wiring: enable `django-htmx`, return partials with an out-of-band winner fragment

- **Decision**: Add `"django_htmx"` to `INSTALLED_APPS` and `"django_htmx.middleware.HtmxMiddleware"` to `MIDDLEWARE` in `config/settings/base.py` (both already unused despite `django-htmx` being a declared dependency).
  The toggle view always renders `partials/_square.html` for the toggled square; when a win occurs, it additionally renders `partials/_winner_banner.html` wrapped in an `hx-swap-oob="true"` element targeting a banner region present on every board page, matching the source doc's "Updated cell fragment.
  Optional winner banner fragment." response shape.
- **Rationale**: `django-htmx` gives `request.htmx` for future use (e.g., distinguishing HTMX vs. direct requests) at negligible cost since it's already a dependency; out-of-band swaps are HTMX's standard mechanism for updating a second region (the winner banner) from a response whose primary target is a different element (the toggled square), avoiding any custom JavaScript.
- **Alternatives considered**: A separate polling endpoint for game status (rejected — explicitly out of scope per the spec's "no polling" exclusion); returning JSON and updating the DOM with hand-written JavaScript (rejected — reintroduces exactly the custom-JS complexity HTMX is chosen to avoid, and conflicts with the constitution's "no other JS frameworks/custom JS without 100% TypeScript test coverage" constraint).

## D8 — No denormalized "marked count" or bitmask field on `Board`

- **Decision**: Win detection re-reads all 25 `BoardSquare` rows for the affected board (`.values_list("position", "marked")`) on every toggle, rather than maintaining a denormalized summary field.
- **Rationale**: 25-row reads are inexpensive and keep `has_bingo` a pure function of straightforwardly-queried data; avoiding a denormalized field avoids a second source of truth that toggle logic would otherwise have to keep in sync, which matters more than the marginal query cost at the spec's target scale (100 concurrent participants, SC-004's <500ms budget).
- **Alternatives considered**: A `marked_mask` integer column updated alongside each square (rejected — premature optimization; reintroduces exactly the kind of implicit state the domain-function approach in D4 is meant to avoid).

## D9 — Admin registrations mirror the spec's four manageable entities plus `Board` for inspection

- **Decision**: `admin.py` registers `Buzzword` (list/search/filter on `text`/`active`, with bulk activate/deactivate actions), `Game` (read-mostly: `name`, `status`, `winner`, `created_at`), `Player`, and `Board` (for support/inspection), with `BoardSquare` shown as a read-only inline under `Board` rather than registered standalone.
- **Rationale**: FR-014/015 require buzzword CRUD-minus-delete and game/player visibility including winners; the source doc's admin section additionally lists "Boards" as admin-manageable, so `Board` gets a light read-focused registration for support use, while `BoardSquare` (25 rows per board) is better presented as an inline than a standalone changelist.
- **Alternatives considered**: Registering `BoardSquare` standalone (rejected — 25 rows per board with no independent lifecycle add little value as a top-level changelist compared to an inline on `Board`).

## Flags recorded for visibility (not fixed as part of this planning step)

- Repo-wide `pyrefly`/`ty` strict-mode CI enforcement is still outstanding (tracked in the constitution's own Sync Impact Report, first surfaced by `001-django-postgresql-backend`'s `/speckit-analyze`); this feature's new `domain.py` code is written fully type-annotated regardless.
- The mkdocs-vs-Sphinx documentation-tooling mismatch (constitution finding C1) is mitigated per-feature (see Constitution Check) but not resolved repo-wide; out of scope here.
