"""
Integration test for config.settings.local.

See test_production_settings.py for why no monkeypatching/reload is
needed here.
"""

from config.settings import local


def test_local_settings_use_postgresql():
    assert local.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"


def test_local_settings_enable_debug():
    assert local.DEBUG is True
