"""
Test settings -- PostgreSQL only, never SQLite.

Selected via ``config.settings.test`` (the ``DJANGO_SETTINGS_MODULE``
set in ``[tool.pytest.ini_options]`` in the repo-root
``pyproject.toml``, or explicitly via ``--ds=config.settings.test``).
Inherits the PostgreSQL-only ``DATABASES`` and fail-fast check from
``base`` -- there is no SQLite test runner.
"""

from config.settings.base import *  # noqa: F403

DEBUG = False

# Fast, insecure hashing is fine for tests and speeds up any user-creation fixtures.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
