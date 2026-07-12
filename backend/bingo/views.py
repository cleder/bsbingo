"""Views for the bingo app."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from bingo.domain import InsufficientBuzzwordPoolError, has_bingo, select_random_words
from bingo.forms import DisplayNameForm, GameNameForm
from bingo.models import Board, BoardSquare, Buzzword, Game, GameStatus, Player

if TYPE_CHECKING:
    from uuid import UUID

CENTER_POSITION = 12
BOARD_WORD_COUNT = 24


def create_game(request: HttpRequest) -> HttpResponse:
    """Render/handle the create-game form (FR-001/FR-002)."""
    if request.method == "POST":
        form = GameNameForm(request.POST)
        if form.is_valid():
            game = Game.objects.create(name=form.cleaned_data["name"])
            context = {"form": GameNameForm(), "game": game}
            return render(request, "bingo/home.html", context)
    else:
        form = GameNameForm()
    return render(request, "bingo/home.html", {"form": form})


def join_game(request: HttpRequest, game_id: UUID) -> HttpResponse:
    """Render/handle the join form for one game (FR-003-FR-007)."""
    game = get_object_or_404(Game, pk=game_id)

    if game.status == GameStatus.FINISHED:
        return render(request, "bingo/join.html", {"game": game, "finished": True})

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
                context = {"game": game, "form": form, "insufficient_pool": True}
                return render(request, "bingo/join.html", context)

            with transaction.atomic():
                player = Player.objects.create(
                    game=game,
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

            return HttpResponseRedirect(f"/board/{board.id}/")
    else:
        form = DisplayNameForm()

    return render(request, "bingo/join.html", {"game": game, "form": form})


def view_board(request: HttpRequest, board_id: UUID) -> HttpResponse:
    """Render one participant's board (FR-012)."""
    board = get_object_or_404(Board, pk=board_id)
    squares = BoardSquare.objects.filter(board=board).order_by("position")
    game = board.player.game
    context = {"board": board, "squares": squares, "game": game}
    return render(request, "bingo/board.html", context)


def toggle_cell(request: HttpRequest, board_id: UUID, cell_id: UUID) -> HttpResponse:
    """Toggle one square and detect a winning line (FR-008 through FR-011)."""
    board = get_object_or_404(Board, pk=board_id)
    square = get_object_or_404(BoardSquare, pk=cell_id, board=board)
    game = board.player.game

    if game.status == GameStatus.FINISHED or square.position == CENTER_POSITION:
        return render(request, "bingo/partials/_square.html", {"square": square})

    square.marked = not square.marked
    square.save(update_fields=["marked"])

    marked_positions = frozenset(
        BoardSquare.objects.filter(board=board, marked=True).values_list(
            "position",
            flat=True,
        ),
    )

    square_fragment = render_to_string(
        "bingo/partials/_square.html",
        {"square": square},
        request=request,
    )

    if not has_bingo(marked_positions):
        return HttpResponse(square_fragment)

    Game.objects.filter(pk=game.id, status=GameStatus.ACTIVE).update(
        status=GameStatus.FINISHED,
        winner=board.player,
    )
    game.refresh_from_db()

    banner_fragment = render_to_string(
        "bingo/partials/_winner_banner.html",
        {"game": game},
        request=request,
    )
    return HttpResponse(square_fragment + banner_fragment)
