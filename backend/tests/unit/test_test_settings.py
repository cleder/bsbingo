"""Asserts the active pytest-django settings never resolve to SQLite."""

from django.conf import settings


def test_active_settings_use_postgresql_engine() -> None:
    assert settings.DATABASES["default"]["ENGINE"].endswith("postgresql")
