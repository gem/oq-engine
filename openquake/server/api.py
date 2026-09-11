# -*- coding: utf-8 -*-
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
"""Minimal FastAPI application served by the DbServer."""

import json
import logging
import multiprocessing as mp
import os
import re
import secrets
import signal
import tempfile
import traceback
import zlib
from types import SimpleNamespace
from urllib.parse import parse_qs, urljoin
from xml.parsers.expat import ExpatError

import numpy
from fastapi import FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from openquake.baselib import config, workerpool as w
from openquake.commonlib.auth import API_KEY
from openquake.baselib.general import engine_version as get_engine_version
from openquake.baselib.general import gettemp
from openquake.engine import engine
from openquake.hazardlib import gsim, nrml, valid
from openquake.hazardlib.shakemap.validate import (
    IMPACT_FORM_DEFAULTS, impact_validate)
from openquake.commonlib import dbapi, logs, oqvalidation

app = FastAPI(title='OpenQuake API')


def _check_api_key(api_key):
    """Raise ``HTTPException`` unless the internal API key is valid."""
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=403, detail='Invalid API key')


@app.get('/v1/calc_info/{calc_id}')
def calc_info(calc_id: int):
    """Return calculation information."""
    try:
        return logs.dbcmd('calc_info', calc_id)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


@app.post('/v0/worker_{action}')
async def v0_worker(
        action: str, request: Request,
        x_api_key: str | None = Header(default=None)):
    """Run an authenticated worker-control action."""
    _check_api_key(x_api_key)
    full_action = 'workers_' + action
    if full_action not in logs.WORKER_ACTIONS:
        raise HTTPException(status_code=404)
    body = await request.body()
    payload = json.loads(body) if body else {}
    args = payload.get('args', [])
    master = w.WorkerMaster(args[0] if args else -1)
    return getattr(master, action)()


async def _validate_uploaded_file(request, field, missing_message):
    """Validate one uploaded calculation file."""
    form = await request.form()
    files = {
        key: value for key, value in form.multi_items()
        if hasattr(value, 'file')}
    from openquake.server.views import get_uploaded_file_path, validate_job
    path = (get_uploaded_file_path(
        SimpleNamespace(POST=form, FILES=files), field)
        if field in files else form.get(field))
    if not path:
        return JSONResponse(
            content={'detail': missing_message}, status_code=400)
    result = await run_in_threadpool(validate_job, path)
    return JSONResponse(content=result, status_code=200)


@app.post('/v0/calc/validate_ini')
async def v0_validate_ini(
        request: Request, x_api_key: str | None = Header(default=None)):
    """Validate an uploaded INI file."""
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


@app.post('/v0/calc/run_scenario_calc_from_ses_rupture/{rup_id}')
async def v0_run_scenario(
        rup_id: int, request: Request,
        x_api_key: str | None = Header(default=None)):
    """Run a papers scenario calculation."""
    _check_api_key(x_api_key)
    form = await request.form()
    username = form.get('username')
    if not username:
        raise HTTPException(status_code=400,
                            detail='Missing calculation owner')
    from openquake.server.papers import base as papers
    consequence_model = form.get('consequence_model')
    consequence = (json.loads(consequence_model)
                   if consequence_model else papers.CONSEQUENCE)
    try:
        job_ctx = await run_in_threadpool(
            papers.get_job_ctx, rup_id, papers.FNAME, papers.GMM_LT,
            papers.SITE_MODEL, papers.IMTS_RISK, papers.INTEGRATION_DISTANCE,
            papers.TRUNCATION, papers.NGMFS,
            form.get('exposure_filepath', papers.EXPOSURE),
            form.get('mapping', papers.MAPPING),
            form.get('fragility_curves', papers.FRAGILITY), consequence,
            papers.HAZARD_ONLY, username)
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
    from openquake.server.views import submit_job
    request_files = form if form.getlist('archive') else []
    try:
        job_id = submit_job(
            request_files, ini, username, hazard_job_id, notify_to)
    except Exception as exc:
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        return JSONResponse(
            content={
                'traceback': exc_msg.splitlines(),
                'job_id': getattr(exc, 'job_id', None),
            }, status_code=500)
    return logs.get_job_info(job_id)


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
    from openquake.server.views import aelo_validate, _run_aelo
    result = aelo_validate(SimpleNamespace(POST=form))
    if hasattr(result, 'status_code'):
        return JSONResponse(
            content=json.loads(result.content),
            status_code=result.status_code)
    lon, lat, site_name, asce_version, site_class, vs30 = result

    def build_absolute_uri(path):
        return urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))

    response_data, status = _run_aelo(
        lon, lat, site_name, asce_version, site_class, vs30,
        username, form.get('email') or '', build_absolute_uri,
        form.get('email_file_path'))
    return JSONResponse(content=response_data, status_code=status)


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
    from openquake.server.views import (
        create_impact_job, get_uploaded_file_path)
    user = SimpleNamespace(level=user_level, testdir=None)
    adapter = SimpleNamespace(POST=post, FILES=files)
    rupture_path = get_uploaded_file_path(adapter, 'rupture_file')
    station_path = get_uploaded_file_path(adapter, 'station_data_file')
    station_from_usgs = post.get('station_data_file_from_usgs', '')
    station_source = None
    if station_path:
        station_source = 'user-provided'
    elif station_from_usgs:
        station_path = station_from_usgs
        station_source = 'USGS'
    _rup, _rupdic, params, err = impact_validate(
        post, user, rupture_path, station_path)
    if err:
        return JSONResponse(
            content=err, status_code=400 if 'invalid_inputs' in err else 500)
    if station_source is not None:
        params['station_source'] = station_source
    params['export_dir'] = config.directory.custom_tmp or tempfile.gettempdir()

    def build_absolute_uri(path):
        return urljoin(
            form.get('base_url', '').rstrip('/') + '/', path.lstrip('/'))

    job_request = SimpleNamespace(
        POST=form,
        user=SimpleNamespace(
            email=form.get('email') or '',
            username=form.get('username'), is_authenticated=True,
            level=user_level, testdir=None),
        build_absolute_uri=build_absolute_uri)
    response_data = create_impact_job(
        job_request, params, form.get('email_file_path'))
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
    from openquake.server.views import (
        get_impact_rupture_data, get_uploaded_file_path)
    user = SimpleNamespace(level=user_level, testdir=None)
    files = {
        key: value for key, value in form.multi_items()
        if hasattr(value, 'file')}
    adapter = SimpleNamespace(POST=post, FILES=files)
    rupture_path = get_uploaded_file_path(adapter, 'rupture_file')
    response_data, status = get_impact_rupture_data(
        post, user, rupture_path)
    return JSONResponse(content=response_data, status_code=status)


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


@app.get('/v1/calc/{calc_id}/log/size')
def calc_log_size(calc_id: int):
    """Return the number of log lines for a calculation."""
    return logs.dbcmd('get_log_size', calc_id)


@app.get('/v1/calc/{calc_id}/log/{log_range:path}')
def calc_log(calc_id: int, log_range: str):
    """Return a calculation log slice."""
    try:
        start, stop = log_range.split(':', 1)
        start = int(start or 0)
        stop = int(stop or 0)
    except ValueError as exc:
        raise HTTPException(status_code=400) from exc
    return _calc_log_slice(calc_id, start, stop)


@app.get('/v1/calc/{calc_id}/traceback')
def calc_traceback(calc_id: int):
    """Return the traceback for a calculation."""
    try:
        return logs.dbcmd('get_traceback', calc_id)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


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
async def on_same_fs(request: Request):
    """Check whether the client and server can access the same file."""
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
