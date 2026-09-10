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

import re
import secrets
import zlib
from urllib.parse import parse_qs
from xml.parsers.expat import ExpatError

import numpy
from django.conf import settings
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

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


@app.get('/v0/calc/list_tags')
def v0calc_list_tags(x_api_key: str | None = Header(default=None)):
    """Return calculation tags for authenticated internal callers."""
    _check_api_key(x_api_key)
    return logs.dbcmd('list_tags')


@app.get('/v0/calc/{calc_id}')
def v0_calc(calc_id: int, x_api_key: str | None = Header(default=None)):
    """Return calculation information for authenticated internal callers."""
    _check_api_key(x_api_key)
    try:
        return logs.dbcmd('calc_info', calc_id)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


@app.get('/v0/calc/{calc_id}/log/size')
def v0calc_log_size(
        calc_id: int, x_api_key: str | None = Header(default=None)):
    """Return the calculation log size for an authenticated caller."""
    _check_api_key(x_api_key)
    try:
        return logs.dbcmd('get_log_size', calc_id)
    except dbapi.NotFound as exc:
        raise HTTPException(status_code=404) from exc


@app.get('/v0/calc/{calc_id}/traceback')
def v0calc_traceback(
        calc_id: int, x_api_key: str | None = Header(default=None)):
    """Return a calculation traceback for an authenticated caller."""
    _check_api_key(x_api_key)
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
