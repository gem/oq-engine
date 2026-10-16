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
"""
Internal API of the WebUI, served by Django under the ``/v0`` and ``/v1``
paths of the server.

The functions without the ``v0_``/``v1_`` prefix implement the endpoints:
they are called in-process by :mod:`openquake.server.views` and they raise
:class:`ApiError` on failure. The decorated functions are the HTTP views,
which check the internal API key and turn the outcome into a response.
"""

import json
import logging
import multiprocessing as mp
import os
import secrets
import signal
import sqlite3
import tempfile
import traceback
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urljoin

import numpy
from django.http import FileResponse, HttpResponse, HttpResponseBase
from django.urls import re_path
from django.utils.datastructures import MultiValueDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from openquake.baselib import config, workerpool as w
from openquake.baselib.general import gettemp
from openquake.commonlib.auth import API_KEY
from openquake.commonlib import (
    dbapi, datastore, logs, oqvalidation, readinput)
from openquake.hazardlib import valid
from openquake.commonlib.model_provenance import read_model_provenance
from openquake.calculators import base
from openquake.engine import engine
from openquake.engine.export.core import DataStoreExportError
from openquake.hazardlib.shakemap.validate import (
    IMPACT_FORM_DEFAULTS, impact_validate)
from openquake.server import views
from openquake.server.db.registry import get_action
from openquake.server.papers import base as papers
from openquake.server.services import (
    create_impact_job, export_result, get_impact_rupture_data,
    get_papers_job_ctx, remove_exported, submit_job)


class ApiError(Exception):
    """Error returned to the caller with the given HTTP status."""

    def __init__(self, status, detail=None, content=None):
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.content = content

    def response(self):
        """Return the JSON response describing the error."""
        if self.content is not None:
            return json_response(self.content, self.status)
        detail = self.detail or HTTPStatus(self.status).phrase
        return json_response({'detail': detail}, self.status)


class ExportResponse(FileResponse):
    """Stream an exported file and remove its directory once closed."""

    def __init__(self, fname, **kwargs):
        super().__init__(open(fname, 'rb'), **kwargs)
        self.fname = fname

    def close(self):
        super().close()
        remove_exported(self.fname)


