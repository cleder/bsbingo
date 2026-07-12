"""
Pure domain functions for board generation and win detection.

Kept free of Django ORM/view imports per the constitution's separation-
of-concerns and functional-programming principles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence
    from random import Random

T = TypeVar("T")

_GRID_SIZE = 5

_ROWS: Final = tuple(
    frozenset(row * _GRID_SIZE + col for col in range(_GRID_SIZE))
    for row in range(_GRID_SIZE)
)
_COLUMNS: Final = tuple(
    frozenset(row * _GRID_SIZE + col for row in range(_GRID_SIZE))
    for col in range(_GRID_SIZE)
)
_DIAGONALS: Final = (
    frozenset(i * _GRID_SIZE + i for i in range(_GRID_SIZE)),
    frozenset(i * _GRID_SIZE + (_GRID_SIZE - 1 - i) for i in range(_GRID_SIZE)),
)

WINNING_LINES: Final[tuple[frozenset[int], ...]] = _ROWS + _COLUMNS + _DIAGONALS


def has_bingo(marked: frozenset[int]) -> bool:
    """
    Return whether `marked` fully contains at least one winning line.

    A pure function of the set of marked positions (research.md D4) —
    negligible cost compared to the database round-trip that produces
    it.
    """
    return any(line <= marked for line in WINNING_LINES)


def winning_lines(marked: frozenset[int]) -> frozenset[int]:
    """
    Return the union of every winning line fully contained in `marked`.

    Empty when no line is complete. Used to highlight the completed
    row/column/diagonal on a finished board (FR-015).
    """
    return frozenset[int]().union(*(line for line in WINNING_LINES if line <= marked))


class InsufficientBuzzwordPoolError(Exception):
    """Raised when fewer than `k` items are available to draw from `pool`."""

    def __init__(self, available: int, needed: int) -> None:
        """Record the shortfall so callers can render a specific message."""
        self.available = available
        self.needed = needed
        super().__init__(
            f"Need {needed} items but pool only has {available} available",
        )


def select_random_words[T](pool: Sequence[T], k: int, rng: Random) -> list[T]:
    """
    Return `k` distinct items drawn from `pool`, in random order.

    Raises `InsufficientBuzzwordPoolError` when `len(pool) < k`
    (research.md D3) — board generation must reject rather than silently
    degrade when the active buzzword pool is too small (FR-016).
    """
    if len(pool) < k:
        raise InsufficientBuzzwordPoolError(available=len(pool), needed=k)
    return rng.sample(list(pool), k)
