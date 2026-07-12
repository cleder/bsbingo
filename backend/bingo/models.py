"""Models for the bingo app."""

from __future__ import annotations

from uuid import uuid4

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

CENTER_POSITION = 12
BOARD_SIZE = 25


class GameStatus(models.TextChoices):
    """
    Enumerates the only two legal lifecycle states of a `Game`.

    A `TextChoices` enum (rather than a bare string) makes any third
    status value unrepresentable, satisfying FR-017.
    """

    ACTIVE = "active", "Active"
    FINISHED = "finished", "Finished"


class Buzzword(models.Model):
    """
    A candidate word/phrase eligible for inclusion on newly generated boards.

    Only `active` buzzwords are drawn from when a board is generated
    (FR-006, FR-014); deactivating a word removes it from future boards
    without affecting boards that already reference it.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    text = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata for `Buzzword`."""

        ordering = ("text",)

    def __str__(self) -> str:
        """Return the buzzword's text for display in admin/shell contexts."""
        return str(self.text)


class Game(models.Model):
    """
    A single bingo session, identified by its capability URL (`id`).

    The `id` UUID doubles as the unguessable identifier embedded in the
    share/join link (`/game/<id>/join/`), per the spec's capability-URL
    access model — there is no separate authentication for players.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=10,
        choices=GameStatus.choices,
        default=GameStatus.ACTIVE,
    )
    winner = models.ForeignKey(
        "Player",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata for `Game`."""

        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Return the game's name for display in admin/shell contexts."""
        return str(self.name)


class Player(models.Model):
    """
    A single participant within one `Game`.

    Display names are intentionally not unique within a game (FR-004) —
    two participants may share a name and still get independent boards.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=100)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata for `Player`."""

        ordering = ("joined_at",)

    def __str__(self) -> str:
        """Return the player's name for display in admin/shell contexts."""
        return str(self.name)


class Board(models.Model):
    """
    A single player's 5x5 bingo board.

    The `id` UUID *is* the board's capability URL (`/board/<id>/`) — the
    participant's sole means of accessing their own board (FR-012).
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    player = models.OneToOneField(
        Player,
        on_delete=models.CASCADE,
        related_name="board",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Return a label for display in admin/shell contexts."""
        return f"Board for {self.player.name}"


class BoardSquare(models.Model):
    """
    One of the 25 cells on a `Board`.

    `buzzword` is null only for the center free space (position 12),
    which is created pre-marked and is a toggle no-op thereafter
    (research.md D5). `buzzword` uses `on_delete=PROTECT` so an admin
    can't delete a word that a board still references — deactivation is
    the intended removal path.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="squares")
    position = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    buzzword = models.ForeignKey(
        Buzzword,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
    marked = models.BooleanField(default=False)

    class Meta:
        """Model metadata for `BoardSquare`."""

        constraints = (
            models.UniqueConstraint(
                fields=("board", "position"),
                name="unique_board_position",
            ),
            models.CheckConstraint(
                condition=models.Q(position__gte=0, position__lte=24),
                name="position_range",
            ),
        )
        ordering = ("position",)

    def __str__(self) -> str:
        """Return a label for display in admin/shell contexts."""
        return f"Square {self.position} of {self.board.id}"
