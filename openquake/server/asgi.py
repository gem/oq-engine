# -*- coding: utf-8 -*-
"""Combined Django and FastAPI application for Uvicorn."""

import os

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        """Do nothing when setproctitle is unavailable."""


from django.conf import settings
from django.core.asgi import get_asgi_application
from starlette.staticfiles import StaticFiles

from openquake.commonlib import dbapi
from openquake.server.db import actions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openquake.server.settings')
setproctitle('oq-webui')

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
