# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""Minimal FastAPI application served by Uvicorn."""

import json
import logging
import multiprocessing as mp
import os
import re
import sqlite3
import secrets
import signal
import tempfile
import traceback
import zlib
from datetime import datetime
from unittest.mock import patch
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote_plus, urljoin
from xml.parsers.expat import ExpatError

import numpy
from fastapi import Body, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import (
    FileResponse, JSONResponse, PlainTextResponse, Response)
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from openquake.baselib import config, workerpool as w
from openquake.commonlib.auth import API_KEY
from openquake.baselib.general import engine_version as get_engine_version
from openquake.baselib.general import gettemp
from openquake.engine import engine
from openquake.engine.export.core import DataStoreExportError
from openquake.hazardlib import gsim, nrml, valid
from openquake.hazardlib.shakemap.validate import (
    IMPACT_FORM_DEFAULTS, impact_validate)
from openquake.commonlib import (
    dbapi, datastore, logs, oqvalidation, readinput)
from openquake.commonlib.model_provenance import read_model_provenance
from openquake.calculators import base
from openquake.server.db.registry import get_action
from openquake.server.services import (
    create_aggrisk_csv, create_extract_file, create_impact_job,
    create_impact_report_file, create_png_file,
    create_job_zip, export_result, get_exposure_by_mmi,
    get_impact_results,
    get_impact_rupture_data, get_papers_job_ctx, remove_exported,
    remove_temp_file, submit_job)
app = FastAPI(title='OpenQuake API')
app.state.adapters = {}


def configure_adapters(**adapters):
    """Register framework-specific adapters for the API endpoints."""
    app.state.adapters.update(adapters)


def _adapter(name):
    try:
        return app.state.adapters[name]
    except KeyError as exc:
        raise RuntimeError('Missing API adapter: %s' % name) from exc


def _check_api_key(api_key):
    """Raise ``HTTPException`` unless the internal API key is valid."""
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=403, detail='Invalid API key')




def validate_job(job_file):
    """Validate a calculation input and return its JSON-compatible result."""
    try:
        oq = readinput.get_oqparam(job_file)
        with patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
            base.calculators(oq, calc_id=None).run()
    except Exception as exc:
        return dict(error_msg=str(exc), error_line=None, valid=False)
    return dict(error_msg=None, error_line=None, valid=True)


def get_uploaded_file_path(request, filename):
    """Copy an uploaded file to a temporary path and return its location."""
    file = request.FILES.get(filename)
    if file:
        # NOTE: we could not find a reliable way to avoid the deletion of the
        # uploaded file right after the request is consumed, therefore we need
        # to store a copy of it
        name = getattr(file, 'name', None) or file.filename
        suffix = name[-4:]
        source = getattr(file, 'file', None)
        if source is None:
            with open(file.temporary_file_path(), 'rb') as stream:
                content = stream.read()
        else:
            source.seek(0)
            content = source.read()
        return gettemp(content, suffix=suffix)


@app.get('/v1/calc_info/{calc_id}')
def calc_info(calc_id: int, x_api_key: str | None = Header(default=None)):
    """Return calculation information."""
    _check_api_key(x_api_key)
    try:
        return logs.dbcmd('calc_info', calc_id)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


@app.get('/v0/calc/model_provenance/{calc_id}')
def v0_model_provenance(
        calc_id: int, x_api_key: str | None = Header(default=None)):
    """Return model provenance for an authenticated internal caller."""
    _check_api_key(x_api_key)
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        raise HTTPException(status_code=404)
    path = job.ds_calc_dir + '.hdf5'
    if not os.path.exists(path):
        return {
            'available': False,
            'reason': 'Model provenance metadata is not available',
        }
    try:
        with datastore.read(path) as dstore:
            summary = read_model_provenance(dstore)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logging.exception('Could not read model provenance')
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if summary is None:
        return {
            'available': False,
            'reason': 'Model provenance metadata is not available',
        }
    return {'available': True, 'summary': summary}


