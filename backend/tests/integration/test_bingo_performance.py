"""
Lightweight load/latency check for the toggle-cell endpoint (SC-004).

Simulates 100 simultaneous participants each toggling one square on their
own board, and asserts that no single toggle request exceeds the <500ms
budget -- a proxy for SC-004 without the flakiness of real thread-based
concurrency against a transactional test database.
"""

import time

import pytest
from bingo.models import Board, BoardSquare, Buzzword, Game, Player
from django.urls import reverse

PARTICIPANT_COUNT = 100
LATENCY_BUDGET_SECONDS = 0.5
CENTER_POSITION = 12


@pytest.mark.django_db
def test_toggle_cell_stays_under_latency_budget_for_many_participants(client):
    game = Game.objects.create(name="Load Test Game")
    words = [Buzzword.objects.create(text=f"word-{i}") for i in range(24)]

    boards = []
    for i in range(PARTICIPANT_COUNT):
        player = Player.objects.create(game=game, name=f"Participant-{i}")
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
                BoardSquare(board=board, position=position, buzzword=word)
                for position, word in zip(other_positions, words, strict=True)
            ),
        ]
        BoardSquare.objects.bulk_create(squares)
        boards.append(board)

    max_elapsed = 0.0
    for board in boards:
        square = BoardSquare.objects.get(board=board, position=0)
        url = reverse("bingo:toggle_cell", args=[board.id, square.id])

        start = time.perf_counter()
        response = client.post(url)
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        max_elapsed = max(max_elapsed, elapsed)

    assert max_elapsed < LATENCY_BUDGET_SECONDS
