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

from openquake.server.api import (  # noqa: E402
    app, configure_adapters, public_calc_datastore, public_calc_extract,
    public_calc_job_zip, public_calc_result, public_download_aggrisk,
    public_extract_html_table,
    public_download_png, public_exposure_by_lse, public_exposure_by_mmi,
    public_engine_get_outputs, public_impact_report,
    public_impact_results)

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
path_prefix = settings.WEBUI_PATHPREFIX.strip('/')
if path_prefix:
    prefixed_routes = (
        ('/engine/{calc_id}/outputs', public_engine_get_outputs,
         ('GET', 'OPTIONS'), 'prefixed_public_engine_get_outputs'),
        ('/v1/calc/result/{result_id}', public_calc_result,
         ('GET', 'HEAD', 'OPTIONS'), 'prefixed_public_calc_result'),
        ('/v1/calc/{job_id}/datastore', public_calc_datastore,
         ('GET', 'OPTIONS'), 'prefixed_public_calc_datastore'),
        ('/v1/calc/{job_id}/job_zip', public_calc_job_zip,
         ('GET', 'OPTIONS'), 'prefixed_public_calc_job_zip'),
        ('/v1/calc/{calc_id}/extract/{what:path}', public_calc_extract,
         ('GET', 'HEAD', 'OPTIONS'), 'prefixed_public_calc_extract'),
        ('/v1/calc/{calc_id}/download_aggrisk', public_download_aggrisk,
         ('GET', 'OPTIONS'), 'prefixed_public_download_aggrisk'),
        ('/v1/calc/{calc_id}/impact', public_impact_results,
         ('GET', 'HEAD', 'OPTIONS'), 'prefixed_public_impact_results'),
        ('/v1/calc/{calc_id}/exposure_by_mmi', public_exposure_by_mmi,
         ('GET', 'HEAD', 'OPTIONS'), 'prefixed_public_exposure_by_mmi'),
        ('/v1/calc/{calc_id}/exposure_by_lse', public_exposure_by_lse,
         ('GET', 'HEAD', 'OPTIONS'), 'prefixed_public_exposure_by_lse'),
        ('/v1/calc/{calc_id}/extract_html_table/{name:path}',
         public_extract_html_table, ('GET', 'OPTIONS'),
         'prefixed_public_extract_html_table'),
        ('/v1/calc/{calc_id}/impact_report', public_impact_report,
         ('GET', 'OPTIONS'), 'prefixed_public_impact_report'),
        ('/v1/calc/{calc_id}/download_png/{what:path}', public_download_png,
         ('GET', 'OPTIONS'), 'prefixed_public_download_png'),
    )
    for route_path, endpoint, methods, name in prefixed_routes:
        app.add_api_route(
            '/%s%s' % (path_prefix, route_path), endpoint,
            methods=methods, include_in_schema=False, name=name)
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
