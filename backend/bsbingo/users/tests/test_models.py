from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from bsbingo.users.models import User

pytestmark = pytest.mark.django_db


def test_user_get_absolute_url(user: User) -> None:
    assert user.get_absolute_url() == f"/users/{user.username}/"
