# -*- coding: utf-8 -*-
"""Combined Django and FastAPI application for Uvicorn."""

import os

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        """Do nothing when setproctitle is unavailable."""


from django.conf import settings
from django.contrib.staticfiles.finders import (AppDirectoriesFinder,
                                                get_finders)
from django.core.asgi import get_asgi_application
from starlette.staticfiles import StaticFiles

from openquake.commonlib import dbapi
from openquake.server.db import actions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openquake.server.settings')
setproctitle('oq-webui')

from openquake.server.api import app, configure_adapters  # noqa: E402

# Initialize the database before starting the ASGI application.
actions.upgrade_db(dbapi.db)
# Initialize Django before reading its static-file settings.
django_application = get_asgi_application()
from openquake.server.views import (  # noqa: E402
    _run_aelo, aelo_validate, impact_callback)
from openquake.server.papers import base as papers  # noqa: E402

configure_adapters(
    aelo_validate=aelo_validate,
    run_aelo=_run_aelo,
    impact_callback=impact_callback,
    papers=papers)
static_dir = settings.STATICFILES_DIRS[0]
static_packages = []
# Include the static directories supplied by installed Django apps.  The
# templates from the tools use paths such as ``ipt/css/ipt.css`` and these
# files are not copied into the engine's static directory at install time.
for finder in get_finders():
    if isinstance(finder, AppDirectoriesFinder):
        static_packages.extend(
            (package, 'static') for package in finder.storages)
app.mount(settings.STATIC_URL.rstrip('/'), StaticFiles(
    directory=static_dir, packages=static_packages), name='static')
# Keep FastAPI routes and static files first; send the rest to Django.
app.mount('/', django_application)
