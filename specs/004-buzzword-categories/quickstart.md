<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Quickstart: Buzzword Categories](#quickstart-buzzword-categories)
  - [Prerequisites](#prerequisites)
  - [Try it locally (once implemented)](#try-it-locally-once-implemented)
  - [Key test scenarios to verify](#key-test-scenarios-to-verify)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Quickstart: Buzzword Categories

## Prerequisites

- Repo checked out on branch `004-buzzword-categories`.
- Backend dev environment set up per [docs/development.md](../../docs/development.md) (PostgreSQL running, `backend/` virtualenv/deps installed).

## Try it locally (once implemented)

1. Run migrations: `python manage.py migrate` (from `backend/`) to create the `Category` table and the new `Buzzword.categories` / `Game.buzzword_pool` M2M tables.
2. In Django admin, create a few `Category` rows (e.g. "Corporate", "Sports").
3. Create/edit a `Buzzword` in admin and assign it to at least one category — saving with zero categories selected is rejected.
4. Visit the create-game page (`/`).
   Select one or more categories; the buzzword checklist below narrows to buzzwords tagged with at least one selected category (or shows all active buzzwords if no category is selected).
5. Select at least one buzzword and submit the game name — submitting with zero buzzwords selected is rejected with a validation error.
6. Share the resulting join link; joining draws board words only from the game's selected buzzword pool, not the global active-buzzword set.

## Key test scenarios to verify

- Saving a buzzword with zero categories (admin form) is rejected.
- Removing a buzzword's last remaining category (e.g. via bulk admin action) is rejected.
- Selecting a category with zero matching active buzzwords shows an empty/appropriate state, not an error.
- Submitting game creation with zero buzzwords selected is rejected; the game is not created.
- A buzzword tagged with two categories appears when either category is selected individually.
- Deactivating a category removes it from future category-selection options without affecting existing buzzword categorization, games, or boards.
- Joining a game only offers/produces boards drawn from that game's `buzzword_pool`, even if other active buzzwords exist outside that pool.
