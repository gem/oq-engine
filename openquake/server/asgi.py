# -*- coding: utf-8 -*-
"""Combined Django and FastAPI application for Uvicorn."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openquake.server.settings')

from openquake.server.api import app  # noqa: E402

# Keep FastAPI routes first and send all unported routes to Django.
django_application = get_asgi_application()
app.mount('/', django_application)
