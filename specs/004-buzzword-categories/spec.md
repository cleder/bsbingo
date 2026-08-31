<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Feature Specification: Buzzword Categories](#feature-specification-buzzword-categories)
  - [Clarifications](#clarifications)
    - [Session 2026-08-30](#session-2026-08-30)
  - [User Scenarios & Testing *(mandatory)*](#user-scenarios--testing-mandatory)
    - [User Story 1 - Filter buzzwords by category when creating a game (Priority: P1)](#user-story-1---filter-buzzwords-by-category-when-creating-a-game-priority-p1)
    - [User Story 2 - Manage categories on buzzwords (Priority: P2)](#user-story-2---manage-categories-on-buzzwords-priority-p2)
    - [User Story 3 - Browse and manage the category list (Priority: P3)](#user-story-3---browse-and-manage-the-category-list-priority-p3)
    - [Edge Cases](#edge-cases)
  - [Requirements *(mandatory)*](#requirements-mandatory)
    - [Functional Requirements](#functional-requirements)
    - [Key Entities *(include if feature involves data)*](#key-entities-include-if-feature-involves-data)
  - [Assumptions](#assumptions)
  - [Success Criteria *(mandatory)*](#success-criteria-mandatory)
    - [Measurable Outcomes](#measurable-outcomes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Feature Specification: Buzzword Categories

**Feature Branch**: `004-buzzword-categories` **Created**: 2026-08-30 **Status**: Draft **Input**: User description: "As a game creator I want Buzzword to have a category, so when I create a new game I can first choose the category and then choose the buzzwords for a new game.
A buzzword can have multiple categories."

## Clarifications

### Session 2026-08-30

- Q: Can a game creator proceed with game creation if they select zero buzzwords?
  → A: No — at least one buzzword must be selected to proceed.
- Q: Is any data migration or backfill needed for existing buzzwords lacking a category?
  → A: No — this is a clean-slate feature with no legacy buzzword data to migrate.
- Q: Must a buzzword have at least one category assigned at creation time?
  → A: Yes — a buzzword MUST have at least one category assigned when it is created; zero-category buzzwords are not a legal state.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter buzzwords by category when creating a game (Priority: P1)

A game creator starts creating a new game, first picks one or more categories (e.g. "Corporate", "Sports"), and is then shown only the buzzwords that belong to at least one of the selected categories to choose from for the new board pool.

**Why this priority**: This is the core value of the feature — without category filtering, the creator still faces the same unfiltered buzzword list as today, so this delivers the entire point of the request.

**Independent Test**: Can be fully tested by creating buzzwords tagged with different categories, starting game creation, selecting a category, and confirming only matching buzzwords are offered.

**Acceptance Scenarios**:

1. **Given** buzzwords exist in categories "Corporate" and "Sports", **When** a game creator selects the "Corporate" category during game creation, **Then** only buzzwords tagged "Corporate" are available to choose from.
2. **Given** a buzzword tagged with both "Corporate" and "Sports", **When** the creator selects either category, **Then** that buzzword appears in the available list both times.
3. **Given** no category is selected, **When** the creator proceeds, **Then** all active buzzwords remain available (existing behavior is preserved).
4. **Given** a game creator has selected zero buzzwords, **When** they attempt to proceed, **Then** the system blocks progression with a validation message requiring at least one buzzword to be selected.

---

### User Story 2 - Manage categories on buzzwords (Priority: P2)

An administrator assigns one or more categories to a buzzword, creates new categories as needed, and removes a category from a buzzword without affecting other buzzwords or boards that already reference it.

**Why this priority**: Category selection during game creation (User Story 1) is only useful once buzzwords actually carry category data — this is the prerequisite management capability.

**Independent Test**: Can be fully tested by creating a category, assigning it to one or more buzzwords via the admin interface, and confirming the assignment persists and can be changed independently of other buzzwords.

**Acceptance Scenarios**:

1. **Given** an existing buzzword with no categories, **When** an administrator assigns it to a category, **Then** the buzzword is listed under that category going forward.
2. **Given** a buzzword assigned to multiple categories, **When** an administrator removes one category assignment, **Then** the buzzword remains assigned to its other categories and is unaffected in existing boards.
3. **Given** a category still referenced by at least one buzzword, **When** an administrator looks for a way to remove it, **Then** only deactivation is offered — hard deletion of a category is not a supported operation, so a buzzword's category assignment can never be silently dropped by deleting the category it points to.

---

### User Story 3 - Browse and manage the category list (Priority: P3)

An administrator views the full list of categories, creates new ones, renames existing ones, and deactivates categories that are no longer needed, similar to how buzzwords are already managed.

**Why this priority**: Nice-to-have curation and lifecycle management; the feature is usable end-to-end via User Stories 1–2 without dedicated category CRUD screens, but ongoing maintenance benefits from it.

**Independent Test**: Can be fully tested by creating, renaming, and deactivating a category through the admin interface and confirming the changes are reflected in the category list and in game creation filtering.

**Acceptance Scenarios**:

1. **Given** the administrator is on the category management screen, **When** they create a new category with a unique name, **Then** it appears in the category list and becomes selectable during game creation.
2. **Given** a category is deactivated, **When** a game creator starts a new game, **Then** the deactivated category no longer appears as a filter option, but buzzwords already tagged with it are unaffected.

---

### Edge Cases

- What happens when a game creator selects a category that currently has zero active buzzwords?
  The system shows an empty/appropriate state, and the creator must select a different category (or none) to select at least one buzzword before proceeding.
- What happens when a game creator has selected zero buzzwords overall?
  The system MUST prevent proceeding and require selecting at least one buzzword.
- What happens when all categories assigned to a buzzword are deactivated?
  The buzzword itself remains active, retains its (now-deactivated) category assignments, and still appears when no category filter is applied.
- What happens when an administrator tries to create a category with a name that already exists?
  The system rejects the submission with a validation error, consistent with existing buzzword text uniqueness handling.
- What happens when an administrator tries to create or save a buzzword with no category assigned?
  The system rejects the submission, since every buzzword MUST have at least one category.
- What happens when an administrator tries to hard-delete a category (rather than deactivate it)?
  The system does not offer this operation at all, for any category, referenced or not — deactivation is the only removal path, exactly as with `Buzzword`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST require every `Buzzword` to be associated with at least one category at creation time, and MUST allow association with multiple categories; a buzzword with zero categories is an invalid state.
- **FR-002**: System MUST allow a category to be associated with multiple buzzwords (many-to-many relationship).
- **FR-003**: Administrators MUST be able to create, rename, and deactivate categories through the existing admin management interface; hard deletion of a category MUST NOT be offered, mirroring `Buzzword`'s deactivate-only lifecycle.
- **FR-004**: Administrators MUST be able to assign and remove category associations on a buzzword without affecting other buzzwords or previously generated boards.
- **FR-005**: System MUST prevent duplicate category names (case-insensitive uniqueness), consistent with existing buzzword text uniqueness rules.
- **FR-006**: During game creation, the game creator MUST be able to select one or more categories before selecting/confirming the buzzword pool for the new game.
- **FR-007**: When one or more categories are selected during game creation, the system MUST restrict the offered buzzwords to only those active buzzwords tagged with at least one of the selected categories.
- **FR-008**: When no category is selected during game creation, the system MUST offer all active buzzwords, preserving current (pre-feature) behavior.
- **FR-009**: Deactivating a category MUST remove it from future category-selection options without altering any buzzword's active status or any already-generated board.
- **FR-010**: System MUST NOT permit hard deletion of a `Category` through the admin interface under any circumstances (see FR-003); deactivating a referenced category MUST NOT delete those buzzwords, unassign their category, or corrupt existing board data.
  Making deletion entirely unavailable — rather than merely discouraged — makes it impossible for a buzzword to ever be left with zero categories via cascade deletion.
- **FR-011**: System MUST continue to enforce that only active buzzwords are drawn from when a board is generated (existing rule), regardless of category filtering.
- **FR-012**: System MUST prevent a game creator from proceeding with game creation while zero buzzwords are selected; at least one buzzword MUST be selected to continue.

### Key Entities *(include if feature involves data)*

- **Category**: A named grouping label (e.g. "Corporate", "Sports") that a game creator can filter by; has a unique name and an active/inactive state; independent of any single buzzword's lifecycle.
- **Buzzword**: (existing entity) A candidate word/phrase; extended to require at least one, and allow multiple, category associations.
- **Buzzword-Category association**: The many-to-many link between buzzwords and categories, allowing a single buzzword to belong to multiple categories and a single category to contain multiple buzzwords.

## Assumptions

- Category management reuses the same administrative access model already in place for buzzword management (no new user roles introduced).
- Category selection during game creation is optional; games can still be created with no category filter, matching current behavior.
  Buzzword selection, however, is mandatory (at least one).
- Selecting multiple categories during game creation combines their buzzwords (logical OR), rather than requiring a buzzword to match every selected category.
- Category names, like buzzword text, are simple short labels with no additional metadata (e.g. no descriptions or icons) required for the MVP of this feature.
- This is a clean-slate feature: no pre-existing buzzword data lacks a category, so no data migration or backfill step is required to satisfy the mandatory-category rule.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A game creator can narrow the buzzword pool to a specific category in under 10 seconds during game creation.
- **SC-002**: 100% of buzzwords tagged with multiple categories correctly appear when any one of their assigned categories is selected.
- **SC-003**: Administrators can assign or remove a category from a buzzword without any measurable impact (errors or data changes) on other buzzwords or previously created games/boards.
- **SC-004**: Existing game-creation flows that select no category filter continue to function identically to before this feature (category filtering itself remains optional), with zero regressions in the buzzword pool offered.
- **SC-005**: 100% of attempts to save a buzzword with zero categories, or proceed with game creation with zero buzzwords selected, are rejected with a clear validation message.
