"""
ASGI config for the Bullshit Bingo project.

It exposes the ASGI callable as a module-level variable named
``application``. The sandbox overlay invokes this module via Gunicorn
with the Uvicorn worker class (``gunicorn config.asgi:application -k
uvicorn_worker.UvicornWorker``; see ``k8s/sandbox/kustomization.yaml``).
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_asgi_application()
