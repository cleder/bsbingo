from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "bsbingo.users"
    verbose_name = _("Users")

    def ready(self) -> None:
        try:
            import bsbingo.users.signals  # noqa: F401
        except ImportError:
            pass
