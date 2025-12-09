from typing import TYPE_CHECKING

import pytest

from bsbingo.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from bsbingo.users.models import User


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    return UserFactory()