def _json_value(value):
    """Convert database action results to JSON-compatible values."""
    if isinstance(value, dbapi.Row):
        return {
            '__oq_type__': 'row',
            'fields': list(value._fields),
            'values': [_json_value(item) for item in value._values],
        }
    if isinstance(value, dbapi.Table):
        return {
            '__oq_type__': 'table',
            'fields': list(value._fields),
            'rows': [_json_value(row) for row in value],
        }
    if isinstance(value, datetime):
        return {'__oq_type__': 'datetime', 'value': value.isoformat()}
    if isinstance(value, sqlite3.Cursor):
        return None
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, numpy.generic):
        return value.item()
    return value


@app.post('/v0/db/{action}')
def v0_db_action(
        action: str, payload: dict | None = Body(default=None),
        x_api_key: str | None = Header(default=None)):
    """Execute an allowlisted database action."""
    _check_api_key(x_api_key)
    try:
        func = get_action(action)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = payload or {}
    args = logs._decode_db_value(payload.get('args', []))
    kwargs = logs._decode_db_value(payload.get('kwargs', {}))
    try:
        result = func(dbapi.db, *args, **kwargs)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc
    except Exception as exc:
        logging.exception('Database action failed: %s', action)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JSONResponse(content=_json_value(result))


@app.post('/v0/worker_{action}')
def v0_worker(
        action: str, payload: dict | None = Body(default=None),
        x_api_key: str | None = Header(default=None)):
    """Run an authenticated worker-control action."""
    _check_api_key(x_api_key)
    full_action = 'workers_' + action
    if full_action not in logs.WORKER_ACTIONS:
        raise HTTPException(status_code=404)
    payload = payload or {}
    args = payload.get('args', [])
    master = w.WorkerMaster(args[0] if args else -1)
    return getattr(master, action)()


async def _validate_uploaded_file(request, field, missing_message):
    """Validate one uploaded calculation file."""
    form = await request.form()
    files = {
        key: value for key, value in form.multi_items()
        if hasattr(value, 'file')}
    if field in files:
        path = get_uploaded_file_path(
            SimpleNamespace(POST=form, FILES=files), field)
    else:
        path = form.get(field)
    if not path:
        return JSONResponse(content={'detail': missing_message},
                            status_code=400)
    result = await run_in_threadpool(validate_job, path)
    return JSONResponse(content=result, status_code=200)


@app.post('/v0/calc/validate_ini')
async def v0_validate_ini(
        request: Request, x_api_key: str | None = Header(default=None)):
    """Validate an uploaded INI file for an authenticated caller."""
    _check_api_key(x_api_key)
    return await _validate_uploaded_file(
        request, 'job_ini', 'Missing job_ini file')


@app.post('/v0/calc/validate_zip')
async def v0_validate_zip(
        request: Request, x_api_key: str | None = Header(default=None)):
    """Validate an uploaded calculation archive."""
    _check_api_key(x_api_key)
    return await _validate_uploaded_file(
        request, 'archive', 'Missing archive file')


@app.post('/v0/calc/run')
async def v0_calc_run(
        request: Request, x_api_key: str | None = Header(default=None)):
    """Submit a calculation for an authenticated Django caller."""
    _check_api_key(x_api_key)
    form = await request.form()
    ini = form.get('ini') or form.get('job_ini') or '.ini'
    hazard_job_id = form.get('hazard_job_id') or None
    username = form.get('username')
    if not username:
        raise HTTPException(status_code=400,
                            detail='Missing calculation owner')
    notify_to = form.get('notify_to') or None
    request_files = form if form.getlist('archive') else []
    try:
        job_id = await run_in_threadpool(
            submit_job, request_files, ini, username, hazard_job_id, notify_to)
    except Exception as exc:
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        return JSONResponse(
            content={
                'traceback': exc_msg.splitlines(),
                'job_id': getattr(exc, 'job_id', None),
            }, status_code=500)
    return await run_in_threadpool(logs.get_job_info, job_id)


@app.post('/v0/calc/{calc_id}/abort')
def v0_calc_abort(
        calc_id: int, x_api_key: str | None = Header(default=None)):
    """Abort a running calculation for an authenticated caller."""
    _check_api_key(x_api_key)
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        return {'error': 'Unknown job %s' % calc_id}
    if job.status not in ('submitted', 'executing'):
        return {'error': 'Job %s is not running' % job.id}
    if job.pid:
        try:
            os.kill(job.pid, signal.SIGINT)
        except Exception as exc:
            logging.error(exc)
        else:
            logging.warning('Aborting job %d, pid=%d', job.id, job.pid)
            logs.dbcmd('set_status', job.id, 'aborted')
        return {'success': 'Killing job %d' % job.id}
    return {'error': 'PID for job %s not found' % job.id}


