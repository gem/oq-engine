# -*- coding: utf-8 -*-
"""Combined Django and FastAPI application for Uvicorn."""

import os

from django.conf import settings
from django.core.asgi import get_asgi_application
from starlette.staticfiles import StaticFiles

from openquake.commonlib import dbapi
from openquake.server.db import actions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openquake.server.settings')

from openquake.server.api import app  # noqa: E402

# Initialize the database before starting the ASGI application.
actions.upgrade_db(dbapi.db)
# Initialize Django before reading its static-file settings.
django_application = get_asgi_application()
static_dir = settings.STATICFILES_DIRS[0]
app.mount(settings.STATIC_URL.rstrip('/'),
          StaticFiles(directory=static_dir), name='static')
# Keep FastAPI routes and static files first; send the rest to Django.
app.mount('/', django_application)
