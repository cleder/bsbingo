<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature Specification: Buzzword Bingo Game](#feature-specification-buzzword-bingo-game)
  - [Clarifications](#clarifications)
    - [Session 2026-07-12](#session-2026-07-12)
  - [User Scenarios & Testing *(mandatory)*](#user-scenarios--testing-mandatory)
    - [User Story 1 - Create a game and share it (Priority: P1)](#user-story-1---create-a-game-and-share-it-priority-p1)
    - [User Story 2 - Join a game and receive a personal board (Priority: P2)](#user-story-2---join-a-game-and-receive-a-personal-board-priority-p2)
    - [User Story 3 - Play the board and detect a winner (Priority: P3)](#user-story-3---play-the-board-and-detect-a-winner-priority-p3)
    - [User Story 4 - Manage the buzzword pool (Priority: P4)](#user-story-4---manage-the-buzzword-pool-priority-p4)
    - [Edge Cases](#edge-cases)
  - [Requirements *(mandatory)*](#requirements-mandatory)
    - [Functional Requirements](#functional-requirements)
    - [Key Entities](#key-entities)
  - [Assumptions](#assumptions)
  - [Success Criteria *(mandatory)*](#success-criteria-mandatory)
    - [Measurable Outcomes](#measurable-outcomes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Feature Specification: Buzzword Bingo Game

**Feature Branch**: `002-buzzword-bingo-game` **Created**: 2026-07-12 **Status**: Draft **Input**: User description: "Buzzword Bingo MVP — a web-based game where a user creates a bingo game, shares a join link, participants join and each receive a unique randomly generated 5×5 buzzword board, players mark buzzwords during play, the system automatically detects bingo (row/column/diagonal), and announces a winner.
No user accounts, authentication, host roles, waiting rooms, or real-time sync are in scope.
Buzzwords are managed through an admin interface."

## Clarifications

### Session 2026-07-12

- Q: What should happen when a required text field (game name, player display name) is submitted blank or whitespace-only?
  → A: Reject the submission with a validation error; redisplay the form until a non-blank value is provided.
- Q: What is the maximum acceptable response time for a cell toggle action (mark/unmark) to complete and return the updated fragment, under the 100-concurrent-participant load target?
  → A: Under 500ms.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a game and share it (Priority: P1)

A host visits the site, names a new bingo game, and immediately receives a shareable link that others can use to join.
Without this, no game can ever exist, so this is the foundation of the whole experience.

**Why this priority**: Nothing else in the product is reachable until a game exists and can be shared — this is the entry point for every other flow.

**Independent Test**: Can be fully tested by visiting the homepage, submitting a game name, and confirming a unique, shareable join link is returned — delivers value on its own as a standalone "create a session" capability.

**Acceptance Scenarios**:

1. **Given** a visitor on the homepage, **When** they submit a game name, **Then** a new game is created in an active state and a unique join link is shown to them.
2. **Given** a newly created game, **When** the host copies the join link, **Then** anyone who opens that link can reach the join flow for that specific game.

---

### User Story 2 - Join a game and receive a personal board (Priority: P2)

A participant opens the shared join link, enters their name, and is given their own randomly generated bingo board to play with, distinct from every other participant's board.

**Why this priority**: A game has no players — and therefore no gameplay — until people can join and receive a board; this is the second-most critical step after game creation.

**Independent Test**: Can be fully tested by opening a join link for an active game, submitting a display name, and confirming a personal 5×5 board is generated and displayed — delivers value as a standalone "get a board" capability.

**Acceptance Scenarios**:

1. **Given** an active game's join link, **When** a participant submits their name, **Then** a new player, and a new board with 25 squares, are created for them and they are taken to their board.
2. **Given** an active game, **When** two different participants join, **Then** each receives their own distinct board, even if they entered the same display name.
3. **Given** a game that has already finished, **When** someone opens the join link, **Then** they are told the game is no longer accepting participants and no board is created.

---

### User Story 3 - Play the board and detect a winner (Priority: P3)

A player opens their personal board and taps squares as buzzwords come up, marking and unmarking them.
The moment a full row, column, or diagonal is marked, the system recognizes the win and shows a winner announcement.

**Why this priority**: This is the core gameplay loop and payoff of the product, but it depends on games and boards already existing (User Stories 1 and 2).

**Independent Test**: Can be fully tested by opening a player's board, marking squares to complete a line, and confirming the system immediately reports a win and shows the winner — delivers the core "play and win" value on its own.

**Acceptance Scenarios**:

1. **Given** a player's board, **When** they tap an unmarked square, **Then** it becomes marked without a full page reload, and vice versa for tapping a marked square.
2. **Given** a board where marking a square completes a full row, column, or either diagonal, **When** that square is marked, **Then** the game is recognized as won, the game is marked finished, and the winner is announced.
3. **Given** a game that has already finished, **When** any player (winner or not) tries to mark or unmark a square, **Then** the request is rejected and the board is not changed.
4. **Given** a player's personal board link, **When** someone other than that player opens or submits to it, **Then** they cannot change that board's marks.

---

### User Story 4 - Manage the buzzword pool (Priority: P4)

An administrator maintains the pool of buzzwords available for boards: adding new ones, editing existing ones, and deactivating ones that should no longer appear on new boards.

**Why this priority**: Boards cannot be generated at all without a healthy pool of buzzwords, but this is a setup/maintenance activity rather than something end users experience directly, so it is lower priority than the player-facing flows.

**Independent Test**: Can be fully tested by adding, editing, and deactivating buzzwords through the management interface and confirming only active buzzwords appear on newly generated boards — delivers standalone value as a content-management capability.

**Acceptance Scenarios**:

1. **Given** the management interface, **When** an administrator adds a new buzzword, **Then** it becomes eligible to appear on boards generated afterward.
2. **Given** an existing buzzword, **When** an administrator deactivates it, **Then** it no longer appears on any newly generated board.
3. **Given** the list of games and players, **When** an administrator reviews it, **Then** they can see which games have finished and who won each one.

---

### Edge Cases

- Joining with a blank or whitespace-only display name is rejected with a validation error, and the join form is redisplayed (see FR-003).
- What happens when fewer than 25 active buzzwords exist and a new board needs to be generated?
- What happens when two players mark the winning square for their own boards at nearly the same moment — does exactly one winner get recorded?
- How does the system respond when someone opens a join link, board link, or toggle action with a well-formed but nonexistent or mistyped identifier?
- How does the system respond to a malformed (non-UUID) identifier in a join, board, or toggle URL?
- What happens if a participant tries to join the same game a second time — do they get a second, independent board?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let a visitor create a new game by supplying a non-blank game name, and MUST place every new game in an active state.
  Blank or whitespace-only game names MUST be rejected with a validation error.
- **FR-002**: The system MUST generate a unique, shareable link for each game that participants can use to join that specific game.
- **FR-003**: The system MUST let a participant join an active game by supplying a non-blank display name, without requiring an account or credentials.
  Blank or whitespace-only display names MUST be rejected with a validation error.
- **FR-004**: The system MUST allow multiple participants in the same game to use the same display name; participants are distinguished by their individual board, not by name uniqueness.
- **FR-005**: The system MUST reject attempts to join a game that has already finished, and MUST NOT create a player or board for that attempt.
- **FR-006**: Upon a participant joining, the system MUST generate a personal 5×5 (25-square) bingo board for them, populated with randomly selected, currently active buzzwords with no duplicate buzzword appearing twice on the same board.
- **FR-007**: The system MUST make the center square of every board a free space that starts already marked.
- **FR-008**: The system MUST let a player mark and unmark their own squares, and MUST reflect each change without requiring a full page reload.
- **FR-009**: The system MUST check for a winning pattern (a fully marked horizontal row, vertical column, or either diagonal) after every mark/unmark action.
- **FR-010**: When a winning pattern is completed, the system MUST mark that game as finished, record the winning player, and display a winner announcement.
- **FR-011**: The system MUST reject any further mark/unmark attempts on a game once it has finished, for every player in that game.
- **FR-012**: The system MUST only allow the participant in possession of a given board's link to mark or unmark squares on that board.
- **FR-013**: The system MUST return a not-found response for any join, board, or mark/unmark request that references a game, board, or square identifier that does not exist or is malformed.
- **FR-014**: The system MUST let an administrator create, edit, and deactivate buzzwords through a management interface, and MUST exclude deactivated buzzwords from newly generated boards.
- **FR-015**: The system MUST let an administrator view games (including their status and, once finished, their winner) and players through the management interface.
- **FR-016**: The system MUST prevent generating a new board when fewer than 25 active buzzwords exist, and MUST communicate this condition rather than generating an incomplete or duplicate-containing board.
- **FR-017**: The system MUST make illegal states unrepresentable through strict static typing and explicit domain types.

### Key Entities

- **Buzzword**: A single word or phrase eligible to appear on boards.
  Has display text and an active/inactive flag; only active buzzwords are eligible for new boards.
- **Game**: A single bingo session created by a host.
  Has a name, a status (active or finished), an optional winning player once finished, and a creation time.
  Identified by an unguessable link so only people with the link can find it.
- **Player**: A participant within one game.
  Has a display name and a join time, and belongs to exactly one game.
  Display names are not required to be unique.
- **Board**: One participant's personal bingo card, belonging to exactly one player.
  Identified by an unguessable link that acts as that player's sole means of access to their board.
- **Board Square**: One of the 25 positions on a board.
  Has a position (0-24), an assigned buzzword (or none, for the center free space), and a marked/unmarked state.

## Assumptions

- "Authentication" and "Board access" language describing control over a personal board refers to possession of that board's unguessable link (a capability URL), not to a user-account login system — the product explicitly excludes user accounts and authentication from scope.
- Exactly one winner is recorded per game: the first mark/unmark action that completes a winning pattern finishes the game and records that player as the winner; any other player's near-simultaneous completion is not recorded as a co-winner.
- When fewer than 25 active buzzwords exist at the moment a board must be generated, the join attempt is declined with an explanatory message rather than silently producing a smaller or duplicate-containing board.
- A participant may join the same active game more than once (e.g., in a different browser tab), and each join produces its own independent player and board.
- No email, SMS, or other out-of-band notification is sent to announce a winner; the winner announcement is only shown to players viewing the game/board in-app.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A host can create a game and obtain its shareable join link in under 1 minute.
- **SC-002**: A participant can go from opening a join link to seeing their personal board in under 10 seconds.
- **SC-003**: 100% of completed winning patterns (row, column, or diagonal) are detected and announced to players immediately following the mark that completed them, with no manual refresh needed.
- **SC-004**: A single game supports at least 100 simultaneous participants, each marking their own board, with each cell toggle completing and reflecting the update in under 500ms.
- **SC-005**: 100% of attempts to modify a board that is not one's own, or to modify any board after its game has finished, are rejected.
- **SC-006**: Across a sample of newly generated boards in the same game, no two boards contain an identical arrangement of buzzwords.
- **SC-007**: An administrator can add, edit, or deactivate a buzzword in under 30 seconds using the management interface.