@app.post('/v0/calc/{calc_id}/remove')
def v0_calc_remove(
        calc_id: int, username: str = Form(...),
        x_api_key: str | None = Header(default=None)):
    """Remove a calculation for an authenticated caller."""
    _check_api_key(x_api_key)
    try:
        message = logs.dbcmd('del_calc', calc_id, username)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc
    if 'success' in message or 'error' in message:
        return message
    raise HTTPException(status_code=500, detail=str(message))


@app.post('/v0/calc/aelo_run')
async def v0_aelo_run(
        request: Request, x_api_key: str | None = Header(default=None)):
    """Run an AELO calculation for an authenticated Django caller."""
    _check_api_key(x_api_key)
    form = await request.form()
    username = form.get('username')
    base_url = form.get('base_url')
    if not username or not base_url:
        raise HTTPException(status_code=400,
                            detail='Missing AELO caller information')
    result = await run_in_threadpool(
        _adapter('aelo_validate'), SimpleNamespace(POST=form))
    if hasattr(result, 'status_code'):
        return JSONResponse(
            content=json.loads(result.content),
            status_code=result.status_code)
    lon, lat, site_name, asce_version, site_class, vs30 = result

    def build_absolute_uri(path):
        return urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))

    response_data, status = await run_in_threadpool(
        _adapter('run_aelo'), lon, lat, site_name, asce_version, site_class,
        vs30, username, form.get('email') or '', build_absolute_uri,
        form.get('email_file_path'))
    return JSONResponse(content=response_data, status_code=status)


@app.post('/v0/calc/run_scenario_calc_from_ses_rupture/{rup_id}')
async def v0_run_scenario(
        rup_id: int, request: Request,
        x_api_key: str | None = Header(default=None)):
    """Run a papers scenario calculation for an authenticated caller."""
    _check_api_key(x_api_key)
    form = await request.form()
    username = form.get('username')
    if not username:
        raise HTTPException(status_code=400,
                            detail='Missing calculation owner')
    papers = _adapter('papers')
    try:
        job_ctx = await run_in_threadpool(
            get_papers_job_ctx, papers, rup_id, form)
        mp.Process(target=engine.run_jobs, args=([job_ctx],), kwargs={
            'notify_to': form.get('notify_to')}).start()
        response_data = await run_in_threadpool(
            logs.get_job_info, job_ctx.calc_id)
    except Exception as exc:
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        return JSONResponse(
            content={'traceback': exc_msg.splitlines(),
                     'job_id': getattr(exc, 'job_id', None)},
            status_code=500)
    return JSONResponse(content=response_data, status_code=200)


