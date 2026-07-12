<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Contract: Player-Facing HTTP Endpoints](#contract-player-facing-http-endpoints)
  - [`GET/POST /` — Create Game (User Story 1)](#getpost---create-game-user-story-1)
  - [`GET/POST /game/<uuid:game_id>/join/` — Join Game (User Story 2)](#getpost-gameuuidgame_idjoin--join-game-user-story-2)
  - [`GET /board/<uuid:board_id>/` — View Board (User Story 3)](#get-boarduuidboard_id--view-board-user-story-3)
  - [`POST /board/<uuid:board_id>/cell/<uuid:cell_id>/toggle/` — Toggle Cell (User Story 3)](#post-boarduuidboard_idcelluuidcell_idtoggle--toggle-cell-user-story-3)
  - [Out of scope for this contract](#out-of-scope-for-this-contract)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contract: Player-Facing HTTP Endpoints

**Feature**: `002-buzzword-bingo-game`

Four routes, all served by the `bingo` app and included from `config.urls`.
All identifiers in the path are UUIDs; a malformed (non-UUID) or well-formed-but-nonexistent identifier both return `404` (FR-013) — the distinction is not exposed to the caller.

## `GET/POST /` — Create Game (User Story 1)

- **GET**: Renders the create-game form (`home.html`).
- **POST**: Body: `name` (required, non-blank after trimming — FR-001).
  - **Success**: Creates a `Game` with `status=ACTIVE`, returns `200`/`302` rendering or redirecting to a page showing the shareable join URL `/game/<game.id>/join/` (FR-002).
  - **Validation failure** (blank/whitespace-only `name`): Re-renders `home.html` with a field error; no `Game` is created.

## `GET/POST /game/<uuid:game_id>/join/` — Join Game (User Story 2)

- **GET**: `404` if `game_id` doesn't resolve to any `Game`.
  Otherwise renders the join form (`join.html`), unless the game has already finished — in which case it renders a "no longer accepting participants" message instead of the form (no `404`; the game exists, it just can't be joined) (FR-005).
- **POST**: Body: `name` (required, non-blank after trimming — FR-003).
  - **Success**: Creates a `Player` (`game=<game_id>`, `name=<name>`), a `Board`, and 25 `BoardSquare`s (FR-006/FR-007), then redirects (`302`) to `/board/<board.id>/`.
  - **Game already finished**: No `Player`/`Board`/`BoardSquare` created; re-renders the "no longer accepting participants" state (FR-005).
  - **Fewer than 25 active buzzwords**: No `Player`/`Board`/`BoardSquare` created; re-renders `join.html` with an explanatory error (FR-016; [research.md](../research.md) D3).
  - **Validation failure** (blank/whitespace-only `name`): Re-renders `join.html` with a field error.

## `GET /board/<uuid:board_id>/` — View Board (User Story 3)

- `404` if `board_id` doesn't resolve to any `Board`.
- Otherwise renders `board.html`: the 5×5 grid (25 squares, each showing its buzzword text and marked/unmarked visual state) plus a winner-banner region (empty unless the game has already finished, in which case it shows the recorded winner).
- No mutation occurs on `GET`; this route is safe to reload or share (though sharing is not a use case the spec expects — only the participant holding this URL is expected to use it, per FR-012).

## `POST /board/<uuid:board_id>/cell/<uuid:cell_id>/toggle/` — Toggle Cell (User Story 3)

HTMX endpoint.
Expected to be called with an `HX-Request` header, but does not require it — any client capable of issuing the `POST` gets the same fragment response.

- `404` if `board_id` doesn't resolve to a `Board`, or `cell_id` doesn't resolve to a `BoardSquare` belonging to that `Board` (FR-013).
- **Game already finished** (regardless of who — winner or not — is toggling): `403`-equivalent rejection; no state change.
  Response re-renders the square's current (unchanged) fragment so the client's DOM stays consistent (FR-011).
- **Center square (position 12)**: No-op; always marked.
  Response renders its current fragment unchanged ([research.md](../research.md) D5).
- **Otherwise**: Toggles `marked` on the referenced `BoardSquare`, then runs win detection ([research.md](../research.md) D4) over the board's current marked positions.
  - **No win**: Response is the updated `partials/_square.html` fragment for the toggled square only.
  - **Win**: The `Game` is atomically transitioned `ACTIVE → FINISHED` with `winner` set to this square's board's player, guarded against a concurrent double-win ([research.md](../research.md) D6).
    Response is the updated square fragment **plus** an out-of-band `partials/_winner_banner.html` fragment (`hx-swap-oob="true"`) announcing the winner (FR-010).
  - **Lost the win race** (another request finished the game first, between this request's read and write): The square's `marked` toggle still applies (it's a valid move on a still-active-at-the-time board), but the win this request detected is not recorded as a second winner; the response fragment reflects the game's now-finished state and its actual (other) winner.

## Out of scope for this contract

- Any polling, WebSocket, or Server-Sent-Events endpoint — explicitly excluded from the feature (project overview §2 Out of Scope).
- Admin-interface routes (`/admin/...`) — covered separately in [admin-interface.md](./admin-interface.md).
