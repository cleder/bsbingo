<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Data Model: Buzzword Bingo Game](#data-model-buzzword-bingo-game)
  - [Entity 1: Buzzword](#entity-1-buzzword)
  - [Entity 2: Game](#entity-2-game)
  - [Entity 3: Player](#entity-3-player)
  - [Entity 4: Board](#entity-4-board)
  - [Entity 5: BoardSquare](#entity-5-boardsquare)
  - [Relationships](#relationships)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Data Model: Buzzword Bingo Game

**Feature**: `002-buzzword-bingo-game` | **Date**: 2026-07-12

Five Django models in the `bingo` app implement the spec's Key Entities.
See [research.md](./research.md) D1–D2 for the UUID-primary-key and uniqueness rationale.

## Entity 1: Buzzword

| Field | Type | Notes |
|---|---|---|
| `id` | `UUIDField`, primary key | `default=uuid4`, `editable=False` |
| `text` | `CharField(max_length=100)` | `unique=True` (D2) |
| `active` | `BooleanField` | `default=True`; only active buzzwords are eligible for new boards (FR-006, FR-014) |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

**Validation rules**: `text` must be non-blank (standard Django `CharField` `blank=False` default) and unique.

## Entity 2: Game

| Field | Type | Notes |
|---|---|---|
| `id` | `UUIDField`, primary key | `default=uuid4`, `editable=False` — this is the game's capability identifier, though the *join* link additionally embeds it in `/game/<id>/join/` (FR-002) |
| `name` | `CharField(max_length=200)` | Non-blank, whitespace-only rejected by `bingo/forms.py` (FR-001) |
| `status` | `CharField(max_length=10, choices=GameStatus.choices)` | `GameStatus` is a `django.db.models.TextChoices` enum: `ACTIVE = "active"`, `FINISHED = "finished"`; `default=GameStatus.ACTIVE` |
| `winner` | `ForeignKey("Player", null=True, blank=True, on_delete=SET_NULL, related_name="+")` | Set only when `status == FINISHED` (FR-010) |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

**State transitions**: `ACTIVE → FINISHED` exactly once, via the conditional `UPDATE ... WHERE status = 'active'` in [research.md](./research.md) D6.
There is no `FINISHED → ACTIVE` transition and no other status value — `GameStatus` makes any third state unrepresentable (FR-017).

**Validation rules**: New players/boards may only be created while `status == ACTIVE` (FR-005); all mark/unmark requests are rejected once `status == FINISHED` (FR-011).

## Entity 3: Player

| Field | Type | Notes |
|---|---|---|
| `id` | `UUIDField`, primary key | `default=uuid4`, `editable=False` |
| `game` | `ForeignKey(Game, on_delete=CASCADE, related_name="players")` | |
| `name` | `CharField(max_length=100)` | Non-blank, whitespace-only rejected by `bingo/forms.py` (FR-003); **not** unique — multiple players in the same game may share a name (FR-004) |
| `joined_at` | `DateTimeField` | `auto_now_add=True` |

## Entity 4: Board

| Field | Type | Notes |
|---|---|---|
| `id` | `UUIDField`, primary key | `default=uuid4`, `editable=False` — this UUID **is** the board's capability URL (`/board/<id>/`), per D1; the participant's sole means of access (FR-012) |
| `player` | `OneToOneField(Player, on_delete=CASCADE, related_name="board")` | |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

## Entity 5: BoardSquare

| Field | Type | Notes |
|---|---|---|
| `id` | `UUIDField`, primary key | `default=uuid4`, `editable=False` — also the identifier used in the toggle route `/board/<board_id>/cell/<id>/toggle/` |
| `board` | `ForeignKey(Board, on_delete=CASCADE, related_name="squares")` | |
| `position` | `IntegerField(validators=[MinValueValidator(0), MaxValueValidator(24)])` | `unique_together = ("board", "position")` — exactly one square per position per board |
| `buzzword` | `ForeignKey(Buzzword, null=True, blank=True, on_delete=PROTECT, related_name="+")` | `null` only for the center free square (position 12); `PROTECT` so a buzzword can't be deleted out from under boards that reference it — deactivation (`active=False`) is the intended removal path, not deletion |
| `marked` | `BooleanField` | `default=False`; the center square (position 12) is created with `marked=True` (FR-007) and is a toggle no-op thereafter (D5) |

**Validation rules**: A board has exactly 25 `BoardSquare` rows created atomically at join time (FR-006); the 24 non-center squares reference 24 distinct `Buzzword` rows drawn only from `active=True` buzzwords (FR-006, FR-016; see [research.md](./research.md) D3 for the too-small-pool rejection path).

## Relationships

```text
Game 1───* Player 1───1 Board 1───* BoardSquare *───1 Buzzword
  └──────────────────── winner (0..1, set once FINISHED)
```

- One `Game` has many `Player`s (FR-003/FR-004).
- One `Player` has exactly one `Board` (FR-006).
- One `Board` has exactly 25 `BoardSquare`s (FR-006/FR-007).
- Many `BoardSquare`s (across many boards) may reference the same `Buzzword`; each individual board references any given `Buzzword` at most once (FR-006).
- `Game.winner` references the one `Player` whose move completed a winning line (FR-010; see [research.md](./research.md) D6 for how exactly one winner is guaranteed under concurrent moves).
