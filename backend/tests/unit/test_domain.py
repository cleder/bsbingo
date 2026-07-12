"""Property-based tests for the bingo app's pure domain functions."""

import random

import pytest
from bingo.domain import (
    WINNING_LINES,
    InsufficientBuzzwordPoolError,
    has_bingo,
    select_random_words,
    winning_lines,
)
from hypothesis import given
from hypothesis import strategies as st

_POOL = st.lists(st.integers(), min_size=0, max_size=60, unique=True)


@given(pool=_POOL, k=st.integers(min_value=0, max_value=60))
def test_select_random_words_draws_k_distinct_items_only_from_pool(
    pool: list[int],
    k: int,
) -> None:
    if len(pool) < k:
        with pytest.raises(InsufficientBuzzwordPoolError):
            select_random_words(pool, k, random.Random(0))
        return

    result = select_random_words(pool, k, random.Random(0))

    assert len(result) == k
    assert len(set(result)) == k
    assert set(result) <= set(pool)


@given(line=st.sampled_from(WINNING_LINES))
def test_has_bingo_true_for_any_complete_winning_line(line: frozenset[int]) -> None:
    assert has_bingo(frozenset(line)) is True


@given(marked=st.sets(st.integers(min_value=0, max_value=24), max_size=4))
def test_has_bingo_false_when_fewer_than_a_full_line_marked(marked: set[int]) -> None:
    assert has_bingo(frozenset(marked)) is False


@given(marked=st.sets(st.integers(min_value=0, max_value=24), max_size=24))
def test_winning_lines_returns_union_of_every_fully_marked_line(
    marked: set[int],
) -> None:
    marked_fs = frozenset(marked)
    expected: frozenset[int] = frozenset[int]().union(
        *(line for line in WINNING_LINES if line <= marked_fs),
    )
    assert winning_lines(marked_fs) == expected


@given(line=st.sampled_from(WINNING_LINES))
def test_winning_lines_returns_exactly_the_one_complete_line(
    line: frozenset[int],
) -> None:
    assert winning_lines(frozenset(line)) == frozenset(line)


@given(marked=st.sets(st.integers(min_value=0, max_value=24), max_size=4))
def test_winning_lines_empty_when_fewer_than_a_full_line_marked(
    marked: set[int],
) -> None:
    assert winning_lines(frozenset(marked)) == frozenset()
