<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Contract: Django Admin Interface](#contract-django-admin-interface)
  - [`Buzzword` admin](#buzzword-admin)
  - [`Game` admin](#game-admin)
  - [`Player` admin](#player-admin)
  - [`Board` admin](#board-admin)
  - [Out of scope for this contract](#out-of-scope-for-this-contract)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contract: Django Admin Interface

**Feature**: `002-buzzword-bingo-game`

Standard Django admin (`/admin/...`, already routed in `config/urls.py`), gated by Django's own staff-login mechanism (unaffected by this feature — see [plan.md](../plan.md) Constitution Check on `python-social-auth` scope).
This is not a public/player-facing contract; it satisfies FR-014/FR-015.

## `Buzzword` admin

- List view: `text`, `active`, `created_at`; filterable by `active`; searchable by `text`.
- Bulk actions: activate / deactivate selected buzzwords.
- Create/edit: `text` (unique — a duplicate save is rejected with a form error), `active`.
- No delete restriction beyond Django's default; buzzwords already referenced by a `BoardSquare` cannot be deleted (`on_delete=PROTECT` — see [data-model.md](../data-model.md) Entity 5), only deactivated.

## `Game` admin

- List view: `name`, `status`, `winner`, `created_at`; filterable by `status`.
- Read-mostly: `status` and `winner` are set only by gameplay (see [research.md](../research.md) D6), not hand-edited through this interface.

## `Player` admin

- List view: `name`, `game`, `joined_at`; filterable by `game`.

## `Board` admin

- List view: `player`, `created_at`.
- `BoardSquare` rows shown as a read-only inline (25 per board) rather than a standalone changelist ([research.md](../research.md) D9).

## Out of scope for this contract

- No custom admin actions beyond buzzword activate/deactivate — no manual game-ending or player-removal action is requested by the spec.
