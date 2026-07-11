"""
Base Django settings shared across all environments.

Every environment (production, local development, and tests) is
PostgreSQL-only. There is no SQLite fallback anywhere -- see
``_database_config_from_env`` below.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psycopg
import psycopg.conninfo
from django.core.exceptions import ImproperlyConfigured

if TYPE_CHECKING:
    from collections.abc import Mapping

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-changeme")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


_POSTGRES_ENV_VARS = (
    "POSTGRES_HOST",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)


def _database_config_from_env(env: Mapping[str, str]) -> dict[str, Any]:
    """
    Build a Django ``DATABASES["default"]`` entry from the environment.

    Prefers ``DATABASE_URL`` -- the only connection source sandbox/production expose
    -- and falls back to discrete ``POSTGRES_*`` vars for local-dev convenience.
    Raises ``ImproperlyConfigured`` if neither source yields a complete, parseable
    PostgreSQL configuration; there is no code path that returns a SQLite engine.
    """
    database_url = env.get("DATABASE_URL")
    if database_url:
        try:
            params = psycopg.conninfo.conninfo_to_dict(database_url)
        except psycopg.ProgrammingError as exc:
            msg = f"DATABASE_URL is not a valid PostgreSQL connection string: {exc}"
            raise ImproperlyConfigured(msg) from exc
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": params.get("dbname", ""),
            "USER": params.get("user", ""),
            "PASSWORD": params.get("password", ""),
            "HOST": params.get("host", ""),
            "PORT": params.get("port", ""),
        }

    missing = [name for name in _POSTGRES_ENV_VARS if not env.get(name)]
    if missing:
        msg = (
            "PostgreSQL is not configured: set DATABASE_URL, or all of "
            f"{', '.join(_POSTGRES_ENV_VARS)}. Missing: {', '.join(missing)}."
        )
        raise ImproperlyConfigured(msg)

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env["POSTGRES_DB"],
        "USER": env["POSTGRES_USER"],
        "PASSWORD": env["POSTGRES_PASSWORD"],
        "HOST": env["POSTGRES_HOST"],
        "PORT": env.get("POSTGRES_PORT", "5432"),
    }


DATABASES = {"default": _database_config_from_env(os.environ)}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation"
        ".UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",  # Keep for username/password login
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get(
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET",
    "",
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
