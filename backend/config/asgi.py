"""
ASGI config for the Bullshit Bingo project.

It exposes the ASGI callable as a module-level variable named
``application``. Sandbox/production already invoke this module directly
via ``daphne ... config.asgi:application`` (see
``k8s/sandbox/kustomization.yaml``).
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_asgi_application()
