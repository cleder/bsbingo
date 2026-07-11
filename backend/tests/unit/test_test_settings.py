"""Asserts the active pytest-django settings never resolve to SQLite."""

from django.conf import settings


def test_active_settings_use_postgresql_engine():
    # Django's lazy settings proxy isn't precisely typed; DATABASES is a real dict.
    # pyrefly: ignore[bad-index, unsupported-operation]
    assert settings.DATABASES["default"]["ENGINE"].endswith("postgresql")
