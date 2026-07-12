"""Views for the bingo app."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, NotRequired, TypedDict

from django.db import transaction
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse

from bingo.domain import (
    BOARD_WORD_COUNT,
    InsufficientBuzzwordPoolError,
    select_random_words,
    winning_lines,
)
from bingo.forms import DisplayNameForm, GameNameForm
from bingo.models import Board, BoardSquare, Buzzword, Game, GameStatus, Player

if TYPE_CHECKING:
    from uuid import UUID

    from django.db.models.query import QuerySet

CENTER_POSITION = 12


class _HomeContext(TypedDict):
    """Template context for `bingo/home.html` (the create-game form)."""

    form: GameNameForm
    game: NotRequired[Game]
    join_url: NotRequired[str]


class _JoinContext(TypedDict):
    """Template context for `bingo/join.html` (the join form)."""

    game: Game
    form: NotRequired[DisplayNameForm]
    finished: NotRequired[bool]
    insufficient_pool: NotRequired[bool]


class _BoardContext(TypedDict):
    """Template context for `bingo/board.html` (one participant's board)."""

    board: Board
    squares: QuerySet[BoardSquare]
    game: Game
    is_winner: bool
    is_readonly: bool
    winning_positions: frozenset[int]


class _SquareContext(TypedDict):
    """Template context for `bingo/partials/_square.html`."""

    square: BoardSquare
    winning_positions: frozenset[int]
    is_readonly: bool
    oob: NotRequired[bool]


class _WinnerBannerContext(TypedDict):
    """Template context for `bingo/partials/_winner_banner.html`."""

    game: Game
    is_winner: bool


def create_game(request: HttpRequest) -> HttpResponse:
    """Render/handle the create-game form (FR-001/FR-002)."""
    if request.method == "POST":
        form = GameNameForm(request.POST)
        if form.is_valid():
            game: Game = Game.objects.create(name=form.cleaned_data["name"])
            join_url = request.build_absolute_uri(
                reverse("bingo:join_game", args=[game.id]),
            )
            context: _HomeContext = {
                "form": GameNameForm(),
                "game": game,
                "join_url": join_url,
            }
            return render(request, "bingo/home.html", context)
    else:
        form = GameNameForm()
    return render(request, "bingo/home.html", _HomeContext(form=form))


def join_game(request: HttpRequest, game_id: UUID) -> HttpResponse:
    """Render/handle the join form for one game (FR-003-FR-007)."""
    game: Game = get_object_or_404(Game, pk=game_id)

    if game.status == GameStatus.FINISHED:
        return render(
            request,
            "bingo/join.html",
            _JoinContext(game=game, finished=True),
        )

    if request.method == "POST":
        form = DisplayNameForm(request.POST)
        if form.is_valid():
            pool = list(
                Buzzword.objects.filter(active=True).values_list("id", flat=True),
            )
            try:
                chosen = select_random_words(
                    pool,
                    BOARD_WORD_COUNT,
                    random.SystemRandom(),
                )
            except InsufficientBuzzwordPoolError:
                context: _JoinContext = {
                    "game": game,
                    "form": form,
                    "insufficient_pool": True,
                }
                return render(request, "bingo/join.html", context)

            with transaction.atomic():
                locked_game = Game.objects.select_for_update().get(pk=game_id)
                if locked_game.status == GameStatus.FINISHED:
                    return render(
                        request,
                        "bingo/join.html",
                        _JoinContext(game=locked_game, finished=True),
                    )

                player = Player.objects.create(
                    game=locked_game,
                    name=form.cleaned_data["name"],
                )
                board = Board.objects.create(player=player)
                other_positions = [p for p in range(25) if p != CENTER_POSITION]
                squares = [
                    BoardSquare(
                        board=board,
                        position=CENTER_POSITION,
                        buzzword=None,
                        marked=True,
                    ),
                    *(
                        BoardSquare(board=board, position=position, buzzword_id=word_id)
                        for position, word_id in zip(
                            other_positions,
                            chosen,
                            strict=True,
                        )
                    ),
                ]
                BoardSquare.objects.bulk_create(squares)

            return HttpResponseRedirect(reverse("bingo:view_board", args=[board.id]))
    else:
        form = DisplayNameForm()

    return render(request, "bingo/join.html", _JoinContext(game=game, form=form))


def view_board(request: HttpRequest, board_id: UUID) -> HttpResponse:
    """Render one participant's board (FR-005-009, FR-015-016)."""
    board: Board = get_object_or_404(Board, pk=board_id)
    squares: QuerySet[BoardSquare] = (
        BoardSquare.objects.filter(board=board)
        .select_related("buzzword")
        .order_by("position")
    )
    game: Game = board.player.game
    is_readonly = game.status == GameStatus.FINISHED
    is_winner = is_readonly and game.winner == board.player
    winning_positions = (
        winning_lines(
            frozenset(
                squares.filter(marked=True).values_list("position", flat=True),
            ),
        )
        if is_winner
        else frozenset()
    )
    context: _BoardContext = {
        "board": board,
        "squares": squares,
        "game": game,
        "is_winner": is_winner,
        "is_readonly": is_readonly,
        "winning_positions": winning_positions,
    }
    return render(request, "bingo/board.html", context)


def _finished_board_response(
    request: HttpRequest,
    board: Board,
    game: Game,
    clicked_square: BoardSquare,
) -> HttpResponse:
    """
    Render the read-only board and finished/winner banner for one participant.

    Shared by "this tap arrived after the game already ended" and "this
    tap just completed the winning line", so `is_winner` is always
    derived from the authoritative `game.winner` (never assumed), and
    both callers deliver the full-board read-only OOB swap (FR-016), not
    just the tapped cell.
    """
    is_winner = game.winner == board.player
    marked_positions = (
        frozenset(
            BoardSquare.objects.filter(board=board, marked=True).values_list(
                "position",
                flat=True,
            ),
        )
        if is_winner
        else frozenset()
    )
    winners = winning_lines(marked_positions) if is_winner else frozenset()

    clicked_fragment = render_to_string(
        "bingo/partials/_square.html",
        _SquareContext(
            square=clicked_square,
            winning_positions=winners,
            is_readonly=True,
        ),
        request=request,
    )
    other_fragments = "".join(
        render_to_string(
            "bingo/partials/_square.html",
            _SquareContext(
                square=other,
                winning_positions=winners,
                is_readonly=True,
                oob=True,
            ),
            request=request,
        )
        for other in BoardSquare.objects.filter(board=board)
        .select_related("buzzword")
        .exclude(pk=clicked_square.pk)
    )
    banner_fragment = render_to_string(
        "bingo/partials/_winner_banner.html",
        _WinnerBannerContext(game=game, is_winner=is_winner),
        request=request,
    )
    return HttpResponse(clicked_fragment + other_fragments + banner_fragment)


def toggle_cell(request: HttpRequest, board_id: UUID, cell_id: UUID) -> HttpResponse:
    """Toggle one square and detect a winning line (FR-008-011, FR-015-016)."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    board: Board = get_object_or_404(Board, pk=board_id)
    square: BoardSquare = get_object_or_404(BoardSquare, pk=cell_id, board=board)
    game: Game = board.player.game

    if game.status == GameStatus.FINISHED:
        return _finished_board_response(request, board, game, square)

    if square.position == CENTER_POSITION:
        return render(
            request,
            "bingo/partials/_square.html",
            _SquareContext(
                square=square,
                winning_positions=frozenset(),
                is_readonly=False,
            ),
        )

    square.marked = not square.marked
    square.save(update_fields=["marked"])

    marked_positions = frozenset(
        BoardSquare.objects.filter(board=board, marked=True).values_list(
            "position",
            flat=True,
        ),
    )
    game_now_finished = bool(winning_lines(marked_positions))

    if not game_now_finished:
        square_fragment = render_to_string(
            "bingo/partials/_square.html",
            _SquareContext(
                square=square,
                winning_positions=frozenset(),
                is_readonly=False,
            ),
            request=request,
        )
        return HttpResponse(square_fragment)

    Game.objects.filter(pk=game.id, status=GameStatus.ACTIVE).update(
        status=GameStatus.FINISHED,
        winner=board.player,
    )
    game.refresh_from_db()
    return _finished_board_response(request, board, game, square)
