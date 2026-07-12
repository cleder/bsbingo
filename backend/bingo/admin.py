"""Admin registrations for the bingo app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin

from bingo.models import Board, BoardSquare, Buzzword, Game, Player

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest


@admin.action(description="Mark selected buzzwords as active")
def make_active(
    _modeladmin: admin.ModelAdmin,
    _request: HttpRequest,
    queryset: QuerySet[Buzzword],
) -> None:
    """Bulk-activate the selected buzzwords, making them eligible again."""
    queryset.update(active=True)


@admin.action(description="Mark selected buzzwords as inactive")
def make_inactive(
    _modeladmin: admin.ModelAdmin,
    _request: HttpRequest,
    queryset: QuerySet[Buzzword],
) -> None:
    """Deactivate the selected buzzwords, excluding them from new boards."""
    queryset.update(active=False)


@admin.register(Buzzword)
class BuzzwordAdmin(admin.ModelAdmin):
    """Manage the pool of buzzwords eligible for new boards (FR-014)."""

    list_display = ("text", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("text",)
    actions = (make_active, make_inactive)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Read-mostly visibility into a game's status and winner (FR-015)."""

    list_display = ("name", "status", "winner", "created_at")
    list_filter = ("status",)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Read-mostly visibility into a game's participants (FR-015)."""

    list_display = ("name", "game", "joined_at")
    list_filter = ("game",)


class BoardSquareInline(admin.TabularInline):
    """Read-only inline listing of a board's 25 squares (research.md D9)."""

    model = BoardSquare
    extra = 0
    can_delete = False
    readonly_fields = ("position", "buzzword", "marked")


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Support/inspection view of a player's board (research.md D9)."""

    list_display = ("player", "created_at")
    inlines = (BoardSquareInline,)
