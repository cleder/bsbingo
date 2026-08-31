<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Research: Buzzword Categories](#research-buzzword-categories)
  - [Decision R1: How to enforce at least one category per buzzword for a Django M2M field](#decision-r1-how-to-enforce-at-least-one-category-per-buzzword-for-a-django-m2m-field)
  - [Decision R2: Where the game's curated buzzword pool is stored](#decision-r2-where-the-games-curated-buzzword-pool-is-stored)
  - [Decision R3: Category selection UX (single form vs. HTMX two-step)](#decision-r3-category-selection-ux-single-form-vs-htmx-two-step)
  - [Decision R4: Category name uniqueness](#decision-r4-category-name-uniqueness)
  - [Decision R5: Migration scope (clean-slate clarification)](#decision-r5-migration-scope-clean-slate-clarification)
  - [Decision R6: Category has no hard-delete path](#decision-r6-category-has-no-hard-delete-path)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Research: Buzzword Categories

## Decision R1: How to enforce at least one category per buzzword for a Django M2M field

**Decision**: Enforce at two layers — (1) `forms.ModelMultipleChoiceField(required=True)` on the buzzword admin/creation form rejects an empty submission, and (2) a `m2m_changed` signal on `Buzzword.categories` (`pre_remove`/`pre_clear`) raises if the change would leave the buzzword with zero categories, guarding paths that bypass the form (shell, bulk admin actions, future API).

**Rationale**: Django cannot express a minimum-cardinality constraint on a `ManyToManyField` declaratively (no `CheckConstraint` reaches M2M-through tables in a portable way, and `blank=False` on a M2M field is a form-only, not DB-level, hint).
A pure form check is the common approach for the primary UI path but is silently bypassed by any code that manipulates the M2M relation directly.
Combining both closes the gap without introducing a bespoke through-model just to add a `CheckConstraint`.

**Alternatives considered**:

- *Custom explicit through-model with a DB constraint*: rejected — M2M cardinality constraints (e.g. "at least one row per buzzword") cannot be expressed as a single-table `CheckConstraint`; would require a trigger, which is disproportionate for this feature and not used elsewhere in the codebase.
- *Only form-level validation, no signal*: rejected — fails FR-001's "MUST" for any mutation path other than the admin form (e.g. `buzzword.categories.clear()` in the Django shell or a bulk action), leaving the illegal state reachable.
- *`clean()` on the `Buzzword` model itself*: rejected — `full_clean()` cannot validate M2M relations before the instance has a primary key, so it cannot cover creation-time validation at all; the form-level check is strictly better for creation, and the signal is still needed for later removals.

## Decision R2: Where the game's curated buzzword pool is stored

**Decision**: Add `Game.buzzword_pool = models.ManyToManyField(Buzzword, related_name="games")`, populated once at game-creation time from the creator's selection. `join_game`'s board generation reads `game.buzzword_pool.filter(active=True)` instead of the current global `Buzzword.objects.filter(active=True)`.

**Rationale**: FR-006/FR-007 require the *specific game* to have its own curated pool chosen at creation time, not a global filter re-applied at every join.
Storing the selection on `Game` makes this pool a durable, per-game fact — consistent with the existing pattern where `Board`/`BoardSquare` already capture a per-player snapshot rather than re-deriving from global state at render time.

**Alternatives considered**:

- *Store only the selected `Category` IDs on `Game` and re-resolve buzzwords at each join*: rejected — a buzzword's category assignment or active flag could change between the game's creation and a later join, silently changing the pool underneath an already-shared game link, which conflicts with the spirit of FR-004 (existing board/board data isolation) and the existing precedent that deactivating a buzzword doesn't affect already-referenced data.
- *A new explicit `GameBuzzwordSelection` model instead of a plain M2M*: rejected — no extra per-pair metadata is needed (no "who added this," no ordering), so a plain `ManyToManyField` is the simplest structure that satisfies the requirement, consistent with the constitution's functional/minimal-complexity principles.

## Decision R3: Category selection UX (single form vs. HTMX two-step)

**Decision**: Keep `create_game` a single Django form page (no new route), but progressively enhance it: submitting the category checklist re-renders the buzzword checklist fragment via an HTMX partial swap (`partials/_buzzword_choices.html`), then the final "Create Game" submit posts the game name + selected buzzword IDs together.
No new URL routes are introduced.

**Rationale**: Matches the existing HTMX-partial-swap pattern already used for cell toggling (`toggle_cell` → `_square.html`) — same technology, same "thin view, server-rendered fragment" shape, no new JS framework, satisfying the constitution's HTMX-first constraint.
A single page keeps the number of routes and templates minimal (FR-006's "first choose categories, then buzzwords" is a UI sequencing requirement, not necessarily a multi-page/multi-request wizard).

**Alternatives considered**:

- *Separate `/game/create/categories/` and `/game/create/buzzwords/` pages with server-side session state*: rejected — adds a new stateful multi-request flow and a new place to leak partial game-creation state, for no functional benefit over an in-page HTMX refresh.
- *Client-side-only filtering (ship the full buzzword-category mapping as JSON, filter in TypeScript)*: rejected — for larger buzzword pools this pushes filtering logic into custom JS beyond what's needed, and the constitution requires any custom JS/TS to hit 100% test coverage; an HTMX partial swap keeps the filtering logic in already-tested Django view code instead of duplicating it in TypeScript.

## Decision R4: Category name uniqueness

**Decision**: Case-insensitive uniqueness on `Category.name`, enforced the same way project conventions would call for — a `UniqueConstraint` using `Lower("name")` (Django's functional-index constraint form), matching FR-005's explicit requirement and mirroring `Buzzword.text`'s plain `unique=True` (case-sensitive) but tightened per the spec's explicit "case-insensitive" wording.

**Rationale**: FR-005 explicitly calls out case-insensitive uniqueness for categories (stricter than the existing case-sensitive `Buzzword.text` uniqueness), so it needs its own constraint rather than reusing `Buzzword`'s pattern verbatim.

**Alternatives considered**:

- *Plain `unique=True` (case-sensitive) on `name`, matching `Buzzword.text`*: rejected — does not satisfy FR-005's explicit case-insensitive requirement ("Corporate" and "corporate" would both be accepted as distinct categories).
- *Application-level check only (no DB constraint)*: rejected — race conditions between concurrent admin submissions could still create duplicate categories differing only in case; a DB-level constraint is the standard way to make that illegal state unrepresentable.

## Decision R5: Migration scope (clean-slate clarification)

**Decision**: One new migration adds the `Category` model, the `Buzzword.categories` M2M, and the `Game.buzzword_pool` M2M.
No data-migration/backfill step is included, since the clarified assumption is that this is a clean-slate feature with no pre-existing `Buzzword` rows that must retroactively be assigned a category.

**Rationale**: The "no migrations needed" clarification refers to *data* migration/backfill, not the mandatory Django *schema* migration that any new model/field always requires — schema migrations are unavoidable and already part of this app's existing workflow (`0001_initial.py`, `0002_boardsquare_position_range.py`).
Distinguishing the two avoids misreading the clarification as "skip the migration file entirely," which is not technically possible for new models/fields.

**Alternatives considered**:

- *Add a data migration that creates a default "Uncategorized" category and back-assigns all existing buzzwords to it*: rejected per the explicit clarification that no legacy data exists to migrate; adding one anyway would be unnecessary complexity for a clean-slate deployment.

## Decision R6: Category has no hard-delete path

**Decision**: `Category` is deactivate-only, exactly like `Buzzword` — hard deletion is never offered through Django admin (`CategoryAdmin.has_delete_permission` returns `False`, and the bulk "delete selected" admin action is excluded).
Only `create`, `rename`, and `deactivate`/`activate` are supported (FR-003).

**Rationale**: An earlier draft of this spec allowed deleting a `Category` while relying on the `m2m_changed` guard (Decision R1) to protect `Buzzword.categories`' ≥1 invariant.
That guard only fires for `.remove()`/`.clear()` calls made through the M2M manager — Django's cascade-delete collector for an implicit M2M target deletes join-table rows directly via SQL and does not reliably emit `m2m_changed`, so deleting a category that is a buzzword's *only* category could silently strand that buzzword with zero categories, violating FR-001.
Removing the delete path entirely (rather than trying to guard it) makes the illegal state structurally unreachable, which is simpler and stronger than a delete-time check.

**Alternatives considered**:

- *Allow delete, add a `pre_delete` signal on `Category` that blocks deletion only when it's some buzzword's sole category*: rejected as unnecessary complexity — `Buzzword` itself already has no delete path (only `active` toggling), so making `Category` deactivate-only is consistent with the existing codebase convention rather than introducing a new, more permissive pattern just for this one model.
- *Allow delete, cascade-clear the M2M row, and rely on the (unreliable) `m2m_changed` guard*: rejected — as shown above, this is not actually safe against Django's cascade-delete implementation, so it would not satisfy FR-001/FR-010.
