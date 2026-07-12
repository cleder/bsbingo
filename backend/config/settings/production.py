"""Production settings: security hardening on the shared Postgres base."""

import os

from django.core.exceptions import ImproperlyConfigured

from config.settings.base import *  # noqa: F403

_INSECURE_SECRET_KEY_DEFAULT = "django-insecure-changeme"  # noqa: S105  # pragma: allowlist secret

if os.environ.get("DJANGO_SECRET_KEY", _INSECURE_SECRET_KEY_DEFAULT) in (
    "",
    _INSECURE_SECRET_KEY_DEFAULT,
):
    msg = (
        "DJANGO_SECRET_KEY must be set to a unique, unpredictable value in production."
    )
    raise ImproperlyConfigured(msg)

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 week
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
