"""
Property-based and unit tests for the DATABASE_URL/POSTGRES_* config parser.

These exercise ``_database_config_from_env`` directly with fabricated
environment mappings, independent of the real process environment, so
fail-fast behavior can be tested for every input shape without touching
``os.environ``.
"""

import pytest
from config.settings.base import _database_config_from_env
from django.core.exceptions import ImproperlyConfigured
from hypothesis import given
from hypothesis import strategies as st

_SAFE_IDENTIFIER = st.from_regex(r"[a-zA-Z0-9_]{1,20}", fullmatch=True)
_POSTGRES_VAR_NAMES = (
    "POSTGRES_HOST",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)


@given(
    user=_SAFE_IDENTIFIER,
    password=_SAFE_IDENTIFIER,
    host=_SAFE_IDENTIFIER,
    port=st.integers(min_value=1, max_value=65535),
    dbname=_SAFE_IDENTIFIER,
)
def test_database_url_is_parsed_into_postgres_config(
    user: str,
    password: str,
    host: str,
    port: int,
    dbname: str,
) -> None:
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    config = _database_config_from_env({"DATABASE_URL": database_url})

    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["NAME"] == dbname
    assert config["USER"] == user
    assert config["PASSWORD"] == password
    assert config["HOST"] == host
    assert config["PORT"] == str(port)


@given(
    host=_SAFE_IDENTIFIER,
    dbname=_SAFE_IDENTIFIER,
    user=_SAFE_IDENTIFIER,
    password=_SAFE_IDENTIFIER,
)
def test_discrete_postgres_vars_are_used_when_database_url_is_absent(
    host: str,
    dbname: str,
    user: str,
    password: str,
) -> None:
    config = _database_config_from_env(
        {
            "POSTGRES_HOST": host,
            "POSTGRES_DB": dbname,
            "POSTGRES_USER": user,
            "POSTGRES_PASSWORD": password,
        }
    )

    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["NAME"] == dbname
    assert config["USER"] == user
    assert config["HOST"] == host
    assert config["PORT"] == "5432"


def test_database_url_takes_precedence_over_discrete_vars() -> None:
    url = "postgresql://urluser:urlpass@urlhost:5432/urldb"  # pragma: allowlist secret
    config = _database_config_from_env(
        {
            "DATABASE_URL": url,
            "POSTGRES_HOST": "ignored-host",
            "POSTGRES_DB": "ignored-db",
            "POSTGRES_USER": "ignored-user",
            "POSTGRES_PASSWORD": "ignored-password",  # pragma: allowlist secret
        }
    )

    assert config["NAME"] == "urldb"
    assert config["HOST"] == "urlhost"


def test_missing_database_url_and_postgres_vars_raises_improperly_configured() -> None:
    with pytest.raises(ImproperlyConfigured):
        _database_config_from_env({})


@given(present_var=st.sampled_from(_POSTGRES_VAR_NAMES))
def test_partial_postgres_vars_raises_improperly_configured(present_var: str) -> None:
    with pytest.raises(ImproperlyConfigured):
        _database_config_from_env({present_var: "something"})


def test_malformed_database_url_raises_improperly_configured() -> None:
    with pytest.raises(ImproperlyConfigured):
        _database_config_from_env({"DATABASE_URL": "not a valid postgres dsn ??"})


def test_no_code_path_ever_produces_sqlite_engine() -> None:
    config = _database_config_from_env({"DATABASE_URL": "postgresql://u:p@h:5432/d"})
    assert config["ENGINE"] != "django.db.backends.sqlite3"