@app.post('/v0/calc/impact_run')
async def v0_impact_run(
        request: Request, x_api_key: str | None = Header(default=None)):
    """Run IMPACT for an authenticated Django caller."""
    _check_api_key(x_api_key)
    form = await request.form()
    post = {
        key: value for key, value in form.multi_items()
        if not hasattr(value, 'file') and key not in (
            'user_level', 'username', 'email', 'base_url')}
    try:
        user_level = int(form.get('user_level', 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400,
                            detail='Invalid IMPACT user level')
    files = {
        key: value for key, value in form.multi_items()
        if hasattr(value, 'file')}
    user = SimpleNamespace(level=user_level, testdir=None)
    adapter = SimpleNamespace(POST=post, FILES=files)
    rupture_path = get_uploaded_file_path(adapter, 'rupture_file')
    if not rupture_path:
        rupture_path = post.get('rupture_from_usgs') or ''
    if rupture_path == 'None':
        rupture_path = ''
    station_path = get_uploaded_file_path(adapter, 'station_data_file')
    station_from_usgs = post.get('station_data_file_from_usgs', '')
    station_source = None
    if station_path:
        station_source = 'user-provided'
    elif station_from_usgs:
        station_path = station_from_usgs
        station_source = 'USGS'
    _rup, _rupdic, params, err = await run_in_threadpool(
        impact_validate, post, user, rupture_path, station_path)
    if err:
        return JSONResponse(
            content=err, status_code=400 if 'invalid_inputs' in err else 500)
    if station_source is not None:
        params['station_source'] = station_source
    if params.get('make_impact_reports'):
        params['postrisk_func'] = 'make_impact_reports.main'
    params['export_dir'] = config.directory.custom_tmp or tempfile.gettempdir()

    def build_absolute_uri(path):
        return urljoin(
            form.get('base_url', '').rstrip('/') + '/', path.lstrip('/'))

    def build_urls(job_id):
        return {
            'outputs_uri_web': build_absolute_uri(
                f'/engine/{job_id}/outputs_impact'),
            'outputs_uri': build_absolute_uri(
                f'/v1/calc/result/{job_id}'),
            'log_uri': build_absolute_uri(
                f'/v1/calc/{job_id}/log/0:'),
            'traceback_uri': build_absolute_uri(
                f'/v1/calc/{job_id}/traceback'),
        }

    response_data = await run_in_threadpool(
        create_impact_job, params, form.get('username'),
        form.get('email') or '', build_urls, _adapter('impact_callback'),
        form.get('email_file_path'))
    return JSONResponse(content=response_data, status_code=200)


@app.post('/v0/calc/impact_get_rupture_data')
async def v0_impact_get_rupture_data(
        request: Request, x_api_key: str | None = Header(default=None)):
    """Build IMPACT rupture data for an authenticated Django caller."""
    _check_api_key(x_api_key)
    form = await request.form()
    post = {
        key: value for key, value in form.multi_items()
        if key not in ('rupture_file', 'user_level')}
    try:
        user_level = int(form.get('user_level', 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400,
                            detail='Invalid IMPACT user level')
    user = SimpleNamespace(level=user_level, testdir=None)
    files = {
        key: value for key, value in form.multi_items()
        if hasattr(value, 'file')}
    adapter = SimpleNamespace(POST=post, FILES=files)
    rupture_path = get_uploaded_file_path(adapter, 'rupture_file')
    response_data, status = await run_in_threadpool(
        get_impact_rupture_data, post, user, rupture_path)
    return JSONResponse(content=response_data, status_code=status)


@app.get('/v1/calc_list/count')
def calc_list_count(
        request: Request,
        x_api_key: str | None = Header(default=None),
        x_valid_users: str | None = Header(default=None),
        x_user_acl_on: str | None = Header(default=None)):
    """Count calculations matching filters from the Django list view."""
    _check_api_key(x_api_key)
    try:
        valid_users = json.loads(x_valid_users or '[]')
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail='Invalid user context') from exc
    params = dict(request.query_params)
    params['count_only'] = '1'
    return logs.dbcmd(
        'get_calcs', params, valid_users,
        valid.boolean(x_user_acl_on or '1'))


@app.get('/v1/calc/list_tags')
def calc_list_tags():
    """Return all calculation tags."""
    return logs.dbcmd('list_tags')


def _calc_log_slice(calc_id, start, stop):
    """Return a calculation log slice."""
    try:
        return logs.dbcmd('get_log_slice', calc_id, start, stop)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


@app.get('/v0/calc/{calc_id}/log/size')
def calc_log_size(calc_id: int):
    """Return the number of log lines for a calculation."""
    return logs.dbcmd('get_log_size', calc_id)


@app.get('/v0/calc/{calc_id}/log/{log_range:path}')
def calc_log(calc_id: int, log_range: str,
             x_api_key: str | None = Header(default=None)):
    """Return a calculation log slice."""
    _check_api_key(x_api_key)
    try:
        start, stop = log_range.split(':', 1)
        start = int(start or 0)
        stop = int(stop or 0)
    except ValueError as exc:
        raise HTTPException(status_code=400) from exc
    return _calc_log_slice(calc_id, start, stop)


@app.get('/v0/calc/{calc_id}/traceback')
def calc_traceback(calc_id: int, x_api_key: str | None = Header(default=None)):
    """Return the traceback for a calculation."""
    _check_api_key(x_api_key)
    try:
        return logs.dbcmd('get_traceback', calc_id)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


_ACCESS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Max-Age': '1000',
    'Access-Control-Allow-Headers': '*',
}
HDF5 = 'application/x-hdf'
ZIP = 'application/x-zip'


def _with_access_headers(response):
    """Add the CORS headers used by the public calculation endpoints."""
    response.headers.update(_ACCESS_HEADERS)
    return response


