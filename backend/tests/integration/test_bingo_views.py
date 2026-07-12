"""Integration tests for the bingo app's player-facing HTTP endpoints."""

from uuid import uuid4

import pytest
from bingo.models import Board, BoardSquare, Buzzword, Game, GameStatus, Player
from django.urls import reverse

CENTER_POSITION = 12

# --- User Story 1: Create a game and share it ---------------------------


@pytest.mark.django_db
def test_create_game_with_valid_name_creates_active_game_and_shows_join_url(client):
    response = client.post(reverse("bingo:create_game"), {"name": "Sprint Planning"})

    game = Game.objects.get()
    assert game.name == "Sprint Planning"
    assert game.status == GameStatus.ACTIVE
    assert f"/game/{game.id}/join/".encode() in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("blank_name", ["", "   "])
def test_create_game_with_blank_name_creates_nothing_and_shows_error(
    client,
    blank_name,
):
    response = client.post(reverse("bingo:create_game"), {"name": blank_name})

    assert response.status_code == 200
    assert not Game.objects.exists()


# --- User Story 2: Join a game and receive a personal board --------------


@pytest.fixture
def buzzword_pool(db):
    """Create 30 active buzzwords -- comfortably more than the 24 needed."""
    return [Buzzword.objects.create(text=f"word-{i}") for i in range(30)]


@pytest.fixture
def active_game(db):
    """Create a single active game to join in each test."""
    return Game.objects.create(name="Test Game")


@pytest.mark.django_db
def test_join_active_game_creates_player_board_and_25_squares(
    client,
    buzzword_pool,
    active_game,
):
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
def test_join_route_404s_for_nonexistent_or_malformed_game_id(client):
    response = client.get(f"/game/{uuid4()}/join/")
    assert response.status_code == 404

    response = client.get("/game/not-a-uuid/join/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_join_with_duplicate_display_names_creates_independent_players(
    client,
    buzzword_pool,
    active_game,
):
    join_url = reverse("bingo:join_game", args=[active_game.id])
    client.post(join_url, {"name": "Bob"})
    client.post(join_url, {"name": "Bob"})

    players = list(Player.objects.filter(game=active_game, name="Bob"))
    assert len(players) == 2
    boards = list(Board.objects.filter(player__in=players))
    assert len(boards) == 2
    assert boards[0].id != boards[1].id


@pytest.mark.django_db
def test_join_finished_game_creates_nothing_and_shows_message(client, buzzword_pool):
    finished_game = Game.objects.create(name="Done", status=GameStatus.FINISHED)

    response = client.post(
        reverse("bingo:join_game", args=[finished_game.id]),
        {"name": "Carol"},
    )

    assert response.status_code == 200
    assert not Player.objects.filter(game=finished_game).exists()
    assert b"no longer accepting participants" in response.content.lower()


@pytest.mark.django_db
@pytest.mark.parametrize("blank_name", ["", "   "])
def test_join_with_blank_display_name_creates_nothing_and_shows_error(
    client,
    buzzword_pool,
    active_game,
    blank_name,
):
    response = client.post(
        reverse("bingo:join_game", args=[active_game.id]),
        {"name": blank_name},
    )

    assert response.status_code == 200
    assert not Player.objects.filter(game=active_game).exists()


@pytest.mark.django_db
def test_join_with_insufficient_buzzword_pool_is_declined(client, active_game):
    for i in range(5):
        Buzzword.objects.create(text=f"only-{i}")

    response = client.post(
        reverse("bingo:join_game", args=[active_game.id]),
        {"name": "Dana"},
    )

    assert response.status_code == 200
    assert not Player.objects.filter(game=active_game).exists()


# --- User Story 3: Play the board and detect a winner ---------------------


@pytest.fixture
def board_factory(buzzword_pool):
    """Create fully-populated boards (25 squares, center pre-marked)."""

    def _make_board(game) -> Board:
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
    client,
    active_game,
    board_factory,
):
    board = board_factory(active_game)
    square = BoardSquare.objects.get(board=board, position=0)

    response = client.post(reverse("bingo:toggle_cell", args=[board.id, square.id]))

    square.refresh_from_db()
    assert square.marked is True
    assert response.status_code == 200
    assert b"hx-swap-oob" not in response.content


@pytest.mark.django_db
def test_toggle_completing_line_finishes_game_and_returns_winner_banner(
    client,
    active_game,
    board_factory,
):
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
    assert active_game.winner_id == board.player_id
    assert response.status_code == 200
    assert b"hx-swap-oob" in response.content


@pytest.mark.django_db
def test_toggle_after_game_finished_is_rejected(client, active_game, board_factory):
    board = board_factory(active_game)
    active_game.status = GameStatus.FINISHED
    active_game.save()
    square = BoardSquare.objects.get(board=board, position=0)

    response = client.post(reverse("bingo:toggle_cell", args=[board.id, square.id]))

    square.refresh_from_db()
    assert response.status_code == 200
    assert square.marked is False


@pytest.mark.django_db
def test_toggle_404s_for_nonexistent_malformed_or_mismatched_ids(
    client,
    active_game,
    board_factory,
):
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
def test_view_board_404s_for_nonexistent_or_malformed_board_id(client):
    response = client.get(f"/board/{uuid4()}/")
    assert response.status_code == 404

    response = client.get("/board/not-a-uuid/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_toggle_center_square_is_noop(client, active_game, board_factory):
    board = board_factory(active_game)
    center = BoardSquare.objects.get(board=board, position=CENTER_POSITION)

    response = client.post(reverse("bingo:toggle_cell", args=[board.id, center.id]))

    center.refresh_from_db()
    assert center.marked is True
    assert response.status_code == 200


@pytest.mark.django_db
def test_concurrent_winning_toggles_only_first_recorded_as_winner(
    active_game,
    board_factory,
):
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
    assert active_game.winner_id == board_a.player_id


# --- User Story 4: Manage the buzzword pool --------------------------------


@pytest.mark.django_db
def test_deactivated_buzzword_excluded_from_boards_generated_afterward(
    client,
    active_game,
):
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
def test_admin_exposes_finished_game_status_and_winner(client, django_user_model):
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
