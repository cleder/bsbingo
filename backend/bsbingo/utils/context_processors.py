from django.conf import LazySettings, settings


def settings_context(_request) -> dict[str, LazySettings]:
    return {"settings": settings}