def _json_default(value):
    """Convert the values which the json module cannot serialize."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, numpy.generic):
        return value.item()
    if isinstance(value, dbapi.Row):
        return list(value)
    raise TypeError('Object of type %s is not JSON serializable'
                    % type(value).__name__)


def json_response(data, status=200):
    """Return a JSON response, converting dates and numpy scalars."""
    return HttpResponse(
        json.dumps(data, default=_json_default), status=status,
        content_type='application/json')


def run(func, *args, **kwargs):
    """
    Call an internal API function and return its response. The errors
    raised as :class:`ApiError` or as :class:`dbapi.NotFound` become JSON
    error responses, while a returned HTTP response is passed unchanged.
    """
    try:
        result = func(*args, **kwargs)
    except ApiError as exc:
        return exc.response()
    except dbapi.NotFound:
        return ApiError(404).response()
    if isinstance(result, HttpResponseBase):
        return result
    return json_response(result)


def _pairs(source):
    """Return the (key, value) pairs of a dictionary or a MultiValueDict."""
    if hasattr(source, 'lists'):
        return [(key, value) for key, values in source.lists()
                for value in values]
    return list(source.items())


def make_form(*sources):
    """
    Merge plain fields (dictionaries or QueryDicts) and uploaded files into
    a single MultiValueDict, the form accepted by the internal functions.
    """
    form = MultiValueDict()
    for source in sources:
        for key, value in _pairs(source):
            form.appendlist(key, value)
    return form


def _split(form):
    """Return the plain fields and the uploaded files of a form."""
    fields, files = MultiValueDict(), MultiValueDict()
    for key, value in _pairs(form):
        (files if hasattr(value, 'file') else fields).appendlist(key, value)
    return fields, files


def _uri_builder(base_url):
    """Return a function building absolute URIs from paths on the server."""
    def build_absolute_uri(path):
        return urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
    return build_absolute_uri


def has_api_key(request):
    """Return whether the request carries the internal API key."""
    api_key = request.headers.get('X-API-Key')
    return bool(api_key) and secrets.compare_digest(api_key, API_KEY)


def _check_api_key(request):
    """Raise ApiError unless the request has the internal API key."""
    if not has_api_key(request):
        raise ApiError(403, 'Invalid API key')


def internal_view(*methods, auth=True):
    """
    Turn a function of the request into a Django view accepting only the
    given HTTP methods. The view is exempt from CSRF checks, since the
    callers are programs, and it requires the internal API key unless
    ``auth`` is false.
    """
    def decorator(func):
        @csrf_exempt
        @require_http_methods(methods)
        @wraps(func)
        def view(request, *args):
            try:
                if auth:
                    _check_api_key(request)
            except ApiError as exc:
                return exc.response()
            return run(func, request, *args)
        return view
    return decorator


def _form(request):
    """Return the form (fields and files) of a POST request."""
    return make_form(request.POST, request.FILES)


def _json_body(request):
    """Return the JSON payload of a request, or None if it is empty."""
    if not request.body:
        return None
    try:
        return json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ApiError(400, 'Invalid JSON body') from exc


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


def db_action(action, payload):
    """Execute an allowlisted database action."""
    try:
        func = get_action(action)
    except KeyError as exc:
        raise ApiError(404, str(exc)) from exc
    payload = payload or {}
    args = logs._decode_db_value(payload.get('args', []))
    kwargs = logs._decode_db_value(payload.get('kwargs', {}))
    try:
        result = func(dbapi.db, *args, **kwargs)
    except dbapi.NotFound:
        raise
    except Exception as exc:
        logging.exception('Database action failed: %s', action)
        raise ApiError(500, str(exc)) from exc
    return _json_value(result)


def worker_action(action, payload):
    """Run an authenticated worker-control action."""
    if 'workers_' + action not in logs.WORKER_ACTIONS:
        raise ApiError(404)
    payload = payload or {}
    args = payload.get('args', [])
    master = w.WorkerMaster(args[0] if args else -1)
    return getattr(master, action)()


def calc_info(calc_id):
    """Return the information about a calculation."""
    return logs.dbcmd('calc_info', calc_id)


def _no_provenance():
    """Return the answer for calculations without model provenance."""
    return {
        'available': False,
        'reason': 'Model provenance metadata is not available',
    }


def model_provenance(calc_id):
    """Return the model provenance of a calculation."""
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        raise ApiError(404)
    path = job.ds_calc_dir + '.hdf5'
    if not os.path.exists(path):
        return _no_provenance()
    try:
        with datastore.read(path) as dstore:
            summary = read_model_provenance(dstore)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logging.exception('Could not read model provenance')
        raise ApiError(500, str(exc)) from exc
    if summary is None:
        return _no_provenance()
    return {'available': True, 'summary': summary}


def get_uploaded_file_path(files, filename):
    """Copy an uploaded file to a temporary path and return its location."""
    file = files.get(filename)
    if file:
        # NOTE: we could not find a reliable way to avoid the deletion of the
        # uploaded file right after the request is consumed, therefore we need
        # to store a copy of it
        suffix = file.name[-4:]
        source = getattr(file, 'file', None)
        if source is None:
            with open(file.temporary_file_path(), 'rb') as stream:
                content = stream.read()
        else:
            source.seek(0)
            content = source.read()
        return gettemp(content, suffix=suffix)


def validate_job(job_file):
    """Validate a calculation input and return its JSON-compatible result."""
    try:
        oq = readinput.get_oqparam(job_file)
        with patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
            base.calculators(oq, calc_id=None).run()
    except Exception as exc:
        return dict(error_msg=str(exc), error_line=None, valid=False)
    return dict(error_msg=None, error_line=None, valid=True)


def validate_upload(form, field, missing_message):
    """Validate the calculation file stored under the given field."""
    fields, files = _split(form)
    if field in files:
        path = get_uploaded_file_path(files, field)
    else:
        path = fields.get(field)
    if not path:
        raise ApiError(400, missing_message)
    return validate_job(path)


def calc_run(form):
    """Submit a calculation, using the archive in the form if present."""
    ini = form.get('ini') or form.get('job_ini') or '.ini'
    hazard_job_id = form.get('hazard_job_id') or None
    username = form.get('username')
    if not username:
        raise ApiError(400, 'Missing calculation owner')
    notify_to = form.get('notify_to') or None
    request_files = form if form.getlist('archive') else []
    try:
        job_id = submit_job(
            request_files, ini, username, hazard_job_id, notify_to)
    except Exception as exc:
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        raise ApiError(500, content={
            'traceback': exc_msg.splitlines(),
            'job_id': getattr(exc, 'job_id', None)}) from exc
    return logs.get_job_info(job_id)


def calc_abort(calc_id):
    """Abort a running calculation."""
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


def calc_remove(calc_id, username):
    """Remove a calculation on behalf of its owner."""
    message = logs.dbcmd('del_calc', calc_id, username)
    if 'success' in message or 'error' in message:
        return message
    raise ApiError(500, str(message))


def aelo_run(form):
    """Run an AELO calculation from the given form."""
    username = form.get('username')
    base_url = form.get('base_url')
    if not username or not base_url:
        raise ApiError(400, 'Missing AELO caller information')
    result = views.aelo_validate(SimpleNamespace(POST=form))
    if hasattr(result, 'status_code'):
        raise ApiError(result.status_code,
                       content=json.loads(result.content))
    lon, lat, site_name, asce_version, site_class, vs30 = result
    response_data, status = views._run_aelo(
        lon, lat, site_name, asce_version, site_class, vs30, username,
        form.get('email') or '', _uri_builder(base_url),
        form.get('email_file_path'))
    return json_response(response_data, status)


def run_scenario_calc_from_ses_rupture(rup_id, form):
    """Run a PAPERS scenario calculation for an SES rupture."""
    if not form.get('username'):
        raise ApiError(400, 'Missing calculation owner')
    try:
        job_ctx = get_papers_job_ctx(papers, rup_id, form)
        mp.Process(target=engine.run_jobs, args=([job_ctx],), kwargs={
            'notify_to': form.get('notify_to')}).start()
        return logs.get_job_info(job_ctx.calc_id)
    except Exception as exc:
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        raise ApiError(500, content={
            'traceback': exc_msg.splitlines(),
            'job_id': getattr(exc, 'job_id', None)}) from exc


def _user(form):
    """Return the user, with the level given in the form, of an IMPACT job."""
    try:
        level = int(form.get('user_level', 0))
    except (TypeError, ValueError) as exc:
        raise ApiError(400, 'Invalid IMPACT user level') from exc
    return SimpleNamespace(level=level, testdir=None)


def _station(files, post):
    """Return the station data path and its source, if any."""
    station_path = get_uploaded_file_path(files, 'station_data_file')
    if station_path:
        return station_path, 'user-provided'
    station_from_usgs = post.get('station_data_file_from_usgs', '')
    if station_from_usgs:
        return station_from_usgs, 'USGS'
    return station_path, None


def _impact_urls(base_url):
    """Return a function building the URLs of an IMPACT job."""
    build_absolute_uri = _uri_builder(base_url)

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
    return build_urls


def impact_run(form):
    """Run an IMPACT calculation from the given form."""
    fields, files = _split(form)
    user = _user(form)
    post = {key: value for key, value in fields.items()
            if key not in ('user_level', 'username', 'email', 'base_url')}
    rupture_path = get_uploaded_file_path(files, 'rupture_file')
    if not rupture_path:
        rupture_path = post.get('rupture_from_usgs') or ''
    if rupture_path == 'None':
        rupture_path = ''
    station_path, station_source = _station(files, post)
    _rup, _rupdic, params, err = impact_validate(
        post, user, rupture_path, station_path)
    if err:
        return json_response(
            err, 400 if 'invalid_inputs' in err else 500)
    if station_source is not None:
        params['station_source'] = station_source
    if params.get('make_impact_reports'):
        params['postrisk_func'] = 'make_impact_reports.main'
    params['export_dir'] = (
        config.directory.custom_tmp or tempfile.gettempdir())
    response_data = create_impact_job(
        params, form.get('username'), form.get('email') or '',
        _impact_urls(form.get('base_url', '')), views.impact_callback,
        form.get('email_file_path'))
    return json_response(response_data)


def impact_get_rupture_data(form):
    """Build the rupture data of an IMPACT job from the given form."""
    post = {key: value for key, value in _pairs(form)
            if key not in ('rupture_file', 'user_level')}
    user = _user(form)
    _, files = _split(form)
    rupture_path = get_uploaded_file_path(files, 'rupture_file')
    response_data, status = get_impact_rupture_data(
        post, user, rupture_path)
    return json_response(response_data, status)


def calc_list_count(params, valid_users, acl_on):
    """Count the calculations matching the filters of the list view."""
    params = dict(params, count_only='1')
    return logs.dbcmd(
        'get_calcs', params, valid_users, valid.boolean(acl_on or '1'))


def calc_log(calc_id, start, stop):
    """Return a slice of the log of a calculation."""
    return logs.dbcmd('get_log_slice', calc_id, start, stop)


def calc_log_size(calc_id):
    """Return the number of log lines of a calculation."""
    return logs.dbcmd('get_log_size', calc_id)


def calc_traceback(calc_id):
    """Return the traceback of a calculation."""
    return logs.dbcmd('get_traceback', calc_id)


def calc_result(result_id, export_type=None):
    """Export a result in the requested format, as a downloadable file."""
    try:
        exported = export_result(result_id, export_type)
    except DataStoreExportError as exc:
        # TODO: there should be a better error page
        raise ApiError(500, '%s: %s' % (exc.__class__.__name__, exc)) from exc
    if exported is None:  # the requested format is not supported
        raise ApiError(404)
    fname, content_type, exportname = exported
    response = ExportResponse(fname, content_type=content_type)
    # NB: the Content-Disposition is set manually, since the one generated
    # by FileResponse would quote the file name
    response['Content-Disposition'] = (
        'attachment; filename=%s' % exportname)
    return response


def aelo_site_classes():
    """Return the AELO site-class definitions."""
    return oqvalidation.SITE_CLASSES


def impact_form_defaults():
    """Return the default values for the IMPACT form."""
    return IMPACT_FORM_DEFAULTS


def _valid_users(request):
    """Return the list of valid users sent in the request headers."""
    try:
        return json.loads(request.headers.get('X-Valid-Users') or '[]')
    except json.JSONDecodeError as exc:
        raise ApiError(400, 'Invalid user context') from exc


@internal_view('GET')
def v1_calc_info(request, calc_id):
    """Return the information about a calculation."""
    return calc_info(int(calc_id))


@internal_view('GET')
def v1_calc_list_count(request):
    """Count the calculations matching the filters of the list view."""
    return calc_list_count(
        request.GET.dict(), _valid_users(request),
        request.headers.get('X-User-ACL-On'))


@internal_view('GET', auth=False)
def v1_aelo_site_classes(request):
    """Return the AELO site-class definitions."""
    return aelo_site_classes()


@internal_view('GET', auth=False)
def v1_impact_form_defaults(request):
    """Return the default values for the IMPACT form."""
    return impact_form_defaults()


@internal_view('GET')
def v0_model_provenance(request, calc_id):
    """Return the model provenance of a calculation."""
    return model_provenance(int(calc_id))


@internal_view('POST')
def v0_db_action(request, action):
    """Execute an allowlisted database action."""
    return db_action(action, _json_body(request))


@internal_view('POST')
def v0_worker(request, action):
    """Run an authenticated worker-control action."""
    return worker_action(action, _json_body(request))


@internal_view('POST')
def v0_validate_ini(request):
    """Validate an uploaded INI file."""
    return validate_upload(_form(request), 'job_ini',
                           'Missing job_ini file')


@internal_view('POST')
def v0_validate_zip(request):
    """Validate an uploaded calculation archive."""
    return validate_upload(_form(request), 'archive',
                           'Missing archive file')


@internal_view('POST')
def v0_calc_run(request):
    """Submit a calculation for an authenticated Django caller."""
    return calc_run(_form(request))


@internal_view('POST')
def v0_calc_abort(request, calc_id):
    """Abort a running calculation for an authenticated caller."""
    return calc_abort(int(calc_id))


@internal_view('POST')
def v0_calc_remove(request, calc_id):
    """Remove a calculation for an authenticated caller."""
    username = request.POST.get('username')
    if not username:
        raise ApiError(422, 'Missing username')
    return calc_remove(int(calc_id), username)


@internal_view('POST')
def v0_aelo_run(request):
    """Run an AELO calculation for an authenticated Django caller."""
    return aelo_run(_form(request))


@internal_view('POST')
def v0_run_scenario(request, rup_id):
    """Run a papers scenario calculation for an authenticated caller."""
    return run_scenario_calc_from_ses_rupture(int(rup_id), _form(request))


@internal_view('POST')
def v0_impact_run(request):
    """Run IMPACT for an authenticated Django caller."""
    return impact_run(_form(request))


@internal_view('POST')
def v0_impact_get_rupture_data(request):
    """Build IMPACT rupture data for an authenticated Django caller."""
    return impact_get_rupture_data(_form(request))


@internal_view('GET', auth=False)
def v0_calc_log_size(request, calc_id):
    """Return the number of log lines for a calculation."""
    return calc_log_size(int(calc_id))


@internal_view('GET')
def v0_calc_log(request, calc_id, start, stop):
    """Return a calculation log slice."""
    return calc_log(int(calc_id), int(start or 0), int(stop or 0))


@internal_view('GET')
def v0_calc_traceback(request, calc_id):
    """Return the traceback for a calculation."""
    return calc_traceback(int(calc_id))


@internal_view('GET', 'HEAD')
def v0_calc_result(request, result_id):
    """Export a calculation result in the requested format."""
    return calc_result(int(result_id), request.GET.get('export_type'))


internal_urlpatterns = [
    re_path(r'^v1/calc_info/(\d+)$', v1_calc_info),
    re_path(r'^v1/calc_list/count$', v1_calc_list_count),
    re_path(r'^v1/aelo_site_classes$', v1_aelo_site_classes),
    re_path(r'^v1/get_impact_form_defaults$', v1_impact_form_defaults),
    re_path(r'^v0/calc/model_provenance/(\d+)$', v0_model_provenance),
    re_path(r'^v0/db/([^/]+)$', v0_db_action),
    re_path(r'^v0/worker_([^/]+)$', v0_worker),
    re_path(r'^v0/calc/validate_ini$', v0_validate_ini),
    re_path(r'^v0/calc/validate_zip$', v0_validate_zip),
    re_path(r'^v0/calc/run$', v0_calc_run),
    re_path(r'^v0/calc/(\d+)/abort$', v0_calc_abort),
    re_path(r'^v0/calc/(\d+)/remove$', v0_calc_remove),
    re_path(r'^v0/calc/aelo_run$', v0_aelo_run),
    re_path(r'^v0/calc/run_scenario_calc_from_ses_rupture/(\d+)$',
            v0_run_scenario),
    re_path(r'^v0/calc/impact_run$', v0_impact_run),
    re_path(r'^v0/calc/impact_get_rupture_data$',
            v0_impact_get_rupture_data),
    re_path(r'^v0/calc/(\d+)/log/size$', v0_calc_log_size),
    re_path(r'^v0/calc/(\d+)/log/(\d*):(\d*)$', v0_calc_log),
    re_path(r'^v0/calc/(\d+)/traceback$', v0_calc_traceback),
    re_path(r'^v0/calc/result/(\d+)$', v0_calc_result),
]
