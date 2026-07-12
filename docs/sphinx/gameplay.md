<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Buzzword Bingo gameplay](#buzzword-bingo-gameplay)
  - [Player flow](#player-flow)
  - [Access model](#access-model)
  - [Admin flow](#admin-flow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Buzzword Bingo gameplay

Player- and admin-facing setup notes for the `bingo` app (feature `002-buzzword-bingo-game`).
See [`specs/002-buzzword-bingo-game/`](../../specs/002-buzzword-bingo-game/) for the full spec, data model, and endpoint contracts.

## Player flow

1. Visit `/` and submit a game name to create a `Game` and receive a
   shareable join link (`/game/<id>/join/`).
2. Each participant opens the join link and submits a display name to
   receive their own randomly generated 5×5 board (`/board/<id>/`), with
   the center square pre-marked as a free space.
3. Marking/unmarking a square is an HTMX request to
   `/board/<id>/cell/<id>/toggle/`, which swaps only the toggled square —
   no full page reload.
4. Completing a full row, column, or diagonal finishes the game and
   delivers a winner-banner fragment in the same response; further toggles
   by any participant in that game are then rejected.

## Access model

There is no player login.
A game's or board's UUID *is* its capability URL — possessing the link is the only credential needed.
This is deliberate: the spec excludes user accounts/authentication for players.

## Admin flow

Staff sign in to `/admin/` (via the existing `python-social-auth` integration) to:

- Add, edit, and bulk activate/deactivate `Buzzword` entries — only
  active buzzwords are eligible for boards generated afterward.
- Inspect `Game`/`Player` records, including a finished game's recorded
  `status` and `winner`.
- Inspect a `Board`'s 25 `BoardSquare` rows as a read-only inline.