def _file_access_error(status_code, content=None):
    """Build a CORS-enabled error response for a file endpoint."""
    if content is None:
        content = {403: 'Forbidden', 404: 'Not Found'}.get(
            status_code, '')
    return _with_access_headers(Response(
        content=content, status_code=status_code, media_type='text/html'))


def _retrieval_error_response(exc, resource, status_code=400):
    """Build the text error response used by datastore retrieval routes."""
    tb = ''.join(traceback.format_tb(exc.__traceback__))
    content = '%s: %s in %s\n%s' % (
        exc.__class__.__name__, exc, resource, tb)
    return _with_access_headers(PlainTextResponse(
        content, status_code=status_code))


def _json_data_response(data, request):
    """Serialize legacy API data, including non-finite float values."""
    content = json.dumps(_json_value(data), allow_nan=True)
    response = Response(content=content, media_type='application/json')
    if request.method == 'HEAD':
        response.body = b''
    return _with_access_headers(response)


def _application_mode():
    # api.py loads before Django settings are initialized by the ASGI app.
    from django.conf import settings

    return settings.APPLICATION_MODE


def _application_is_tools_only():
    return _application_mode() == 'TOOLS_ONLY'


def _with_request_user(request, authorize, *args):
    """Resolve the Django session and run a short authorization check."""
    # api.py loads before the Django ASGI application is initialized.
    from django.conf import settings
    from django.db import close_old_connections
    from openquake.server import utils

    if settings.LOCKDOWN:
        close_old_connections()
    try:
        if settings.LOCKDOWN:
            user = utils.get_user_from_session(
                request.cookies.get(settings.SESSION_COOKIE_NAME))
            if not user.is_authenticated:
                return 403, None
        else:
            user = None
        auth_request = (SimpleNamespace(user=user) if settings.LOCKDOWN
                        else SimpleNamespace())
        return authorize(auth_request, settings, utils, *args)
    finally:
        if settings.LOCKDOWN:
            close_old_connections()


def _authorize_result_download(auth_request, settings, utils, result_id):
    """Check whether a user can download a calculation result."""
    try:
        _, job_status, owner, _, ds_key = logs.dbcmd(
            'get_result', result_id)
    except dbapi.NotFound:
        return 404, None
    if not utils.user_can_view_result(
            auth_request, owner, job_status, ds_key):
        return 403, None
    return 200, None


def _authorize_datastore_download(auth_request, settings, utils, job_id):
    """Check access to a calculation datastore download."""
    user_level = utils.get_user_level(auth_request)
    if user_level < 2 and not settings.ALLOW_DATASTORE_DOWNLOAD:
        detail = '%s, %s' % (
            f'{user_level=}', f'{settings.ALLOW_DATASTORE_DOWNLOAD=}')
        return 403, detail
    job = logs.dbcmd('get_job', int(job_id))
    if job is None or not os.path.exists(job.ds_calc_dir + '.hdf5'):
        return 404, None
    if not utils.user_has_permission(
            auth_request, job.user_name, job.status):
        return 403, None
    return 200, job


def _authorize_job_zip(auth_request, settings, utils, job_id):
    """Check access to a job archive download."""
    if utils.get_user_level(auth_request) < 2:
        return 403, None
    job = logs.dbcmd('get_job', int(job_id))
    if job is None or not os.path.exists(job.ds_calc_dir + '.hdf5'):
        return 404, None
    return 200, job


def _authorize_job_access(auth_request, settings, utils, calc_id):
    """Check whether the current user can access a calculation."""
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return 404, None
    if not utils.user_has_permission(
            auth_request, job.user_name, job.status):
        return 403, None
    return 200, job


def _authorize_extract(
        auth_request, settings, utils, calc_id, what, resource):
    """Check job and resource permissions for an extract download."""
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return 404, None
    if not utils.user_has_permission(
            auth_request, job.user_name, job.status):
        return 403, None
    if (not utils.user_can_extract(auth_request, what)
            and not utils.user_can_extract(auth_request, resource)):
        return 403, None
    return 200, job


def _file_download_response(
        fname, content_type, exportname, background=None):
    """Create an attachment response for a file on disk."""
    response = FileResponse(
        fname, media_type=content_type, background=background)
    # Set the name explicitly to preserve the existing download headers.
    response.headers['content-disposition'] = (
        'attachment; filename=%s' % exportname)
    return response


