"""Bulk-set every Buzzword's `active` flag (a test/CI-only utility)."""

from __future__ import annotations

from typing import override

from django.core.management.base import BaseCommand, CommandParser

from bingo.models import Buzzword


class Command(BaseCommand):
    """
    Set `active` on every `Buzzword` row.

    Exists so `frontend/e2e/dead-ends.spec.ts` can drive the app into
    the "no buzzwords configured" state (FR-017) and back again -- the
    active buzzword pool is global, admin-managed configuration with no
    player-facing UI path, so a real user flow cannot reach that state.
    """

    help = __doc__

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        """Require exactly one of `--active`/`--inactive`."""
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--active", action="store_true")
        group.add_argument("--inactive", action="store_true")

    @override
    def handle(self, *args: object, **options: object) -> None:
        """Apply the requested `active` value to every buzzword."""
        active = bool(options["active"])
        updated = Buzzword.objects.update(active=active)
        self.stdout.write(f"Set active={active} on {updated} buzzwords.")
