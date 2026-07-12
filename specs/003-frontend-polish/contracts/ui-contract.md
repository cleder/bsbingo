<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [UI Contract: Frontend Polish & Mobile-First UX](#ui-contract-frontend-polish--mobile-first-ux)
  - [Shared (every screen, `base.html`)](#shared-every-screen-basehtml)
  - [Home screen (`home.html`)](#home-screen-homehtml)
  - [Join screen (`join.html`)](#join-screen-joinhtml)
  - [Board screen (`board.html`)](#board-screen-boardhtml)
  - [Not-found / error responses](#not-found--error-responses)
  - [Test-ID discipline](#test-id-discipline)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# UI Contract: Frontend Polish & Mobile-First UX

This feature adds no new HTTP endpoints — every screen is served by the four routes already defined in `002-buzzword-bingo-game` (`backend/bingo/urls.py`: `create_game`, `join_game`, `view_board`, `toggle_cell`).
What's new is a set of **stable markup anchors** (element roles, `id`s, and `data-testid` attributes) that both the restyled templates and the `frontend/e2e/` Playwright specs agree on, so tests target semantic, accessible selectors rather than CSS classes that are expected to change during polish.

This is the contract implementers and test-authors both work from: templates MUST expose these anchors; Playwright specs MUST select elements by them (never by CSS class or visual position).

## Shared (every screen, `base.html`)

| Anchor | Element | Notes |
|---|---|---|
| `data-testid="theme-toggle"` | Light/dark toggle `<button>` | Wired to `theme-toggle.ts`; `data-theme="light"/"dark"` on `<html>` reflects the current choice, `aria-pressed` on the button mirrors it (dark mode addendum) |

## Home screen (`home.html`)

| Anchor | Element | Notes |
|---|---|---|
| `data-testid="game-name-input"` | The game-name `<input>` | Has `autofocus`; native `<form>` submit handles Enter (FR-001) |
| `data-testid="create-game-submit"` | Submit button | Min 44×44px touch target (FR-012) |
| Field error | `role="alert"` element adjacent to the input | Rendered only when the form is invalid (FR-002) |
| `data-testid="share-link"` | The shareable join-link text/`<a>` | Shown after successful creation (FR-003) |
| `data-testid="copy-link-button"` | "Copy Link" `<button>` | Wired to `copy-link.ts`; shows a `role="status"` confirmation on success (FR-003) |
| `data-testid="create-another-game"` | Link/button back to a blank create-game form | (FR-003) |

## Join screen (`join.html`)

| Anchor | Element | Notes |
|---|---|---|
| `data-testid="player-name-input"` | The display-name `<input>` | `autofocus`; native Enter submit (FR-004) |
| `data-testid="join-game-submit"` | Submit button | (FR-004) |
| Field error | `role="alert"` element adjacent to the input | (FR-004) |
| `data-testid="game-finished-notice"` | Message shown instead of the form | When `game.status == "finished"` (US4 scenario 2) |
| `data-testid="no-buzzwords-notice"` | Message shown when the buzzword pool is insufficient | (FR-017) |

## Board screen (`board.html`)

| Anchor | Element | Notes |
|---|---|---|
| `data-testid="game-name"`, `data-testid="player-name"` | Header text | Always visible (FR-005) |
| `role="grid"` on the board container; `role="gridcell"` on each `_square.html` button | 5×5 board | Semantic grid for screen readers (FR-006, FR-014) |
| `data-testid="cell-{position}"` (0-24, except the center — see `free-space` below) | Each non-free cell button | Stable regardless of which buzzword landed there — tests select by position, not text (FR-007–FR-010) |
| `.marked` / absence of `.marked` (CSS class, existing) on a cell | Marked/unmarked visual state | Retained from 002; tests may assert on this class since it is functional, not purely cosmetic (FR-008) |
| `data-testid="free-space"` | The center cell | Non-interactive; always shows marked; takes the place of a `cell-12` testid (a cell can only carry one `data-testid`) (FR-009) |
| `id="winner-banner"`, `role="status" aria-live="polite"` (existing, `_winner_banner.html`) | Out-of-band winner/finished notice region | Retained from 002 (FR-016) |
| `data-testid="winner-overlay"` | The celebratory overlay shown to the winning player | Appears on the winning toggle response (FR-015) |
| `data-testid="celebrate-dismiss"` | The "Celebrate" dismiss control on the overlay | Reveals the read-only, highlighted board underneath (FR-015, per Clarifications) |
| `data-winning-line="true"` | Plain (non-testid) attribute applied to each cell in the completed line | A separate attribute, not a second `data-testid`, since `cell-{position}`/`free-space` already occupy that slot on the same element — used for the highlight (FR-015) |
| `data-testid="board-readonly"` | Attribute/class on the board container once `game.status == "finished"` | Signals cells are inert for every participant (FR-016) |

## Not-found / error responses

| Anchor | Condition | Notes |
|---|---|---|
| `data-testid="not-found-notice"` | `view_board`/`join_game` given a nonexistent id (Django's existing `get_object_or_404` → 404 page) | Message text per FR-018; the 404 template gains this `data-testid` (FR-018) |

## Test-ID discipline

- `data-testid` attributes are additive markup only — they carry no styling and MUST NOT be selected against in CSS.
- Every `data-testid` in this table MUST appear in exactly the templates listed; `frontend/e2e/*.spec.ts` MUST NOT introduce a selector that isn't in this table without updating this file first (keeps templates and tests from silently drifting apart).