def _result_file_response(result_id, export_type):
    """Build a file response for a calculation result."""
    try:
        exported = export_result(result_id, export_type)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc
    except DataStoreExportError as exc:
        # TODO: there should be a better error page
        raise HTTPException(
            status_code=500,
            detail='%s: %s' % (exc.__class__.__name__, exc)) from exc
    if exported is None:  # the requested format is not supported
        raise HTTPException(status_code=404)
    fname, content_type, exportname = exported
    return _file_download_response(
        fname, content_type, exportname,
        BackgroundTask(remove_exported, fname))


@app.api_route('/v1/calc/result/{result_id}',
               methods=['GET', 'HEAD', 'OPTIONS'], include_in_schema=False)
def public_calc_result(
        result_id: int, request: Request, export_type: str | None = None):
    """Authorize and download a calculation result for a WebUI user."""
    if _application_is_tools_only():
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())

    status, _ = _with_request_user(
        request, _authorize_result_download, result_id)
    if status != 200:
        return _file_access_error(status)

    try:
        response = _result_file_response(result_id, export_type)
    except HTTPException as exc:
        if exc.status_code == 404:
            response = Response(
                content='Not Found', status_code=404, media_type='text/html')
        else:
            response = JSONResponse(
                content={'detail': exc.detail}, status_code=exc.status_code)
            response.headers['content-type'] = 'text/plain'
    except Exception:
        logging.exception('Could not export result %s', result_id)
        response = PlainTextResponse(
            'Internal Server Error', status_code=500)
    return _with_access_headers(response)


@app.api_route('/v1/calc/{job_id}/datastore',
               methods=['GET', 'OPTIONS'], include_in_schema=False)
def public_calc_datastore(job_id: int, request: Request):
    """Download the HDF5 datastore after checking its owner permissions."""
    if _application_is_tools_only():
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    status, data = _with_request_user(
        request, _authorize_datastore_download, job_id)
    if status != 200:
        return _file_access_error(status, data)
    job = data
    fname = job.ds_calc_dir + '.hdf5'
    response = _file_download_response(
        fname, HDF5, os.path.basename(fname))
    return _with_access_headers(response)


@app.api_route('/v1/calc/{job_id}/job_zip',
               methods=['GET', 'OPTIONS'], include_in_schema=False)
def public_calc_job_zip(job_id: int, request: Request):
    """Create and download a job archive."""
    if _application_is_tools_only():
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    status, job = _with_request_user(
        request, _authorize_job_zip, job_id)
    if status != 200:
        return _file_access_error(status)
    try:
        fname = create_job_zip(job.ds_calc_dir + '.hdf5', job_id)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        content = '%s: %s in job_zip\n%s' % (
            exc.__class__.__name__, exc, tb)
        return _with_access_headers(PlainTextResponse(
            content, status_code=400))
    response = _file_download_response(
        fname, ZIP, os.path.basename(fname),
        BackgroundTask(remove_exported, fname))
    return _with_access_headers(response)


@app.api_route('/v1/calc/{calc_id}/impact',
               methods=['GET', 'HEAD', 'OPTIONS'], include_in_schema=False)
def public_impact_results(calc_id: int, request: Request):
    """Return IMPACT aggregate-risk data as JSON."""
    if _application_mode() != 'IMPACT':
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    status, job = _with_request_user(
        request, _authorize_job_access, calc_id)
    if status != 200:
        return _file_access_error(status)
    try:
        data = get_impact_results(job.ds_calc_dir + '.hdf5')
    except Exception as exc:
        return _retrieval_error_response(exc, 'aggrisk_tags')
    return _json_data_response(data, request)


@app.api_route('/v1/calc/{calc_id}/exposure_by_mmi',
               methods=['GET', 'HEAD', 'OPTIONS'], include_in_schema=False)
def public_exposure_by_mmi(calc_id: int, request: Request):
    """Return exposure aggregated by MMI region and tags."""
    if _application_mode() != 'IMPACT':
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    status, job = _with_request_user(
        request, _authorize_job_access, calc_id)
    if status != 200:
        return _file_access_error(status)
    try:
        data = get_exposure_by_mmi(job.ds_calc_dir + '.hdf5')
    except Exception as exc:
        return _retrieval_error_response(exc, 'mmi_tags')
    return _json_data_response(data, request)


