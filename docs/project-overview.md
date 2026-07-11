<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Buzzword Bingo MVP Specification](#buzzword-bingo-mvp-specification)
  - [1. Overview](#1-overview)
  - [Goal](#goal)
  - [2. Scope](#2-scope)
    - [In Scope](#in-scope)
    - [Out of Scope](#out-of-scope)
  - [3. User Flows](#3-user-flows)
    - [Create Game](#create-game)
      - [Flow](#flow)
      - [Acceptance Criteria](#acceptance-criteria)
    - [Join Game](#join-game)
      - [Flow](#flow-1)
      - [Acceptance Criteria](#acceptance-criteria-1)
    - [Play Game](#play-game)
      - [Flow](#flow-2)
      - [Acceptance Criteria](#acceptance-criteria-2)
  - [4. Data Model](#4-data-model)
    - [Buzzword](#buzzword)
      - [Rules](#rules)
    - [Game](#game)
    - [Player](#player)
    - [Board](#board)
    - [BoardCell](#boardcell)
  - [5. Board Generation](#5-board-generation)
    - [Rules](#rules-1)
  - [6. Bingo Detection](#6-bingo-detection)
  - [7. HTMX Interactions](#7-htmx-interactions)
    - [Toggle Cell](#toggle-cell)
  - [8. URL Structure](#8-url-structure)
  - [9. Django Admin](#9-django-admin)
  - [10. Non-Functional Requirements](#10-non-functional-requirements)
    - [Technology](#technology)
    - [Performance](#performance)
    - [Security](#security)
  - [11. Definition of Done](#11-definition-of-done)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Buzzword Bingo MVP Specification

## 1. Overview

## Goal

Build a simple web-based Buzzword Bingo game using Django and HTMX.

The MVP allows a user to:

1. Create a bingo game.
2. Share a game link.
3. Allow participants to join.
4. Generate a unique bingo board for each participant.
5. Mark buzzwords during gameplay.
6. Detect bingo automatically.
7. Announce the winner.

The application uses server-rendered Django templates with HTMX for dynamic interactions.
No frontend framework is required.

---

## 2. Scope

### In Scope

- Game creation
- Joining games through a URL
- Random bingo board generation
- Player board interaction
- HTMX-based cell updates
- Bingo detection
- Winner announcement
- Django admin management of buzzwords

### Out of Scope

- User accounts
- Authentication
- Host roles
- Waiting rooms
- Player lists
- Explicit game start
- Real-time synchronization
- WebSockets
- Server-Sent Events
- Polling
- Statistics
- Leaderboards
- Custom word uploads
- Printable boards
- Mobile applications

---

## 3. User Flows

### Create Game

#### Flow

1. User visits the homepage.
2. User enters a game name.
3. User submits the form.
4. The system creates a new game.
5. The user receives a shareable join URL.

Example:

```text
/game/8f2e6b8a-3d44-4f4e-a1c8-2a9d7f6c5e11/join/
```

#### Acceptance Criteria

- A game is created with status `active`.
- The game receives a unique UUID.
- The user can copy and share the join URL.

---

### Join Game

#### Flow

1. Participant opens the join URL.
2. Participant enters their name.
3. The system creates:

   - a player
   - a board
   - board cells
4. Participant is redirected to their board.

#### Acceptance Criteria

- Player name is required.
- Each player receives a unique board.
- Multiple players may have the same name.
- Players can join while the game is active.
- Finished games cannot accept new players.

---

### Play Game

#### Flow

1. Player opens their board URL.
2. Player clicks buzzword squares.
3. Squares toggle between marked and unmarked.
4. The server checks for bingo after every move.
5. If a winning pattern exists, the game ends.

Example board URL:

```text
/board/5b97b663-1f2f-4e54-8d2f-f45f3272f870/
```

#### Acceptance Criteria

- Board updates without a full page reload.
- Only the owner of the board URL can modify that board.
- Finished games cannot be modified.

---

## 4. Data Model

### Buzzword

Stores available buzzwords.

| Field      | Type     |
| ---------- | -------- |
| id         | UUID     |
| text       | String   |
| active     | Boolean  |
| created_at | DateTime |

#### Rules

- Only active buzzwords are used.
- A minimum of 25 active buzzwords must exist.

---

### Game

Represents a bingo session.

| Field      | Type                              |
| ---------- | --------------------------------- |
| id         | UUID                              |
| name       | String                            |
| status     | Enum                              |
| winner     | ForeignKey(Player, nullable=True) |
| created_at | DateTime                          |

Status:

```text
active
finished
```

---

### Player

Represents a participant.

| Field     | Type             |
| --------- | ---------------- |
| id        | UUID             |
| game      | ForeignKey(Game) |
| name      | String           |
| joined_at | DateTime         |

---

### Board

Represents a player's bingo card.

| Field      | Type             |
| ---------- | ---------------- |
| id         | UUID             |
| player     | OneToOne(Player) |
| created_at | DateTime         |

The board UUID is used as a capability URL.

Example:

```text
/board/<board_uuid>/
```

Authentication is required.

---

### BoardCell

Represents an individual square.

| Field    | Type                                |
| -------- | ----------------------------------- |
| id       | UUID                                |
| board    | ForeignKey(Board)                   |
| position | Integer                             |
| buzzword | ForeignKey(Buzzword, nullable=True) |
| marked   | Boolean                             |

Position range:

```text
0 - 24
```

---

## 5. Board Generation

### Rules

- Board size is fixed at 5×5.
- Total cells: 25.
- Center cell is a free space.
- Center cell starts marked.
- Remaining 24 cells contain random buzzwords.
- No duplicate buzzwords exist on the same board.

Example:

```text
+-----+-----+-----+-----+-----+
| AI  | ROI | SaaS| Cloud| API |
+-----+-----+-----+-----+-----+
| ... | ... | ... | ... | ... |
+-----+-----+-----+-----+-----+
| ... | ... |FREE | ... | ... |
+-----+-----+-----+-----+-----+
| ... | ... | ... | ... | ... |
+-----+-----+-----+-----+-----+
| ... | ... | ... | ... | ... |
+-----+-----+-----+-----+-----+
```

---

## 6. Bingo Detection

The system checks for winning patterns after every cell update.

Supported patterns:

- Horizontal line
- Vertical line
- Diagonal top-left → bottom-right
- Diagonal top-right → bottom-left

A win occurs when all cells in a line are marked.

Example:

```text
X X X X X
```

---

## 7. HTMX Interactions

### Toggle Cell

Endpoint:

```text
POST /board/<board_uuid>/cell/<cell_uuid>/toggle/
```

Behaviour:

1. Validate board access.
2. Toggle cell state.
3. Check bingo status.
4. Return updated HTML fragment.

Response:

- Updated cell fragment.
- Optional winner banner fragment.

---

## 8. URL Structure

```text
/
└── Create Game

/game/<game_uuid>/join/
└── Join Form

/board/<board_uuid>/
└── Player Board

/board/<board_uuid>/cell/<cell_uuid>/toggle/
└── HTMX Cell Toggle
```

---

## 9. Django Admin

The admin interface provides management of:

- Buzzwords
- Games
- Players
- Boards

Required functionality:

- Create/edit/deactivate buzzwords.
- Inspect active games.
- View winners.

---

## 10. Non-Functional Requirements

### Technology

- Django
- HTMX
- Django Templates
- Django Admin
- PostgreSQL

### Performance

- Board updates should complete quickly under normal usage.
- A game should support at least 100 participants.

### Security

- UUIDs must be used for public URLs.
- Board access is controlled through possession of the board URL and authentication.
- Invalid UUIDs return HTTP 404.
- Finished games reject updates.

---

## 11. Definition of Done

The MVP is complete when:

1. A user can create a game.
2. A shareable join URL is generated.
3. Players can join without accounts.
4. Each player receives a unique bingo board.
5. Players can mark/unmark cells using HTMX.
6. Bingo is detected automatically.
7. The winner is displayed.
8. Finished games prevent further changes.
9. Buzzwords can be managed through Django admin.
