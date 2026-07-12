"""
Integration test for config.settings.production.

Relies on the DATABASE_URL already present in the pytest run's
environment (the same env pytest-django used to load
config.settings.test at session start) -- production.py inherits
DATABASES from base via a star import, so this proves production never
overrides it back to SQLite.
"""

from config.settings import production


def test_production_settings_use_postgresql() -> None:
    assert production.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"


def test_production_settings_disable_debug() -> None:
    assert production.DEBUG is False