@app.api_route('/v1/calc/{calc_id}/download_aggrisk',
               methods=['GET', 'OPTIONS'], include_in_schema=False)
def public_download_aggrisk(calc_id: int, request: Request):
    """Generate and download the aggregate-risk CSV."""
    if _application_mode() != 'IMPACT':
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    status, job = _with_request_user(
        request, _authorize_job_access, calc_id)
    if status != 200:
        return _file_access_error(status)
    try:
        fname = create_aggrisk_csv(job.ds_calc_dir + '.hdf5', calc_id)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        content = '%s: %s in aggrisk_tags\n%s' % (
            exc.__class__.__name__, exc, tb)
        return _with_access_headers(PlainTextResponse(
            content, status_code=400))
    response = FileResponse(
        fname, media_type='text/csv',
        background=BackgroundTask(remove_temp_file, fname))
    response.headers['content-disposition'] = (
        'attachment; filename="aggrisk_%s.csv"' % calc_id)
    return _with_access_headers(response)


@app.api_route('/v1/calc/{calc_id}/impact_report',
               methods=['GET', 'OPTIONS'], include_in_schema=False)
def public_impact_report(calc_id: int, request: Request):
    """Stream a generated IMPACT country report."""
    if _application_mode() != 'IMPACT':
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    status, job = _with_request_user(
        request, _authorize_job_access, calc_id)
    if status != 200:
        return _file_access_error(status)
    iso3 = request.query_params.get('iso3')
    if not iso3:
        return _with_access_headers(Response(
            content='Missing iso3 parameter', status_code=400,
            media_type='text/html'))
    file_format = request.query_params.get('format', 'pdf').lower()
    if file_format not in ('pdf', 'png'):
        content = (f'Invalid format parameter "{file_format}".'
                   ' Choose "pdf" or "png".')
        return _with_access_headers(Response(
            content=content, status_code=400, media_type='text/html'))
    try:
        fname = create_impact_report_file(
            job.ds_calc_dir + '.hdf5', iso3, file_format)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        content = f'{exc.__class__.__name__}: {exc}\n{tb}'
        return _with_access_headers(PlainTextResponse(
            content, status_code=400))
    content_type = (
        'image/png' if file_format == 'png' else 'application/pdf')
    response = FileResponse(
        fname, media_type=content_type,
        background=BackgroundTask(remove_temp_file, fname))
    response.headers['content-disposition'] = (
        f'inline; filename=impact_report_{iso3}.{file_format}')
    return _with_access_headers(response)


@app.api_route('/v1/calc/{calc_id}/download_png/{what:path}',
               methods=['GET', 'OPTIONS'], include_in_schema=False)
def public_download_png(calc_id: int, what: str, request: Request):
    """Render a datastore PNG resource and return it as a file."""
    if _application_is_tools_only():
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    status, job = _with_request_user(
        request, _authorize_job_access, calc_id)
    if status != 200:
        return _file_access_error(status)
    try:
        fname = create_png_file(job.ds_calc_dir + '.hdf5', what, calc_id)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        content = '%s: %s\n%s' % (exc.__class__.__name__, exc, tb)
        return _with_access_headers(PlainTextResponse(
            content, status_code=500))
    response = FileResponse(
        fname, media_type='image/png',
        background=BackgroundTask(remove_temp_file, fname))
    return _with_access_headers(response)


@app.api_route('/v1/calc/{calc_id}/extract/{what:path}',
               methods=['GET', 'HEAD', 'OPTIONS'], include_in_schema=False)
def public_calc_extract(calc_id: int, what: str, request: Request):
    """Extract a datastore resource and send it as an NPZ archive."""
    if _application_is_tools_only():
        return _file_access_error(404)
    if request.method == 'OPTIONS':
        return _with_access_headers(Response())
    query = request.url.query
    resource = what + ('?' + unquote_plus(query) if query else '')
    status, job = _with_request_user(
        request, _authorize_extract, calc_id, what, resource)
    if status != 200:
        return _file_access_error(status)
    try:
        fname = create_extract_file(
            job.ds_calc_dir + '.hdf5', resource)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        path = request.url.path
        if query:
            path += '?' + query
        content = '%s: %s in %s\n%s' % (
            exc.__class__.__name__, exc, path, tb)
        return _with_access_headers(PlainTextResponse(
            content, status_code=500))
    response = _file_download_response(
        fname, ZIP, os.path.basename(fname),
        BackgroundTask(remove_temp_file, fname))
    return _with_access_headers(response)


