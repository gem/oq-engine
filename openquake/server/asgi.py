# -*- coding: utf-8 -*-
"""Combined Django and FastAPI application for Uvicorn."""

import os

from django.conf import settings
from django.contrib.staticfiles.finders import (AppDirectoriesFinder,
                                                get_finders)
from django.core.asgi import get_asgi_application
from starlette.staticfiles import StaticFiles

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openquake.server.settings')

from openquake.server.api import app  # noqa: E402

# Initialize Django before reading its static-file settings.
django_application = get_asgi_application()
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
