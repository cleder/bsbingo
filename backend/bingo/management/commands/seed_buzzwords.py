"""Idempotently ensure enough active buzzwords exist to generate a board."""

from __future__ import annotations

from typing import override

from django.core.management.base import BaseCommand

from bingo.domain import BOARD_WORD_COUNT
from bingo.models import Buzzword

_DEFAULT_COUNT = 40


class Command(BaseCommand):
    """
    Ensure at least `BOARD_WORD_COUNT` active buzzwords exist.

    Real deployments configure buzzwords through the admin; local/e2e
    test environments have no such data-entry step, so this command
    exists to make a freshly migrated database immediately joinable
    (e2e's Playwright `globalSetup` calls this before the suite runs).
    """

    help = __doc__

    @override
    def handle(self, *args: object, **options: object) -> None:
        """Create buzzwords until at least `BOARD_WORD_COUNT` are active."""
        active_count = Buzzword.objects.filter(active=True).count()
        if active_count >= BOARD_WORD_COUNT:
            self.stdout.write(
                f"Already have {active_count} active buzzwords; nothing to do.",
            )
            return

        needed = max(_DEFAULT_COUNT - active_count, BOARD_WORD_COUNT - active_count)
        existing_texts = set(Buzzword.objects.values_list("text", flat=True))
        created = 0
        candidate = 0
        new_words: list[Buzzword] = []
        while created < needed:
            text = f"buzzword-{candidate}"
            candidate += 1
            if text in existing_texts:
                continue
            new_words.append(Buzzword(text=text, active=True))
            created += 1
        Buzzword.objects.bulk_create(new_words)
        self.stdout.write(f"Created {created} active buzzwords.")