@app.api_route('/v0/calc/result/{result_id}', methods=['GET', 'HEAD'])
def calc_result(result_id: int, export_type: str | None = None,
                x_api_key: str | None = Header(default=None)):
    """Export a calculation result in the requested format."""
    _check_api_key(x_api_key)
    return _result_file_response(result_id, export_type)


@app.get('/v1/engine_version', response_class=PlainTextResponse)
def engine_version():
    """Return the engine version as plain text."""
    return get_engine_version()


@app.get('/v1/engine_latest_version', response_class=PlainTextResponse)
def engine_latest_version():
    """Return the latest available engine version as plain text."""
    return engine.check_obsolete_version() or ''


@app.get('/v1/aelo_site_classes')
def aelo_site_classes():
    """Return the AELO site-class definitions."""
    return oqvalidation.SITE_CLASSES


@app.get('/v1/get_impact_form_defaults')
def impact_form_defaults():
    """Return the default values for the IMPACT form."""
    return IMPACT_FORM_DEFAULTS


@app.get('/v1/available_gsims')
def available_gsims():
    """Return the names of the available GSIMs."""
    return list(gsim.get_available_gsims())


def _contains_nonfinite(value):
    """Return whether a nested value contains a non-finite float."""
    if isinstance(value, dict):
        return any(_contains_nonfinite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_nonfinite(item) for item in value)
    return (isinstance(value, (float, numpy.floating)) and
            not numpy.isfinite(value))


@app.get('/v1/ini_defaults')
def ini_defaults():
    """Return the default values of the INI parameters."""
    defaults = {}
    all_names = (dir(oqvalidation.OqParam) +
                 list(oqvalidation.OqParam.ALIASES))
    for name in all_names:
        newname = oqvalidation.OqParam.ALIASES.get(name, name)
        obj = getattr(oqvalidation.OqParam, newname)
        if (isinstance(obj, valid.Param) and
                obj.default is not valid.Param.NODEFAULT):
            if _contains_nonfinite(obj.default):
                continue
            defaults[name] = obj.default
    return defaults


@app.post('/v1/valid/')
async def validate_nrml(request: Request):
    """Validate XML supplied as the ``xml_text`` form parameter."""
    form = parse_qs((await request.body()).decode())
    xml_text = form.get('xml_text', [None])[0]
    if not xml_text:
        return PlainTextResponse(
            'Please provide the "xml_text" parameter', status_code=400)

    xml_file = gettemp(xml_text, suffix='.xml')
    try:
        nrml.to_python(xml_file)
    except ExpatError as exc:
        return {
            'error_msg': str(exc),
            'error_line': exc.lineno,
            'valid': False,
        }
    except Exception as exc:
        exc_msg = exc.args[0] if exc.args else str(exc)
        if isinstance(exc_msg, bytes):
            exc_msg = exc_msg.decode('utf-8')
        elif not isinstance(exc_msg, str):
            exc_msg = str(exc_msg)
        error_match = re.search(r'line (\d+)', exc_msg)
        error_line = int(error_match.group(1)) if error_match else None
        return {
            'error_msg': exc_msg.split(', line')[0],
            'error_line': error_line,
            'valid': False,
        }
    return {'error_msg': None, 'error_line': None, 'valid': True}


@app.post('/v1/on_same_fs')
async def on_same_fs(request: Request, x_api_key: str | None = Header(default=None)):
    """Check whether the client and server can access the same file."""
    _check_api_key(x_api_key)
    form = parse_qs((await request.body()).decode())
    filename = form.get('filename', [None])[0]
    checksum_in = form.get('checksum', [None])[0]
    checksum = 0
    try:
        with open(filename, 'rb') as stream:
            data = stream.read(32)
        checksum = zlib.adler32(data, checksum) & 0xffffffff
        success = checksum == int(checksum_in)
    except (IOError, TypeError, ValueError):
        success = False
    return {'success': success}
