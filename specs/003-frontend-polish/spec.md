<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature Specification: Frontend Polish & Mobile-First UX](#feature-specification-frontend-polish--mobile-first-ux)
  - [Clarifications](#clarifications)
    - [Session 2026-07-12](#session-2026-07-12)
  - [User Scenarios & Testing *(mandatory)*](#user-scenarios--testing-mandatory)
    - [User Story 1 - Create a game and share it in seconds (Priority: P1)](#user-story-1---create-a-game-and-share-it-in-seconds-priority-p1)
    - [User Story 2 - Join with almost no friction (Priority: P2)](#user-story-2---join-with-almost-no-friction-priority-p2)
    - [User Story 3 - Play the board and feel the win (Priority: P3)](#user-story-3---play-the-board-and-feel-the-win-priority-p3)
    - [User Story 4 - Never hit a dead end (Priority: P4)](#user-story-4---never-hit-a-dead-end-priority-p4)
    - [Edge Cases](#edge-cases)
  - [Requirements *(mandatory)*](#requirements-mandatory)
    - [Functional Requirements](#functional-requirements)
  - [Assumptions](#assumptions)
  - [Success Criteria *(mandatory)*](#success-criteria-mandatory)
    - [Measurable Outcomes](#measurable-outcomes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Feature Specification: Frontend Polish & Mobile-First UX

**Feature Branch**: `003-frontend-polish` **Created**: 2026-07-12 **Status**: Draft **Input**: User description: "Frontend polish, verified end-to-end with automated browser testing.
Apply the supplied Buzzword Bingo MVP UX specification to the existing create/share/join/board screens: mobile-first, portrait, one-handed, large-touch-target design; zero-training-required interactions (obvious how to join, what to click, when you've won); fast, playful, immediately-responsive feel.
Covers the home (create game) screen, a dedicated share/link screen, the join screen, the 5x5 player board and its cell states (unmarked, marked, free space), tap/loading feedback, a celebratory winner overlay with the winning line highlighted, the finished-game experience for non-winning players, accessibility (keyboard, focus, contrast, screen reader, 44x44 touch targets), and named empty/error states (no buzzwords configured, finished game, invalid board/game URL).
No new gameplay rules, accounts, or domain entities are introduced — this is a presentation/UX layer feature on top of the existing game built in 002-buzzword-bingo-game."

## Clarifications

### Session 2026-07-12

- Q: SC-005 describes a 9-of-10-first-time-users usability observation, which an automated Playwright suite cannot verify, while FR-020/SC-007 make automated end-to-end tests the completion gate.
  Should SC-005 still gate "feature complete," and if so how?
  → A: Keep SC-005 as an aspirational/qualitative design goal only; it does not gate completion.
  The automated end-to-end test suite (FR-020/SC-007) is the sole completion gate for this feature.
- Q: FR-010 requires an immediate loading indication on tap, but nothing resolves what happens if a player taps the same cell again before that tap's request finishes.
  Should the cell (or the whole board) become non-interactive while its request is in flight?
  → A: Disable only the tapped cell while its own request is in flight; other cells remain tappable.
- Q: What happens when the winning player dismisses the celebratory overlay (taps "Celebrate")?
  Does it reveal their board underneath, or stay up permanently?
  → A: Dismissing the overlay reveals the winner's own board underneath — now read-only, with the winning line still highlighted, consistent with how every other participant's board behaves once the game has finished.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a game and share it in seconds (Priority: P1)

An organizer arriving at the site for the first time, often on their phone right before a talk or meeting starts, types a game name and gets back a link they can immediately paste into a chat or slide, with no confusion about what to do next.

**Why this priority**: Nothing else in the product matters until an organizer can stand up a game quickly and confidently hand out the link — this is the entry point for every session.

**Independent Test**: Can be fully tested by opening the home page on a phone-sized viewport, typing a game name, submitting, and confirming a shareable link is presented with a working one-tap copy action — without needing any other part of the app to be polished.

**Acceptance Scenarios**:

1. **Given** a visitor lands on the home page, **When** the page finishes loading, **Then** the game-name field already has input focus and the on-screen keyboard (on mobile) is ready for typing.
2. **Given** the visitor has typed a game name, **When** they press Enter, **Then** the game is created exactly as if they had tapped the "Create Game" button.
3. **Given** the visitor submits a blank or whitespace-only name, **When** the form is resubmitted, **Then** a validation message appears next to the field without navigating away from the form.
4. **Given** a game has just been created, **When** the confirmation screen appears, **Then** it shows the shareable join link, a "Copy Link" action that confirms the copy succeeded, and an action to create another game.

---

### User Story 2 - Join with almost no friction (Priority: P2)

A participant taps a join link shared in a chat or shown on a slide, types their name, and is looking at their own bingo board in well under the time it takes the speaker to finish an introduction.

**Why this priority**: Every player's experience starts here; a slow or confusing join screen loses players before they ever see the game.

**Independent Test**: Can be fully tested by opening a valid join link on a phone-sized viewport, entering a name, and confirming the player lands on their own board within a few seconds, independent of how the board itself looks.

**Acceptance Scenarios**:

1. **Given** a participant opens a valid join link, **When** the page loads, **Then** the game's name is visible and the name field already has input focus.
2. **Given** the participant has typed their name, **When** they press Enter, **Then** they join exactly as if they had tapped "Join Game".
3. **Given** the participant submits a blank or whitespace-only name, **When** the form is resubmitted, **Then** a validation message appears inline without losing the game context on screen.

---

### User Story 3 - Play the board and feel the win (Priority: P3)

A player taps buzzwords as they're said, sees each tap register instantly, and — the moment they complete a row, column, or diagonal — is greeted with an unmistakable, celebratory "you won" moment that highlights exactly how they won.

**Why this priority**: This is the core, repeated interaction and the emotional payoff of the whole product; it's what makes the game fun rather than just functional.

**Independent Test**: Can be fully tested by opening an existing board, tapping several cells, and confirming each tap gives instant visual feedback; then completing a winning line and confirming the celebratory overlay and line highlight appear, independent of the create/join screens.

**Acceptance Scenarios**:

1. **Given** a player is viewing their board, **When** they tap an unmarked, non-free cell, **Then** the cell immediately shows a pending/loading state, then transitions to its marked appearance (fill, checkmark, stronger contrast) with a smooth animation once confirmed.
2. **Given** a player taps a marked cell, **When** the action completes, **Then** the cell returns to its unmarked appearance the same way.
3. **Given** the center free-space cell, **When** a player taps it, **Then** nothing changes — it is always shown already marked and does not respond to taps.
4. **Given** a player completes a full row, column, or diagonal, **When** the last mark is confirmed, **Then** a celebratory overlay appears immediately on that player's screen and the winning line is visually highlighted on their board.
5. **Given** the celebratory overlay is showing, **When** the winning player dismisses it (taps "Celebrate"), **Then** their own board is revealed underneath, read-only, with the winning line still highlighted.

---

### User Story 4 - Never hit a dead end (Priority: P4)

Whether a link is stale, a game has already finished, no buzzwords have been configured, or someone was simply too late to win, every participant always sees a clear, friendly explanation of what happened and what (if anything) they can do next — never a blank page or a technical error.

**Why this priority**: These situations happen constantly in real conference use (typos, stale links, a fast winner) and determine whether the product feels trustworthy and finished rather than broken.

**Independent Test**: Can be fully tested by visiting a nonexistent board link, a nonexistent game link, a join link for a finished game, and (with a game whose buzzword pool has been emptied) a fresh join attempt — and confirming each shows its own specific message, independent of the rest of the app working.

**Acceptance Scenarios**:

1. **Given** a game has already finished, **When** any other participant's board is open or refreshed, **Then** it shows a "game finished" notice naming the winner and the board becomes read-only.
2. **Given** someone opens a join link for a game that has already finished, **When** the join page loads, **Then** they see a message explaining the game has finished rather than a join form.
3. **Given** no active buzzwords exist to build a board, **When** someone attempts to join, **Then** they see a message explaining that no buzzwords are currently available.
4. **Given** a board or game link that does not correspond to any real game/board, **When** it is opened, **Then** a "not found" message is shown.

---

### Edge Cases

- What does the board look like on the narrowest common phone widths (e.g., ~320px), and does it stay square and legible without horizontal scrolling?
- What happens if a player's device or browser cannot access the clipboard when they tap "Copy Link"?
  The link text itself must remain visible and selectable so it can still be copied by hand.
- What happens if a player taps a cell, then taps it again before the first tap's loading state has resolved?
  The cell is disabled throughout its own pending request, so the second tap has no effect (see FR-010).
- What happens if a player is mid-tap on their board at the exact moment the game finishes (another player just won)?
  Their tap must not silently corrupt their board state, and they must end up seeing the finished-game notice.
- How does someone navigating by keyboard only, or using a screen reader, complete the entire create → share → join → play flow?
- What happens on a slow or flaky conference-wifi connection — does the loading state stay visible long enough to avoid looking broken, without ever appearing stuck?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The create-game screen MUST place input focus on the game-name field automatically when the page loads, and MUST accept submission via the Enter key in addition to an explicit submit action.
- **FR-002**: The create-game screen MUST display validation errors inline, next to the field, without navigating away from the form.
- **FR-003**: After a game is created, the system MUST present a confirmation screen showing the game's shareable join link, a "Copy Link" action that gives visible confirmation once the copy succeeds, and an action to start creating another game.
- **FR-004**: The join screen MUST display the game's name, automatically focus the player-name field on load, accept submission via the Enter key, and display validation errors inline without losing the game context on screen.
- **FR-005**: The player board screen MUST always show the game's name, the player's own name, and a brief reminder of the win condition (complete a row, column, or diagonal).
- **FR-006**: The board MUST render as a fixed 5×5 grid of square cells with consistent spacing at every supported screen size.
- **FR-007**: On wide (desktop-sized) screens the board MUST be centered with a capped maximum width; on narrow (mobile-sized) screens it MUST fill the available width while every cell remains square.
- **FR-008**: Unmarked and marked cells MUST be visually distinguishable from each other (background fill, a checkmark indicator, and stronger contrast when marked), and the change from one state to the other MUST animate smoothly rather than snap instantly.
- **FR-009**: The free (center) space MUST be visually distinct from playable cells, MUST always display as already marked, and MUST NOT respond to taps or clicks.
- **FR-010**: When a player taps or clicks a playable cell, the system MUST immediately display a pending/loading indication for that specific cell before the mark is confirmed, so the interaction feels instantaneous even under network delay.
  While that cell's request is pending, the cell MUST NOT accept another tap/click (preventing a rapid double-tap from firing a second, conflicting toggle); other cells on the board remain tappable.
- **FR-011**: Every interactive control across every screen (form fields, buttons, links, board cells) MUST be reachable and operable using only a keyboard, with a visible focus outline at each step.
- **FR-012**: Every tappable control MUST present a touch target of at least 44×44 pixels.
- **FR-013**: Text and interactive elements MUST meet accessibility contrast guidelines against their background (WCAG 2.1 AA).
- **FR-014**: Every screen MUST use semantic HTML structure with meaningful labels/roles so that form fields, the board grid, individual cells, and status/error messages are usable with a screen reader.
- **FR-015**: When a player completes a winning row, column, or diagonal, the system MUST immediately display a celebratory winner overlay on that player's screen and visually highlight the specific winning line on their board.
  Dismissing the overlay MUST reveal that player's own board underneath, read-only, with the winning line still highlighted.
- **FR-016**: Once a game has finished, every participant's board — the winner's and everyone else's — MUST become read-only (no further mark/unmark interactions).
  Every participant other than the winner MUST also see a clear notice that the game has finished, naming the winner.
- **FR-017**: When no buzzwords are available to build a board, the system MUST display a clear explanatory message instead of an incomplete board or a generic error.
- **FR-018**: When a game or board link does not correspond to a real game or board, the system MUST display a clear "not found" message rather than a generic or technical error.
- **FR-019**: The visual design MUST be consistent across all screens (rounded corners, soft shadows, generous spacing, large readable typography, subtle animations) and MUST avoid dense/cramped layouts, tiny text, and modal-heavy interaction flows.
- **FR-020**: The complete primary flow — create a game, view the share screen, join, mark squares, and reach a win — and the finished-game experience for a non-winning participant, MUST each be verified by automated end-to-end browser tests before this feature is considered complete.

## Assumptions

- This feature polishes and completes the presentation layer of the create/share/join/board flow already built in `002-buzzword-bingo-game`; it introduces no new gameplay rules, accounts, or domain entities.
- "Copy Link" uses the browser's standard clipboard mechanism; when clipboard access is unavailable, the link text remains visible and selectable so a participant can still copy it manually.
- Consistent with `002-buzzword-bingo-game`'s explicit exclusion of real-time sync, the winner overlay is shown to the winning player at the moment they complete the line; other participants learn the game has finished the next time their own client interacts with the server (e.g., viewing or refreshing their board, or attempting their next mark), not via a live push.
- The accessibility target is WCAG 2.1 Level AA.
- End-to-end verification will be performed with automated browser testing (Playwright), covering the primary flows described in the user stories above; specific test scripts and tooling setup are a planning/implementation detail, not part of this specification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time player can go from opening a join link to marking their first square in under 10 seconds, without reading any instructions.
- **SC-002**: Tapping or clicking a cell shows a visible response within 100 milliseconds, before the server confirms the change.
- **SC-003**: 100% of games that reach a winning pattern display the celebratory overlay and highlighted winning line to the winning player, and the "game finished" notice to every other participant, with no manual page refresh required to see either.
- **SC-004**: The board remains fully usable — square cells, no overflow, no horizontal scrolling — across representative mobile widths (320-430px) and on desktop up to the design's maximum board width.
- **SC-005** *(directional goal, not a completion gate — see Clarifications)*: In observation with people who have not used the app before, at least 9 of 10 successfully join a game and mark a square on their first attempt without asking for help.
- **SC-006**: Every identified empty/error state (no buzzwords available, game not found, board not found, game already finished) shows its own specific explanatory message in 100% of encounters, never a generic or technical error page.
- **SC-007**: All primary user journeys described above (create → share → join → play → win, and the finished-game experience for non-winners) pass automated end-to-end browser test coverage.
