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
Internal API of the engine, i.e. the API used only by the processes of the
engine itself and protected by the key in the ``authkey`` of the
``[webapi]`` section of openquake.cfg. It contains the machinery to write
the views checking the key (:func:`internal_view`), the database and worker
actions of the ``/v0`` API and the plumbing of the other views.

This module does not import :mod:`openquake.server.services` nor the views,
which import it.
"""
import json
import logging
import secrets
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from urllib.parse import urljoin

import numpy
from django.http import HttpResponse, HttpResponseBase
from django.urls import re_path
from django.utils.datastructures import MultiValueDict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from openquake.baselib import workerpool as w
from openquake.commonlib import dbapi, logs
from openquake.commonlib.auth import API_KEY
from openquake.server.db.registry import get_action


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


def json_response(data, status=200):
    """Return a JSON response, converting dates and numpy scalars."""
    return HttpResponse(
        json.dumps(data, default=_json_default), status=status,
        content_type='application/json')


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


def _json_body(request):
    """Return the JSON payload of a request, or None if it is empty."""
    if not request.body:
        return None
    try:
        return json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ApiError(400, 'Invalid JSON body') from exc


def db_action(action, payload):
    """Execute an allowlisted database action."""
    try:
        func = get_action(action)
    except KeyError as exc:
        raise ApiError(404, str(exc)) from exc
    payload = payload or {}
    args = dbapi.from_json(payload.get('args', []))
    kwargs = dbapi.from_json(payload.get('kwargs', {}))
    try:
        result = func(dbapi.db, *args, **kwargs)
    except dbapi.NotFound:
        raise
    except Exception as exc:
        logging.exception('Database action failed: %s', action)
        raise ApiError(500, str(exc)) from exc
    return dbapi.to_json(result)


# sanitize the argument of a worker action, i.e. a job ID or a [zworkers]
# dictionary; its values are used to build the ssh commands starting the
# workerpools, so only the known keys are kept and their values must be in
# the known format (host_cores is validated by parallel.parse_hostcore)
def _worker_arg(args):
    if not args:
        return -1  # the current job
    arg = args[0]
    if isinstance(arg, int) and not isinstance(arg, bool):
        return arg
    keys = ('host_cores', 'ctrl_port')
    if not (isinstance(arg, dict) and all(
            isinstance(arg.get(key), str) for key in keys)
            and arg['ctrl_port'].isdigit()):
        raise ApiError(400, 'Invalid worker configuration')
    return {key: arg[key] for key in keys}


def worker_action(action, payload):
    """Run an authenticated worker-control action."""
    if 'workers_' + action not in logs.WORKER_ACTIONS:
        raise ApiError(404)
    payload = payload or {}
    try:
        master = w.WorkerMaster(_worker_arg(payload.get('args', [])))
    except ValueError as exc:  # raised by parallel.parse_hostcore
        raise ApiError(400, str(exc)) from exc
    return getattr(master, action)()


@internal_view('POST')
def v0_db_action(request, action):
    """Execute an allowlisted database action."""
    return db_action(action, _json_body(request))


@internal_view('POST')
def v0_worker(request, action):
    """Run an authenticated worker-control action."""
    return worker_action(action, _json_body(request))


# the /v0 routes of the database and of the worker actions
v0_urlpatterns = [
    re_path(r'^v0/db/([^/]+)$', v0_db_action),
    re_path(r'^v0/worker_([^/]+)$', v0_worker),
]
