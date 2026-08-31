<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Data Model: Buzzword Categories](#data-model-buzzword-categories)
  - [Category (new)](#category-new)
  - [Buzzword (existing, extended)](#buzzword-existing-extended)
  - [Game (existing, extended)](#game-existing-extended)
  - [Relationships](#relationships)
  - [Join-time board generation (updated behavior)](#join-time-board-generation-updated-behavior)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Data Model: Buzzword Categories

## Category (new)

| Field | Type | Notes |
|---|---|---|
| `id` | `UUIDField` (PK, `default=uuid4`, `editable=False`) | Matches the existing convention used by every other model in `bingo/models.py`. |
| `name` | `CharField(max_length=100)` | Required; unique **case-insensitively** (FR-005) via a `UniqueConstraint` on `Lower("name")`. |
| `active` | `BooleanField(default=True)` | Deactivated categories are excluded from future category-selection options (FR-009) but existing buzzword associations are untouched. |
| `created_at` | `DateTimeField(auto_now_add=True)` | Mirrors `Buzzword.created_at`. |

**Meta**: `ordering = ("name",)`, mirroring `Buzzword`'s `ordering = ("text",)`.

**Validation rules**:

- Name MUST be non-blank (`strip=True` in the admin/creation form, same pattern as `GameNameForm`/`DisplayNameForm`).
- Name MUST be unique case-insensitively (FR-005) — duplicate submissions are rejected with a validation error.

**State transitions**: `active` ⇄ `inactive` only; no other lifecycle states (mirrors `Buzzword.active`).
Deactivation does not cascade to delete or unassign existing `Buzzword` associations (FR-009).
Hard deletion is never offered for `Category` (FR-003/FR-010) — `CategoryAdmin` disables the delete permission and bulk delete action entirely, matching `Buzzword`'s own deactivate-only lifecycle (see research.md Decision R6).

## Buzzword (existing, extended)

| Field | Type | Notes |
|---|---|---|
| `categories` | `ManyToManyField(Category, related_name="buzzwords")` | **New.** Every `Buzzword` MUST have at least one associated `Category` (FR-001) — enforced by required form validation at creation/edit time plus an `m2m_changed` signal guard against removing the last remaining category (see [research.md](./research.md) Decision R1). |

All other existing fields (`id`, `text`, `active`, `created_at`) are unchanged.

**Validation rules**:

- A `Buzzword` MUST NOT be saved via the admin/creation form with zero categories selected.
- A `m2m_changed` `pre_remove`/`pre_clear` receiver on `Buzzword.categories` MUST reject any operation that would leave a buzzword with zero categories, regardless of the code path (admin form, bulk action, shell).

## Game (existing, extended)

| Field | Type | Notes |
|---|---|---|
| `buzzword_pool` | `ManyToManyField(Buzzword, related_name="games")` | **New.** The specific, curated set of buzzwords the creator selected for this game (FR-006/FR-007), populated once at creation time. MUST contain at least one buzzword (FR-012) — enforced by required form validation before the `Game` row is created. |

All other existing fields (`id`, `name`, `status`, `winner`, `created_at`) are unchanged.

**Validation rules**:

- Game creation MUST be rejected (form-level, before any `Game` row is written) if zero buzzwords are selected (FR-012).
- `buzzword_pool` is set once at creation and is not mutated by later category/buzzword administration changes — deactivating a buzzword or category after a game's creation does not retroactively shrink `buzzword_pool` (consistent with FR-009's "no effect on already-generated board" precedent, extended here to "already-created game").

## Relationships

```text
Category ──(M2M, "categories")── Buzzword ──(M2M, "buzzword_pool")── Game
                                     │
                                     └──(FK, existing)── BoardSquare
```

- `Category` ↔ `Buzzword`: many-to-many, both directions unrestricted in count except the "≥1 category per buzzword" floor.
- `Buzzword` ↔ `Game`: many-to-many, representing "this buzzword is eligible for this specific game's boards" — distinct from the existing `Buzzword` ↔ `BoardSquare` foreign key, which records which buzzword ended up on which already-generated square.

## Join-time board generation (updated behavior)

`join_game`'s board-generation pool changes from:

```python
pool = list(Buzzword.objects.filter(active=True).values_list("id", flat=True))
```

to:

```python
pool = list(game.buzzword_pool.filter(active=True).values_list("id", flat=True))
```

The existing `InsufficientBuzzwordPoolError` handling (FR-016 in `002-buzzword-bingo-game`) is unchanged — it now simply triggers more readily since the pool is scoped to one game's curated selection rather than every active buzzword system-wide.
