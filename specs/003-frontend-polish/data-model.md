<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Phase 1 Data Model: Frontend Polish & Mobile-First UX](#phase-1-data-model-frontend-polish--mobile-first-ux)
  - [No new persisted entities](#no-new-persisted-entities)
  - [Derived presentation state (not persisted)](#derived-presentation-state-not-persisted)
    - [Cell interaction state (client-rendered, per `BoardSquare`)](#cell-interaction-state-client-rendered-per-boardsquare)
    - [Board-level read-only state (client-rendered, derived from `Game.status` + `Game.winner`)](#board-level-read-only-state-client-rendered-derived-from-gamestatus--gamewinner)
  - [Validation rules](#validation-rules)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Phase 1 Data Model: Frontend Polish & Mobile-First UX

## No new persisted entities

This feature introduces **no new models, fields, or migrations**.
It reuses the domain model already defined and migrated in `002-buzzword-bingo-game` (`specs/002-buzzword-bingo-game/data-model.md` / `backend/bingo/models.py`): `Buzzword`, `Game` (+ `GameStatus`), `Player`, `Board`, `BoardSquare`.
Nothing about their fields, relationships, or lifecycle changes here — see spec.md's Assumptions.

The only data-shaped concepts this feature adds are **presentation-only, unpersisted** — client-side/template-rendering states derived from the existing model, not stored anywhere:

## Derived presentation state (not persisted)

### Cell interaction state (client-rendered, per `BoardSquare`)

A purely visual state machine layered on the existing `marked: bool` field, resolved in the browser during one HTMX round-trip:

| State | Entered when | Exited when | Governing requirement |
|---|---|---|---|
| `unmarked` | Initial render; `square.marked` is `False` | Player taps the cell → `pending` | FR-008 |
| `pending` | Player taps an `unmarked`/`marked`, non-free cell | Server responds with the swapped `_square.html` fragment → `unmarked` or `marked` per the new value | FR-010 |
| `marked` | Initial render or server response with `square.marked` `True` | Player taps the cell → `pending` | FR-008 |
| `free` (terminal) | `square.position == 12` (center) | Never — permanent | FR-009 |

While a cell is `pending`, it does not accept another tap (FR-010) — this is enforced declaratively (HTMX's element-disabling behavior on the in-flight request), not via a hand-rolled JS state machine.

### Board-level read-only state (client-rendered, derived from `Game.status` + `Game.winner`)

| State | Condition | Effect | Governing requirement |
|---|---|---|---|
| `active` | `game.status == GameStatus.ACTIVE` | Cells remain interactive | — (existing 002 behavior) |
| `finished-winner` | `game.status == GameStatus.FINISHED` and the viewed board belongs to `game.winner` | Board renders read-only; winning line highlighted; overlay was already shown and dismissed | FR-015, FR-016 |
| `finished-other` | `game.status == GameStatus.FINISHED` and the viewed board does not belong to `game.winner` | Board renders read-only; "game finished, winner: {name}" notice shown | FR-016 |

This state is computed each render from two already-existing fields (`Game.status`, `Game.winner`) compared against the board being viewed (`board.player == game.winner`) — no new field is needed on any model.
Exposing the comparison result to the template is the only additive `views.py` context change this feature makes (see plan.md's Project Structure).

## Validation rules

No new validation rules — `GameNameForm`/`DisplayNameForm` (existing, `002-buzzword-bingo-game`) are unchanged.
This feature only changes how their existing validation errors are *displayed* (inline, per FR-002/FR-004), not what they validate.
