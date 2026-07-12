"""Integration tests for the bingo app's player-facing HTTP endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from bingo.models import Board, BoardSquare, Buzzword, Game, GameStatus, Player
from django.urls import reverse

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import User
    from django.db.models import QuerySet
    from django.test import Client

CENTER_POSITION = 12

# --- User Story 1: Create a game and share it ---------------------------


@pytest.mark.django_db
def test_create_game_with_valid_name_creates_active_game_and_shows_join_url(
    client: Client,
) -> None:
    response = client.post(reverse("bingo:create_game"), {"name": "Sprint Planning"})

    game = Game.objects.get()
    assert game.name == "Sprint Planning"
    assert game.status == GameStatus.ACTIVE
    assert f"/game/{game.id}/join/".encode() in response.content
    assert b'data-testid="share-link"' in response.content
    assert b'data-testid="copy-link-button"' in response.content
    assert b'data-testid="create-another-game"' in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("blank_name", ["", "   "])
def test_create_game_with_blank_name_creates_nothing_and_shows_error(
    client: Client,
    blank_name: str,
) -> None:
    response = client.post(reverse("bingo:create_game"), {"name": blank_name})

    assert response.status_code == 200
    assert not Game.objects.exists()
    assert b'role="alert"' in response.content
    assert b'data-testid="game-name-input"' in response.content


# --- User Story 2: Join a game and receive a personal board --------------


@pytest.fixture
def buzzword_pool(db: None) -> list[Buzzword]:
    """Create 30 active buzzwords -- comfortably more than the 24 needed."""
    return [Buzzword.objects.create(text=f"word-{i}") for i in range(30)]


@pytest.fixture
def active_game(db: None) -> Game:
    """Create a single active game to join in each test."""
    return Game.objects.create(name="Test Game")


@pytest.mark.django_db
def test_join_active_game_creates_player_board_and_25_squares(
    client: Client,
    buzzword_pool: list[Buzzword],
    active_game: Game,
) -> None:
    response = client.post(
        reverse("bingo:join_game", args=[active_game.id]),
        {"name": "Alice"},
    )

    player = Player.objects.get(game=active_game)
    assert player.name == "Alice"
    board = Board.objects.get(player=player)
    assert response.status_code == 302
    assert response["Location"] == f"/board/{board.id}/"

    squares = BoardSquare.objects.filter(board=board).order_by("position")
    assert squares.count() == 25
    center = squares.get(position=12)
    assert center.marked is True
    assert center.buzzword is None
    non_center = list(squares.exclude(position=12))
    assert len(non_center) == 24
    assert all(not sq.marked for sq in non_center)
    assert all(sq.buzzword is not None for sq in non_center)
    assert len({sq.buzzword.id for sq in non_center if sq.buzzword}) == 24


@pytest.mark.django_db
def test_join_route_404s_for_nonexistent_or_malformed_game_id(client: Client) -> None:
    response = client.get(f"/game/{uuid4()}/join/")
    assert response.status_code == 404
    assert b'data-testid="not-found-notice"' in response.content

    response = client.get("/game/not-a-uuid/join/")
    assert response.status_code == 404
    assert b'data-testid="not-found-notice"' in response.content


@pytest.mark.django_db
def test_join_with_duplicate_display_names_creates_independent_players(
    client: Client,
    buzzword_pool: list[Buzzword],
    active_game: Game,
) -> None:
    join_url = reverse("bingo:join_game", args=[active_game.id])
    client.post(join_url, {"name": "Bob"})
    client.post(join_url, {"name": "Bob"})

    players = list(Player.objects.filter(game=active_game, name="Bob"))
    assert len(players) == 2
    boards = list(Board.objects.filter(player__in=players))
    assert len(boards) == 2
    assert boards[0].id != boards[1].id


@pytest.mark.django_db
def test_join_finished_game_creates_nothing_and_shows_message(
    client: Client,
    buzzword_pool: list[Buzzword],
) -> None:
    finished_game = Game.objects.create(name="Done", status=GameStatus.FINISHED)

    response = client.post(
        reverse("bingo:join_game", args=[finished_game.id]),
        {"name": "Carol"},
    )

    assert response.status_code == 200
    assert not Player.objects.filter(game=finished_game).exists()
    assert b"no longer accepting participants" in response.content.lower()
    assert b'data-testid="game-finished-notice"' in response.content


@pytest.mark.django_db
def test_join_finished_between_initial_check_and_lock_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    client: Client,
    buzzword_pool: list[Buzzword],
    active_game: Game,
) -> None:
    """
    Simulate FR-005's race window.

    Another request finishes the game after `join_game`'s initial
    (unlocked) status check but before its `select_for_update()` re-
    check inside the transaction. Without the re-check, this would
    create a `Player`/`Board` for a finished game.
    """
    real_select_for_update = Game.objects.select_for_update

    def select_for_update_after_concurrent_finish() -> QuerySet[Game]:
        Game.objects.filter(pk=active_game.id).update(status=GameStatus.FINISHED)
        return real_select_for_update()

    monkeypatch.setattr(
        Game.objects,
        "select_for_update",
        select_for_update_after_concurrent_finish,
    )

    response = client.post(
        reverse("bingo:join_game", args=[active_game.id]),
        {"name": "Eve"},
    )

    assert response.status_code == 200
    assert not Player.objects.filter(game=active_game, name="Eve").exists()
    assert b"no longer accepting participants" in response.content.lower()


@pytest.mark.django_db
@pytest.mark.parametrize("blank_name", ["", "   "])
def test_join_with_blank_display_name_creates_nothing_and_shows_error(
    client: Client,
    buzzword_pool: list[Buzzword],
    active_game: Game,
    blank_name: str,
) -> None:
    response = client.post(
        reverse("bingo:join_game", args=[active_game.id]),
        {"name": blank_name},
    )

    assert response.status_code == 200
    assert not Player.objects.filter(game=active_game).exists()
    assert b'role="alert"' in response.content
    assert b'data-testid="player-name-input"' in response.content
    assert active_game.name.encode() in response.content


@pytest.mark.django_db
def test_join_form_renders_expected_markup_anchors(
    client: Client,
    active_game: Game,
) -> None:
    response = client.get(reverse("bingo:join_game", args=[active_game.id]))

    assert response.status_code == 200
    assert b'data-testid="player-name-input"' in response.content
    assert b'data-testid="join-game-submit"' in response.content


@pytest.mark.django_db
def test_join_with_insufficient_buzzword_pool_is_declined(
    client: Client,
    active_game: Game,
) -> None:
    for i in range(5):
        Buzzword.objects.create(text=f"only-{i}")

    response = client.post(
        reverse("bingo:join_game", args=[active_game.id]),
        {"name": "Dana"},
    )

    assert response.status_code == 200
    assert not Player.objects.filter(game=active_game).exists()
    assert b'data-testid="no-buzzwords-notice"' in response.content


# --- User Story 3: Play the board and detect a winner ---------------------


@pytest.fixture
def board_factory(buzzword_pool: list[Buzzword]) -> Callable[[Game], Board]:
    """Create fully-populated boards (25 squares, center pre-marked)."""

    def _make_board(game: Game) -> Board:
        player = Player.objects.create(game=game, name=f"Player-{uuid4()}")
        board = Board.objects.create(player=player)
        words = iter(buzzword_pool)
        squares = [
            BoardSquare(
                board=board,
                position=CENTER_POSITION,
                buzzword=None,
                marked=True,
            ),
        ]
        squares.extend(
            BoardSquare(board=board, position=position, buzzword=next(words))
            for position in range(25)
            if position != CENTER_POSITION
        )
        BoardSquare.objects.bulk_create(squares)
        return board

    return _make_board


@pytest.mark.django_db
def test_toggle_non_winning_square_updates_marked_state_only(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    board = board_factory(active_game)
    square = BoardSquare.objects.get(board=board, position=0)

    response = client.post(reverse("bingo:toggle_cell", args=[board.id, square.id]))

    square.refresh_from_db()
    assert square.marked is True
    assert response.status_code == 200
    assert b"hx-swap-oob" not in response.content


@pytest.mark.django_db
def test_toggle_completing_line_finishes_game_and_returns_winner_banner(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    board = board_factory(active_game)
    row_positions = [0, 1, 2, 3, 4]
    row_squares = {
        sq.position: sq
        for sq in BoardSquare.objects.filter(board=board, position__in=row_positions)
    }
    for position in row_positions[:-1]:
        row_squares[position].marked = True
        row_squares[position].save()
    last_square = row_squares[row_positions[-1]]

    response = client.post(
        reverse("bingo:toggle_cell", args=[board.id, last_square.id]),
    )

    active_game.refresh_from_db()
    assert active_game.status == GameStatus.FINISHED
    assert active_game.winner == board.player
    assert response.status_code == 200
    assert b"hx-swap-oob" in response.content
    assert b'data-testid="winner-overlay"' in response.content
    assert b'data-testid="celebrate-dismiss"' in response.content

    content = response.content.decode()
    for position in row_positions:
        assert f'data-testid="cell-{position}"' in content
        square_html = content.split(f'data-testid="cell-{position}"')[1][:200]
        assert 'data-winning-line="true"' in square_html

    # Every square on the board -- not just the winning line -- becomes
    # read-only the instant the game ends (FR-016).
    assert 'data-testid="cell-5"' in content
    non_line_html = content.split('data-testid="cell-5"')[1][:200]
    assert "disabled" in non_line_html


@pytest.mark.django_db
def test_toggle_completing_line_after_losing_the_race_shows_finished_not_overlay(
    monkeypatch: pytest.MonkeyPatch,
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    """
    Simulate two players completing their lines concurrently.

    Only the first request's atomic `UPDATE ... WHERE status=ACTIVE` can
    actually claim the win; the second (this request) must not show the
    winner overlay to a board that didn't actually win the race -- a
    regression test for a bug where `is_winner` was hardcoded `True`.
    """
    winner_board = board_factory(active_game)
    loser_board = board_factory(active_game)
    row_positions = [0, 1, 2, 3, 4]

    loser_squares = {
        sq.position: sq
        for sq in BoardSquare.objects.filter(
            board=loser_board,
            position__in=row_positions,
        )
    }
    for position in row_positions[:-1]:
        loser_squares[position].marked = True
        loser_squares[position].save()
    last_loser_square = loser_squares[row_positions[-1]]

    real_filter = Game.objects.filter

    def filter_after_concurrent_win(*args: object, **kwargs: object) -> QuerySet[Game]:
        # Simulate the winner's concurrent request claiming the win first,
        # right before this (losing) request's own conditional UPDATE runs.
        real_filter(pk=active_game.id, status=GameStatus.ACTIVE).update(
            status=GameStatus.FINISHED,
            winner=winner_board.player,
        )
        return real_filter(*args, **kwargs)

    monkeypatch.setattr(Game.objects, "filter", filter_after_concurrent_win)

    response = client.post(
        reverse("bingo:toggle_cell", args=[loser_board.id, last_loser_square.id]),
    )

    active_game.refresh_from_db()
    assert active_game.winner == winner_board.player
    assert response.status_code == 200
    assert b'data-testid="winner-overlay"' not in response.content
    assert f"Winner: {winner_board.player.name}".encode() in response.content


@pytest.mark.django_db
def test_toggle_after_game_finished_returns_readonly_board(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    winner_board = board_factory(active_game)
    board = board_factory(active_game)
    active_game.status = GameStatus.FINISHED
    active_game.winner = winner_board.player
    active_game.save()
    square = BoardSquare.objects.get(board=board, position=0)

    response = client.post(reverse("bingo:toggle_cell", args=[board.id, square.id]))

    square.refresh_from_db()
    assert response.status_code == 200
    assert square.marked is False
    assert b"hx-swap-oob" in response.content
    assert b'data-testid="winner-overlay"' not in response.content
    assert f"Winner: {winner_board.player.name}".encode() in response.content

    content = response.content.decode()
    for position in (0, 1):
        square_html = content.split(f'data-testid="cell-{position}"')[1][:200]
        assert "disabled" in square_html


@pytest.mark.django_db
def test_toggle_via_get_is_not_allowed(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    board = board_factory(active_game)
    square = BoardSquare.objects.get(board=board, position=0)

    response = client.get(reverse("bingo:toggle_cell", args=[board.id, square.id]))

    square.refresh_from_db()
    assert response.status_code == 405
    assert square.marked is False


@pytest.mark.django_db
def test_toggle_404s_for_nonexistent_malformed_or_mismatched_ids(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    board = board_factory(active_game)
    other_board = board_factory(active_game)
    square_on_other_board = BoardSquare.objects.get(board=other_board, position=0)

    response = client.post(reverse("bingo:toggle_cell", args=[uuid4(), uuid4()]))
    assert response.status_code == 404

    response = client.post(
        reverse("bingo:toggle_cell", args=[board.id, square_on_other_board.id]),
    )
    assert response.status_code == 404

    response = client.post(f"/board/{board.id}/cell/not-a-uuid/toggle/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_view_board_404s_for_nonexistent_or_malformed_board_id(
    client: Client,
) -> None:
    response = client.get(f"/board/{uuid4()}/")
    assert response.status_code == 404
    assert b'data-testid="not-found-notice"' in response.content

    response = client.get("/board/not-a-uuid/")
    assert response.status_code == 404
    assert b'data-testid="not-found-notice"' in response.content


@pytest.mark.django_db
def test_view_board_active_game_renders_interactive_unhighlighted_board(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    board = board_factory(active_game)

    response = client.get(reverse("bingo:view_board", args=[board.id]))

    assert response.status_code == 200
    assert b'data-testid="board-readonly"' not in response.content
    assert b'data-winning-line="true"' not in response.content
    assert b'data-testid="game-name"' in response.content
    assert b'data-testid="player-name"' in response.content


@pytest.mark.django_db
def test_view_board_after_finish_marks_readonly_and_highlights_winner(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    winner_board = board_factory(active_game)
    row_positions = [0, 1, 2, 3, 4]
    BoardSquare.objects.filter(board=winner_board, position__in=row_positions).update(
        marked=True,
    )
    active_game.status = GameStatus.FINISHED
    active_game.winner = winner_board.player
    active_game.save()

    winner_response = client.get(reverse("bingo:view_board", args=[winner_board.id]))
    assert winner_response.status_code == 200
    assert b'data-testid="board-readonly"' in winner_response.content
    assert b'data-testid="winner-overlay"' in winner_response.content
    content = winner_response.content.decode()
    for position in row_positions:
        square_html = content.split(f'data-testid="cell-{position}"')[1][:200]
        assert 'data-winning-line="true"' in square_html

    # This board completes the same line independently on its own random
    # squares, but isn't the recorded winner -- it must NOT be highlighted
    # (regression test: `winning_positions` must be gated on `is_winner`,
    # not merely on the game being finished/read-only).
    other_board = board_factory(active_game)
    BoardSquare.objects.filter(board=other_board, position__in=row_positions).update(
        marked=True,
    )
    other_response = client.get(reverse("bingo:view_board", args=[other_board.id]))
    assert other_response.status_code == 200
    assert b'data-testid="board-readonly"' in other_response.content
    assert b'data-testid="winner-overlay"' not in other_response.content
    assert b'data-winning-line="true"' not in other_response.content


@pytest.mark.django_db
def test_toggle_center_square_is_noop(
    client: Client,
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    board = board_factory(active_game)
    center = BoardSquare.objects.get(board=board, position=CENTER_POSITION)

    response = client.post(reverse("bingo:toggle_cell", args=[board.id, center.id]))

    center.refresh_from_db()
    assert center.marked is True
    assert response.status_code == 200
    assert b'data-testid="free-space"' in response.content


@pytest.mark.django_db
def test_concurrent_winning_toggles_only_first_recorded_as_winner(
    active_game: Game,
    board_factory: Callable[[Game], Board],
) -> None:
    board_a = board_factory(active_game)
    board_b = board_factory(active_game)

    updated_first = Game.objects.filter(
        pk=active_game.id,
        status=GameStatus.ACTIVE,
    ).update(status=GameStatus.FINISHED, winner=board_a.player)
    updated_second = Game.objects.filter(
        pk=active_game.id,
        status=GameStatus.ACTIVE,
    ).update(status=GameStatus.FINISHED, winner=board_b.player)

    active_game.refresh_from_db()
    assert updated_first == 1
    assert updated_second == 0
    assert active_game.winner == board_a.player


# --- User Story 4: Manage the buzzword pool --------------------------------


@pytest.mark.django_db
def test_deactivated_buzzword_excluded_from_boards_generated_afterward(
    client: Client,
    active_game: Game,
) -> None:
    early_word = Buzzword.objects.create(text="early-word")

    before_player = Player.objects.create(game=active_game, name="Before")
    before_board = Board.objects.create(player=before_player)
    before_square = BoardSquare.objects.create(
        board=before_board,
        position=0,
        buzzword=early_word,
    )

    early_word.active = False
    early_word.save()

    for i in range(24):
        Buzzword.objects.create(text=f"fresh-{i}")

    response = client.post(
        reverse("bingo:join_game", args=[active_game.id]),
        {"name": "After"},
    )

    assert response.status_code == 302
    after_player = Player.objects.get(game=active_game, name="After")
    after_board = Board.objects.get(player=after_player)
    assert not BoardSquare.objects.filter(
        board=after_board,
        buzzword=early_word,
    ).exists()

    before_square.refresh_from_db()
    assert before_square.buzzword == early_word


@pytest.mark.django_db
def test_admin_exposes_finished_game_status_and_winner(
    client: Client,
    django_user_model: type[User],
) -> None:
    admin_user = django_user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password",  # noqa: S106  # pragma: allowlist secret
    )
    client.force_login(admin_user)

    game = Game.objects.create(name="Finished Game")
    player = Player.objects.create(game=game, name="Winner")
    game.status = GameStatus.FINISHED
    game.winner = player
    game.save()

    response = client.get(f"/admin/bingo/game/{game.id}/change/")
    assert response.status_code == 200
    assert b"Finished" in response.content
    assert b"Winner" in response.content

    response = client.get("/admin/bingo/player/")
    assert response.status_code == 200
    assert player.name.encode() in response.content
