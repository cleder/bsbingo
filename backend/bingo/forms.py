"""
Forms for the bingo app.

Non-blank validation lives here (FR-001/FR-003) rather than at the model
level, since Django's default `CharField(blank=False)` only rejects an
empty string, not a whitespace-only one.
"""

from django import forms


class GameNameForm(forms.Form):
    """Validates the game name submitted on the create-game page (FR-001)."""

    name = forms.CharField(max_length=200, strip=True)


class DisplayNameForm(forms.Form):
    """Validates the display name submitted on the join-game page (FR-003)."""

    name = forms.CharField(max_length=100, strip=True)
