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

import logging
import re
import secrets
import traceback
import zlib
from urllib.parse import parse_qs
from xml.parsers.expat import ExpatError

import numpy
from django.conf import settings
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from openquake.baselib.general import engine_version as get_engine_version
from openquake.baselib.general import gettemp
from openquake.engine import engine
from openquake.hazardlib import gsim, nrml, valid
from openquake.hazardlib.shakemap.validate import IMPACT_FORM_DEFAULTS
from openquake.commonlib import dbapi, logs, oqvalidation

app = FastAPI(title='OpenQuake API')


def _check_api_key(api_key):
    """Raise ``HTTPException`` unless the internal API key is valid."""
    if not api_key or not secrets.compare_digest(
            api_key, settings.OQ_API_KEY):
        raise HTTPException(status_code=403, detail='Invalid API key')


@app.get('/v1/calc_info/{calc_id}')
def calc_info(calc_id: int):
    """Return calculation information."""
    try:
        return logs.dbcmd('calc_info', calc_id)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


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


@app.get('/v1/calc/list_tags')
def calc_list_tags():
    """Return all calculation tags."""
    return logs.dbcmd('list_tags')


@app.get('/v1/calc/{calc_id}/log/size')
def calc_log_size(calc_id: int):
    """Return the number of log lines for a calculation."""
    return logs.dbcmd('get_log_size', calc_id)


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
