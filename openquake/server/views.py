# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import csv
import shutil
import json
import string
import pickle
import logging
import os
import tempfile
import subprocess
import traceback
import signal
import zlib
import urllib.parse as urlparse
import re
import psutil
from datetime import datetime, timezone
from urllib.parse import unquote_plus
from xml.parsers.expat import ExpatError
from django.http import (
    HttpResponse, HttpResponseNotFound, HttpResponseBadRequest,
    HttpResponseForbidden)
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
import numpy

from openquake.baselib import hdf5, config, parallel
from openquake.baselib.general import groupby, gettemp, zipfiles, mp
from openquake.hazardlib import nrml, gsim, valid
from openquake.hazardlib.shakemap.validate import (
    impact_validate, ARISTOTLE_FORM_LABELS, ARISTOTLE_FORM_PLACEHOLDERS)
from openquake.commonlib import readinput, oqvalidation, logs, datastore, dbapi
from openquake.calculators import base, views
from openquake.calculators.getters import NotFound
from openquake.calculators.export import export, FIELD_DESCRIPTION
from openquake.calculators.extract import extract as _extract
from openquake.calculators.postproc.plots import plot_shakemap, plot_rupture
from openquake.engine import __version__ as oqversion
from openquake.engine.export import core
from openquake.engine import engine, aelo, impact
from openquake.engine.aelo import (
    get_params_from, PRELIMINARY_MODELS, PRELIMINARY_MODEL_WARNING)
from openquake.engine.export.core import DataStoreExportError
from openquake.server import utils

from django.conf import settings
from django.http import FileResponse
from django.urls import reverse
from wsgiref.util import FileWrapper

if settings.LOCKDOWN:
    from django.contrib.auth import authenticate, login, logout

UTC = timezone.utc
CWD = os.path.dirname(__file__)
METHOD_NOT_ALLOWED = 405
NOT_IMPLEMENTED = 501

XML = 'application/xml'
JSON = 'application/json'
HDF5 = 'application/x-hdf'

#: For exporting calculation outputs, the client can request a specific format
#: (xml, geojson, csv, etc.). If the client does not specify give them (NRML)
#: XML by default.
DEFAULT_EXPORT_TYPE = 'xml'

EXPORT_CONTENT_TYPE_MAP = dict(xml=XML, geojson=JSON)
DEFAULT_CONTENT_TYPE = 'text/plain'

LOGGER = logging.getLogger('openquake.server')

ACCESS_HEADERS = {'Access-Control-Allow-Origin': '*',
                  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                  'Access-Control-Max-Age': 1000,
                  'Access-Control-Allow-Headers': '*'}

KUBECTL = "kubectl apply -f -".split()
ENGINE = "python -m openquake.engine.engine".split()

AELO_FORM_LABELS = {
    'lon': 'Longitude',
    'lat': 'Latitude',
    'vs30': 'Vs30',
    'siteid': 'Site name',
    'asce_version': 'ASCE version',
}

AELO_FORM_PLACEHOLDERS = {
    'lon': 'max. 5 decimals',
    'lat': 'max. 5 decimals',
    'vs30': 'fixed at 760 m/s',
    'siteid': f'max. {settings.MAX_AELO_SITE_NAME_LEN} characters',
    'asce_version': 'ASCE version',
}

HIDDEN_OUTPUTS = ['assetcol', 'job']

# disable check on the export_dir, since the WebUI exports in a tmpdir
oqvalidation.OqParam.is_valid_export_dir = lambda self: True


# Credit for this decorator to https://gist.github.com/aschem/1308865.
def cross_domain_ajax(func):
    def wrap(request, *args, **kwargs):
        # Firefox sends 'OPTIONS' request for cross-domain javascript call.
        if not request.method == "OPTIONS":
            response = func(request, *args, **kwargs)
        else:
            response = HttpResponse()
        for k, v in list(ACCESS_HEADERS.items()):
            response[k] = v
        return response
    return wrap


def _get_base_url(request):
    """
    Construct a base URL, given a request object.

    This comprises the protocol prefix (http:// or https://) and the host,
    which can include the port number. For example:
    http://www.openquake.org or https://www.openquake.org:8000.
    """
    if request.is_secure():
        base_url = 'https://%s'
    else:
        base_url = 'http://%s'
    base_url %= request.META['HTTP_HOST']
    return base_url


def store(request_files, ini, calc_id):
    """
    Store the uploaded files in calc_dir and select the job file by looking
    at the .ini extension.

    :returns: full path of the ini file
    """
    calc_dir = parallel.scratch_dir(calc_id)
    arch = request_files.get('archive')
    if arch is None:
        # move each file to calc_dir using the upload file names
        inifiles = []
        # NB: request_files.values() Django objects are not sortable
        for each_file in request_files.values():
            new_path = os.path.join(calc_dir, each_file.name)
            shutil.move(each_file.temporary_file_path(), new_path)
            if each_file.name.endswith(ini):
                inifiles.append(new_path)
    else:  # extract the files from the archive into calc_dir
        inifiles = readinput.extract_from_zip(arch, ini, calc_dir)
    if not inifiles:
        raise NotFound('There are no %s files in the archive' % ini)
    return inifiles[0]


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def ajax_login(request):
    """
    Accept a POST request to login.

    :param request:
        `django.http.HttpRequest` object, containing mandatory parameters
        username and password required.
    """
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return HttpResponse(content='Successful login',
                                content_type='text/plain', status=200)
        else:
            return HttpResponse(content='Disabled account',
                                content_type='text/plain', status=403)
    else:
        return HttpResponse(content='Invalid login',
                            content_type='text/plain', status=403)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def ajax_logout(request):
    """
    Accept a POST request to logout.
    """
    logout(request)
    return HttpResponse(content='Successful logout',
                        content_type='text/plain', status=200)


@cross_domain_ajax
@require_http_methods(['GET'])
def get_engine_version(request):
    """
    Return a string with the openquake.engine version
    """
    return HttpResponse(oqversion)


@cross_domain_ajax
@require_http_methods(['GET'])
def get_engine_latest_version(request):
    """
    Return a string with if new versions have been released.
    Return 'None' if the version is not available
    """
    return HttpResponse(engine.check_obsolete_version())


@cross_domain_ajax
@require_http_methods(['GET'])
def get_available_gsims(request):
    """
    Return a list of strings with the available GSIMs
    """
    gsims = list(gsim.get_available_gsims())
    return HttpResponse(content=json.dumps(gsims), content_type=JSON)


@cross_domain_ajax
@require_http_methods(['GET'])
def get_ini_defaults(request):
    """
    Return a list of ini attributes with a default value
    """
    ini_defs = {}
    all_names = dir(oqvalidation.OqParam) + list(oqvalidation.OqParam.ALIASES)
    for name in all_names:
        if name in oqvalidation.OqParam.ALIASES:  # old name
            newname = oqvalidation.OqParam.ALIASES[name]
        else:
            newname = name
        obj = getattr(oqvalidation.OqParam, newname)
        if (isinstance(obj, valid.Param)
                and obj.default is not valid.Param.NODEFAULT):
            if isinstance(obj.default, float) and numpy.isnan(obj.default):
                pass
            else:
                ini_defs[name] = obj.default
    return HttpResponse(content=json.dumps(ini_defs), content_type=JSON)


def _make_response(error_msg, error_line, valid):
    response_data = dict(error_msg=error_msg,
                         error_line=error_line,
                         valid=valid)
    return HttpResponse(
        content=json.dumps(response_data), content_type=JSON)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def validate_nrml(request):
    """
    Leverage oq-risklib to check if a given XML text is a valid NRML

    :param request:
        a `django.http.HttpRequest` object containing the mandatory
        parameter 'xml_text': the text of the XML to be validated as NRML

    :returns: a JSON object, containing:
        * 'valid': a boolean indicating if the provided text is a valid NRML
        * 'error_msg': the error message, if any error was found
                       (None otherwise)
        * 'error_line': line of the given XML where the error was found
                        (None if no error was found or if it was not a
                        validation error)
    """
    xml_text = request.POST.get('xml_text')
    if not xml_text:
        return HttpResponseBadRequest(
            'Please provide the "xml_text" parameter')
    xml_file = gettemp(xml_text, suffix='.xml')
    try:
        nrml.to_python(xml_file)
    except ExpatError as exc:
        return _make_response(error_msg=str(exc),
                              error_line=exc.lineno,
                              valid=False)
    except Exception as exc:
        # get the exception message
        exc_msg = exc.args[0]
        if isinstance(exc_msg, bytes):
            exc_msg = exc_msg.decode('utf-8')   # make it a unicode object
        elif isinstance(exc_msg, str):
            pass
        else:
            # if it is another kind of object, it is not obvious a priori how
            # to extract the error line from it
            return _make_response(
                error_msg=str(exc_msg), error_line=None, valid=False)
        # if the line is not mentioned, the whole message is taken
        error_msg = exc_msg.split(', line')[0]
        # check if the exc_msg contains a line number indication
        search_match = re.search(r'line \d+', exc_msg)
        if search_match:
            error_line = int(search_match.group(0).split()[1])
        else:
            error_line = None
        return _make_response(
            error_msg=error_msg, error_line=error_line, valid=False)
    else:
        return _make_response(error_msg=None, error_line=None, valid=True)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def validate_zip(request):
    """
    Leverage the engine libraries to check if a given zip archive is a valid
    calculation input

    :param request:
        a `django.http.HttpRequest` object containing a zip archive

    :returns: a JSON object, containing:
        * 'valid': a boolean indicating if the provided archive is valid
        * 'error_msg': the error message, if any error was found
                       (None otherwise)
    """
    archive = request.FILES.get('archive')
    if not archive:
        return HttpResponseBadRequest('Missing archive file')
    job_zip = archive.temporary_file_path()
    try:
        oq = readinput.get_oqparam(job_zip)
        base.calculators(oq, calc_id=None).read_inputs()
    except Exception as exc:
        return _make_response(str(exc), None, valid=False)
    else:
        return _make_response(None, None, valid=True)


@require_http_methods(['GET'])
@cross_domain_ajax
def download_png(request, calc_id, what):
    """
    Get a PNG image with the relevant name, if available
    """
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name, job.status):
        return HttpResponseForbidden()
    try:
        from PIL import Image
        response = HttpResponse(content_type="image/png")
        with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
            arr = ds['png/%s' % what][:]
        Image.fromarray(arr).save(response, format='png')
        return response
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        return HttpResponse(
            content='%s: %s\n%s' % (exc.__class__.__name__, exc, tb),
            content_type='text/plain', status=500)


@require_http_methods(['GET'])
@cross_domain_ajax
def calc(request, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    try:
        info = logs.dbcmd('calc_info', calc_id)
        if not utils.user_has_permission(request, info['user_name'], info['status']):
            return HttpResponseForbidden()
    except dbapi.NotFound:
        return HttpResponseNotFound()
    return HttpResponse(content=json.dumps(info), content_type=JSON)


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_list(request, id=None):
    # view associated to the endpoints /v1/calc/list and /v1/calc/:id/status
    """
    Get a list of calculations and report their id, status, calculation_mode,
    is_running, description, and a url where more detailed information
    can be accessed. This is called several times by the Javascript.

    Responses are in JSON.
    """
    base_url = _get_base_url(request)
    # always filter calculation list unless user is a superuser
    calc_data = logs.dbcmd('get_calcs', dict(request.GET.items()),
                           utils.get_valid_users(request),
                           not utils.is_superuser(request), id)

    response_data = []
    username = psutil.Process(os.getpid()).username()
    for (hc_id, owner, status, calculation_mode, is_running, desc, pid,
         parent_id, size_mb, host, start_time) in calc_data:
        if host:
            owner += '@' + host.split('.')[0]
        url = urlparse.urljoin(base_url, 'v1/calc/%d' % hc_id)
        abortable = False
        if is_running:
            try:
                if psutil.Process(pid).username() == username:
                    abortable = True
            except psutil.NoSuchProcess:
                pass
        start_time_str = (
            start_time.strftime("%Y-%m-%d, %H:%M:%S") + " "
            + settings.TIME_ZONE)
        response_data.append(
            dict(id=hc_id, owner=owner,
                 calculation_mode=calculation_mode, status=status,
                 is_running=bool(is_running), description=desc, url=url,
                 parent_id=parent_id, abortable=abortable, size_mb=size_mb,
                 start_time=start_time_str))

    # if id is specified the related dictionary is returned instead the list
    if id is not None:
        response_data = [job for job in response_data if str(job['id']) == id]
        if not response_data:
            return HttpResponseNotFound()
        [response_data] = response_data

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def calc_abort(request, calc_id):
    """
    Abort the given calculation, it is it running
    """
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        message = {'error': 'Unknown job %s' % calc_id}
        return HttpResponse(content=json.dumps(message), content_type=JSON)

    if job.status not in ('submitted', 'executing'):
        message = {'error': 'Job %s is not running' % job.id}
        return HttpResponse(content=json.dumps(message), content_type=JSON)

    # only the owner or superusers can abort a calculation
    if (job.user_name not in utils.get_valid_users(request) and
            not utils.is_superuser(request)):
        message = {'error': ('User %s has no permission to abort job %s' %
                             (request.user, job.id))}
        return HttpResponse(content=json.dumps(message), content_type=JSON,
                            status=403)

    if job.pid:  # is a spawned job
        try:
            os.kill(job.pid, signal.SIGINT)
        except Exception as exc:
            logging.error(exc)
        else:
            logging.warning('Aborting job %d, pid=%d', job.id, job.pid)
            logs.dbcmd('set_status', job.id, 'aborted')
        message = {'success': 'Killing job %d' % job.id}
        return HttpResponse(content=json.dumps(message), content_type=JSON)

    message = {'error': 'PID for job %s not found' % job.id}
    return HttpResponse(content=json.dumps(message), content_type=JSON)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def calc_remove(request, calc_id):
    """
    Remove the calculation id
    """
    # Only the owner can remove a job
    user = utils.get_user(request)
    try:
        message = logs.dbcmd('del_calc', calc_id, user)
    except dbapi.NotFound:
        return HttpResponseNotFound()

    if 'success' in message:
        return HttpResponse(content=json.dumps(message),
                            content_type=JSON, status=200)
    elif 'error' in message:
        logging.error(message['error'])
        return HttpResponse(content=json.dumps(message),
                            content_type=JSON, status=403)
    else:
        # This is an untrapped server error
        logging.error(message)
        return HttpResponse(content=message,
                            content_type='text/plain', status=500)


def share_job(user_level, calc_id, share):
    if user_level < 2:
        return HttpResponseForbidden()
    try:
        message = logs.dbcmd('share_job', calc_id, share)
    except dbapi.NotFound:
        return HttpResponseNotFound()

    if 'success' in message:
        return HttpResponse(content=json.dumps(message),
                            content_type=JSON, status=200)
    elif 'error' in message:
        logging.error(message['error'])
        return HttpResponse(content=json.dumps(message),
                            content_type=JSON, status=403)
    else:
        raise AssertionError(
            f"share_job must return 'success' or 'error'!? Returned: {message}")


def get_user_level(request):
    if settings.LOCKDOWN:
        try:
            return request.user.level
        except AttributeError:  # e.g. AnonymousUser (not authenticated)
            return 0
    else:
        # NOTE: when authentication is not required, the user interface
        # can assume the user to have the maximum level
        return 2


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def calc_unshare(request, calc_id):
    """
    Unshare the calculation of the given id
    """
    user_level = get_user_level(request)
    return share_job(user_level, calc_id, share=False)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def calc_share(request, calc_id):
    """
    Share the calculation of the given id
    """
    user_level = get_user_level(request)
    return share_job(user_level, calc_id, share=True)


def log_to_json(log):
    """Convert a log record into a list of strings"""
    return [log.timestamp.isoformat()[:22],
            log.level, log.process, log.message]


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_log(request, calc_id, start, stop):
    """
    Get a slice of the calculation log as a JSON list of rows
    """
    start = start or 0
    stop = stop or 0
    try:
        response_data = logs.dbcmd('get_log_slice', calc_id, start, stop)
    except dbapi.NotFound:
        return HttpResponseNotFound()
    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_log_size(request, calc_id):
    """
    Get the current number of lines in the log
    """
    try:
        response_data = logs.dbcmd('get_log_size', calc_id)
    except dbapi.NotFound:
        return HttpResponseNotFound()
    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def calc_run(request):
    """
    Run a calculation.

    :param request:
        a `django.http.HttpRequest` object.
        If the request has the attribute `hazard_job_id`, the results of the
        specified hazard calculations will be re-used as input by the risk
        calculation.
        The request also needs to contain the files needed to perform the
        calculation. They can be uploaded as separate files, or zipped
        together.
    """
    job_ini = request.POST.get('job_ini')
    hazard_job_id = request.POST.get('hazard_job_id')
    if hazard_job_id:  # "continue" button, tested in the QGIS plugin
        ini = job_ini if job_ini else "risk.ini"
    else:
        ini = job_ini if job_ini else ".ini"
    user = utils.get_user(request)
    try:
        job_id = submit_job(request.FILES, ini, user, hazard_job_id)
    except Exception as exc:  # job failed, for instance missing .xml file
        # get the exception message
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        response_data = dict(traceback=exc_msg.splitlines(), job_id=exc.job_id)
        status = 500
    else:
        response_data = dict(status='created', job_id=job_id)
        status = 200
    return HttpResponse(content=json.dumps(response_data), content_type=JSON,
                        status=status)


def aelo_callback(
        job_id, job_owner_email, outputs_uri, inputs, exc=None, warnings=None):
    if not job_owner_email:
        return
    from_email = settings.EMAIL_HOST_USER
    to = [job_owner_email]
    reply_to = settings.EMAIL_SUPPORT
    lon, lat = inputs['sites'].split()
    body = (f"Input values: lon = {lon}, lat = {lat},"
            f" vs30 = {inputs['vs30']}, siteid = {inputs['siteid']},"
            f" asce_version = {inputs['asce_version']}\n\n")
    if warnings is not None:
        for warning in warnings:
            body += warning + '\n'
    if exc:
        subject = f'Job {job_id} failed'
        body += f'There was an error running job {job_id}:\n{exc}'
    else:
        subject = f'Job {job_id} finished correctly'
        body += (f'Please find the results here:\n{outputs_uri}')
    EmailMessage(subject, body, from_email, to, reply_to=[reply_to]).send()


def impact_callback(
        job_id, params, job_owner_email, outputs_uri, exc=None, warnings=None):
    if not job_owner_email:
        return

    # Example of body:
    # Input parameters:
    # {'lon': 37.0143, 'lat': 37.2256, 'dep': 10.0, 'mag': 7.8, 'rake': 0.0,
    #  'usgs_id': 'us6000jllz', 'rupture_file': None}
    # maximum_distance: 20.0
    # tectonic_region_type: Active Shallow Crust
    # truncation_level: 3.0
    # number_of_ground_motion_fields: 100
    # asset_hazard_distance: 15.0
    # ses_seed: 42
    # station_data_file: None
    # maximum_distance_stations: None
    # countries: TUR
    # description: us6000jllz (37.2256, 37.0143) M7.8 TUR

    params_to_print = ''
    for key, val in params.items():
        if key not in ['calculation_mode', 'inputs', 'job_ini',
                       'hazard_calculation_id']:
            if key == 'rupture_dict':
                params_to_print += params[key] + '\n'
            else:
                params_to_print += f'{key}: {val}\n'

    from_email = settings.EMAIL_HOST_USER
    to = [job_owner_email]
    reply_to = settings.EMAIL_SUPPORT
    body = (f"Input parameters:\n{params_to_print}\n\n")
    if warnings is not None:
        for warning in warnings:
            body += warning + '\n'
    if exc:
        job_id = job_id
        subject = f'Job {job_id} failed'
        body += f'There was an error running job {job_id}:\n{exc}'
    else:
        subject = f'Job {job_id} finished correctly'
        body += (f'Please find the results here:\n{outputs_uri}')
    EmailMessage(subject, body, from_email, to, reply_to=[reply_to]).send()


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def impact_get_rupture_data(request):
    """
    Retrieve rupture parameters corresponding to a given usgs id

    :param request:
        a `django.http.HttpRequest` object containing usgs_id
    """
    rupture_path = get_uploaded_file_path(request, 'rupture_file')
    station_data_file = get_uploaded_file_path(request, 'station_data_file')
    user = request.user
    user.testdir = None
    rup, rupdic, _oqparams, err = impact_validate(
        request.POST, user, rupture_path, station_data_file)
    if err:
        return HttpResponse(content=json.dumps(err), content_type=JSON,
                            status=400 if 'invalid_inputs' in err else 500)
    if rupdic.get('shakemap_array', None) is not None:
        shakemap_array = rupdic['shakemap_array']
        figsize = (6.3, 6.3)  # fitting in a single row in the template without resizing
        rupdic['pga_map_png'] = plot_shakemap(
            shakemap_array, 'PGA', backend='Agg', figsize=figsize,
            with_cities=False, return_base64=True, rupture=rup)
        rupdic['mmi_map_png'] = plot_shakemap(
            shakemap_array, 'MMI', backend='Agg', figsize=figsize,
            with_cities=False, return_base64=True, rupture=rup)
        del rupdic['shakemap_array']
    elif rup is not None:
        img_base64 = plot_rupture(rup, figsize=(8, 8), return_base64=True)
        rupdic['rupture_png'] = img_base64
    return HttpResponse(content=json.dumps(rupdic), content_type=JSON,
                        status=200)


def get_uploaded_file_path(request, filename):
    file = request.FILES.get(filename)
    if file:
        # NOTE: we could not find a reliable way to avoid the deletion of the
        # uploaded file right after the request is consumed, therefore we need
        # to store a copy of it
        return gettemp(open(file.temporary_file_path()).read(), suffix='.xml')


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def impact_run(request):
    """
    Run an ARISTOTLE calculation.

    :param request:
        a `django.http.HttpRequest` object containing
        usgs_id, rupture_file,
        lon, lat, dep, mag, rake, dip, strike,
        local_timestamp, time_event,
        maximum_distance, trt,
        truncation_level, number_of_ground_motion_fields,
        asset_hazard_distance, ses_seed,
        maximum_distance_stations, station_data_file
    """
    # NOTE: this is called via AJAX so the context processor isn't automatically
    # applied, since AJAX calls often do not render templates
    if request.user.level == 0:
        return HttpResponseForbidden()
    rupture_path = get_uploaded_file_path(request, 'rupture_file')
    station_data_file = get_uploaded_file_path(request, 'station_data_file')
    user = request.user
    user.testdir = None
    _rup, rupdic, params, err = impact_validate(
        request.POST, user, rupture_path, station_data_file)
    if err:
        return HttpResponse(content=json.dumps(err), content_type=JSON,
                            status=400 if 'invalid_inputs' in err else 500)
    for key in ['dip', 'strike']:
        if key in rupdic and rupdic[key] is None:
            del rupdic[key]
    [jobctx] = engine.create_jobs(
        [params], config.distribution.log_level, user_name=utils.get_user(request))

    job_owner_email = request.user.email
    response_data = dict()

    job_id = jobctx.calc_id
    outputs_uri_web = request.build_absolute_uri(
        reverse('outputs_impact', args=[job_id]))
    outputs_uri_api = request.build_absolute_uri(
        reverse('results', args=[job_id]))
    log_uri = request.build_absolute_uri(
        reverse('log', args=[job_id, '0', '']))
    traceback_uri = request.build_absolute_uri(
        reverse('traceback', args=[job_id]))
    response_data[job_id] = dict(
        status='created', job_id=job_id, outputs_uri=outputs_uri_api,
        log_uri=log_uri, traceback_uri=traceback_uri)
    if not job_owner_email:
        response_data[job_id]['WARNING'] = (
            'No email address is speficied for your user account,'
            ' therefore email notifications will be disabled. As soon as'
            ' the job completes, you can access its outputs at the'
            ' following link: %s. If the job fails, the error traceback'
            ' will be accessible at the following link: %s'
            % (outputs_uri_api, traceback_uri))

    # spawn the Aristotle main process
    proc = mp.Process(
        target=impact.main_web,
        args=([params], [jobctx], job_owner_email, outputs_uri_web,
              impact_callback))
    proc.start()

    return HttpResponse(content=json.dumps(response_data), content_type=JSON,
                        status=200)


def aelo_validate(request):
    validation_errs = {}
    invalid_inputs = []
    try:
        lon = valid.longitude(request.POST.get('lon'))
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['lon']] = str(exc)
        invalid_inputs.append('lon')
    try:
        lat = valid.latitude(request.POST.get('lat'))
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['lat']] = str(exc)
        invalid_inputs.append('lat')
    try:
        vs30 = valid.positivefloat(request.POST.get('vs30'))
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['vs30']] = str(exc)
        invalid_inputs.append('vs30')
    try:
        siteid = request.POST.get('siteid')
        if len(siteid) > settings.MAX_AELO_SITE_NAME_LEN:
            raise ValueError(
                "site name can not be longer than %s characters" %
                settings.MAX_AELO_SITE_NAME_LEN)
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['siteid']] = str(exc)
        invalid_inputs.append('siteid')
    try:
        asce_version = request.POST.get(
            'asce_version', oqvalidation.OqParam.asce_version.default)
        oqvalidation.OqParam.asce_version.validator(asce_version)
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['asce_version']] = str(exc)
        invalid_inputs.append('asce_version')
    if validation_errs:
        err_msg = 'Invalid input value'
        err_msg += 's\n' if len(validation_errs) > 1 else '\n'
        err_msg += '\n'.join(
            [f'{field.split(" (")[0]}: "{validation_errs[field]}"'
             for field in validation_errs])
        logging.error(err_msg)
        response_data = {"status": "failed", "error_msg": err_msg,
                         "invalid_inputs": invalid_inputs}
        return HttpResponse(content=json.dumps(response_data),
                            content_type=JSON, status=400)
    return lon, lat, vs30, siteid, asce_version


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def aelo_run(request):
    """
    Run an AELO calculation.

    :param request:
        a `django.http.HttpRequest` object containing lon, lat, vs30, siteid,
        asce_version
    """
    res = aelo_validate(request)
    if isinstance(res, HttpResponse):  # error
        return res
    lon, lat, vs30, siteid, asce_version = res

    # build a LogContext object associated to a database job
    try:
        params = get_params_from(
            dict(sites='%s %s' % (lon, lat), vs30=vs30, siteid=siteid,
                 asce_version=asce_version),
            config.directory.mosaic_dir, exclude=['USA'])
        logging.root.handlers = []  # avoid breaking the logs
    except Exception as exc:
        response_data = {'status': 'failed', 'error_cls': type(exc).__name__,
                         'error_msg': str(exc)}
        logging.error('', exc_info=True)
        return HttpResponse(
            content=json.dumps(response_data), content_type=JSON, status=400)
    [jobctx] = engine.create_jobs(
        [params],
        config.distribution.log_level, None, utils.get_user(request), None)
    job_id = jobctx.calc_id

    outputs_uri_web = request.build_absolute_uri(
        reverse('outputs_aelo', args=[job_id]))

    outputs_uri_api = request.build_absolute_uri(
        reverse('results', args=[job_id]))

    log_uri = request.build_absolute_uri(
        reverse('log', args=[job_id, '0', '']))

    traceback_uri = request.build_absolute_uri(
        reverse('traceback', args=[job_id]))

    response_data = dict(
        status='created', job_id=job_id, outputs_uri=outputs_uri_api,
        log_uri=log_uri, traceback_uri=traceback_uri)

    job_owner_email = request.user.email
    if not job_owner_email:
        response_data['WARNING'] = (
            'No email address is speficied for your user account,'
            ' therefore email notifications will be disabled. As soon as'
            ' the job completes, you can access its outputs at the following'
            ' link: %s. If the job fails, the error traceback will be'
            ' accessible at the following link: %s'
            % (outputs_uri_api, traceback_uri))

    # spawn the AELO main process
    mp.Process(target=aelo.main, args=(
        lon, lat, vs30, siteid, asce_version, job_owner_email, outputs_uri_web,
        jobctx, aelo_callback)).start()
    return HttpResponse(content=json.dumps(response_data), content_type=JSON,
                        status=200)


def submit_job(request_files, ini, username, hc_id):
    """
    Create a job object from the given files and run it in a new process.

    :returns: a job ID
    """
    # build a LogContext object associated to a database job
    [job] = engine.create_jobs(
        [dict(calculation_mode='custom',
              description='Calculation waiting to start')],
        config.distribution.log_level, None, username, hc_id)

    # store the request files and perform some validation
    try:
        job_ini = store(request_files, ini, job.calc_id)
        job.oqparam = oq = readinput.get_oqparam(
            job_ini, kw={'hazard_calculation_id': hc_id})
        dic = dict(calculation_mode=oq.calculation_mode,
                   description=oq.description, hazard_calculation_id=hc_id)
        logs.dbcmd('update_job', job.calc_id, dic)
        jobs = [job]
    except Exception as exc:
        tb = traceback.format_exc()
        logs.dbcmd('log', job.calc_id, datetime.now(UTC), 'CRITICAL',
                   'before starting', tb)
        logs.dbcmd('finish', job.calc_id, 'failed')
        exc.job_id = job.calc_id
        raise exc

    custom_tmp = os.path.dirname(job_ini)
    submit_cmd = config.distribution.submit_cmd.split()
    big_job = oq.get_input_size() > int(config.distribution.min_input_size)
    if submit_cmd == ENGINE:  # used for debugging
        for job in jobs:
            subprocess.Popen(submit_cmd + [save_pik(job, custom_tmp)])
    elif submit_cmd == KUBECTL and big_job:
        for job in jobs:
            with open(os.path.join(CWD, 'job.yaml')) as f:
                yaml = string.Template(f.read()).substitute(
                    DATABASE='%(host)s:%(port)d' % config.dbserver,
                    CALC_PIK=save_pik(job, custom_tmp),
                    CALC_NAME='calc%d' % job.calc_id)
            subprocess.run(submit_cmd, input=yaml.encode('ascii'))
    else:
        proc = mp.Process(target=engine.run_jobs, args=([job],))
        proc.start()
        if config.webapi.calc_timeout:
            mp.Process(
                target=engine.watchdog,
                args=(job.calc_id, proc.pid, int(config.webapi.calc_timeout))
            ).start()
    return job.calc_id


def save_pik(job, dirname):
    """
    Save a LogContext object in pickled format; returns the path to it
    """
    pathpik = os.path.join(dirname, 'calc%d.pik' % job.calc_id)
    with open(pathpik, 'wb') as f:
        pickle.dump([job], f)
    return pathpik


def get_public_outputs(oes):
    return [e for o, e in oes if o not in HIDDEN_OUTPUTS]


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_results(request, calc_id):
    """
    Get a summarized list of calculation results for a given ``calc_id``.
    Result is a JSON array of objects containing the following attributes:

        * id
        * name
        * type (hazard_curve, hazard_map, etc.)
        * url (the exact url where the full result can be accessed)
    """
    # If the specified calculation doesn't exist OR is not yet complete,
    # throw back a 404.
    try:
        info = logs.dbcmd('calc_info', calc_id)
        if not utils.user_has_permission(request, info['user_name'], info['status']):
            return HttpResponseForbidden()
    except dbapi.NotFound:
        return HttpResponseNotFound()
    base_url = _get_base_url(request)

    # NB: export_output has as keys the list (output_type, extension)
    # so this returns an ordered map output_type -> extensions such as
    # {'agg_loss_curve': ['xml', 'csv'], ...}
    output_types = groupby(export, lambda oe: oe[0],
                           get_public_outputs)
    results = logs.dbcmd('get_outputs', calc_id)
    if not results:
        return HttpResponseNotFound()

    response_data = []
    for result in results:
        try:  # output from the datastore
            rtype = result.ds_key
            # Catalina asked to remove the .txt outputs (used for the GMFs)
            outtypes = [ot for ot in output_types[rtype] if ot != 'txt']
        except KeyError:
            continue  # non-exportable outputs should not be shown
        url = urlparse.urljoin(base_url, 'v1/calc/result/%d' % result.id)
        datum = dict(
            id=result.id, name=result.display_name, type=rtype,
            outtypes=outtypes, url=url, size_mb=result.size_mb)
        response_data.append(datum)

    return HttpResponse(content=json.dumps(response_data))


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_traceback(request, calc_id):
    """
    Get the traceback as a list of lines for a given ``calc_id``.
    """
    # If the specified calculation doesn't exist throw back a 404.
    try:
        response_data = logs.dbcmd('get_traceback', calc_id)
    except dbapi.NotFound:
        return HttpResponseNotFound()
    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


@cross_domain_ajax
@require_http_methods(['GET', 'HEAD'])
def calc_result(request, result_id):
    """
    Download a specific result, by ``result_id``.

    The common abstracted functionality for getting hazard or risk results.

    :param request:
        `django.http.HttpRequest` object. Can contain a `export_type` GET
        param (the default is 'xml' if no param is specified).
    :param result_id:
        The id of the requested artifact.
    :returns:
        If the requested ``result_id`` is not available in the format
        designated by the `export_type`.

        Otherwise, return a `django.http.HttpResponse` containing the content
        of the requested artifact.

    Parameters for the GET request can include an `export_type`, such as 'xml',
    'geojson', 'csv', etc.
    """
    # If the result for the requested ID doesn't exist, OR
    # the job which it is related too is not complete,
    # throw back a 404.
    try:
        job_id, job_status, job_user, datadir, ds_key = logs.dbcmd(
            'get_result', result_id)
        if ds_key in HIDDEN_OUTPUTS:
            return HttpResponseForbidden()
        if not utils.user_has_permission(request, job_user, job_status):
            return HttpResponseForbidden()
    except dbapi.NotFound:
        return HttpResponseNotFound()

    etype = request.GET.get('export_type')
    export_type = etype or DEFAULT_EXPORT_TYPE

    # NOTE: for some reason, in some cases the environment variable TMPDIR is
    # ignored, so we need to use config.directory.custom_tmp if defined
    temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
    tmpdir = tempfile.mkdtemp(dir=temp_dir)
    try:
        exported = core.export_from_db(
            (ds_key, export_type), job_id, datadir, tmpdir)
    except DataStoreExportError as exc:
        # TODO: there should be a better error page
        return HttpResponse(content='%s: %s' % (exc.__class__.__name__, exc),
                            content_type='text/plain', status=500)
    if not exported:
        # Throw back a 404 if the exact export parameters are not supported
        return HttpResponseNotFound(
            'Nothing to export for export_type=%s, %s' % (export_type, ds_key))
    elif len(exported) > 1:
        # Building an archive so that there can be a single file download
        archname = ds_key + '-' + export_type + '.zip'
        zipfiles(exported, os.path.join(tmpdir, archname))
        exported = os.path.join(tmpdir, archname)
    else:  # single file
        exported = exported[0]

    content_type = EXPORT_CONTENT_TYPE_MAP.get(
        export_type, DEFAULT_CONTENT_TYPE)

    fname = 'output-%s-%s' % (result_id, os.path.basename(exported))
    stream = FileWrapper(open(exported, 'rb'))  # 'b' is needed on Windows
    stream.close = lambda: (
        FileWrapper.close(stream), shutil.rmtree(tmpdir))
    response = FileResponse(stream, content_type=content_type)
    response['Content-Disposition'] = (
        'attachment; filename=%s' % os.path.basename(fname))
    response['Content-Length'] = str(os.path.getsize(exported))
    return response


@cross_domain_ajax
@require_http_methods(['GET', 'HEAD'])
def aggrisk_tags(request, calc_id):
    """
    Return aggrisk_tags, by ``calc_id``, as JSON.

    :param request:
        `django.http.HttpRequest` object.
    :param calc_id:
        The id of the requested calculation.
    :returns:
        a JSON object as documented in rest-api.rst
    """
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name, job.status):
        return HttpResponseForbidden()
    try:
        with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
            df = _extract(ds, 'aggrisk_tags')
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        return HttpResponse(
            content='%s: %s in %s\n%s' %
            (exc.__class__.__name__, exc, 'aggrisk_tags', tb),
            content_type='text/plain', status=400)

    return HttpResponse(content=df.to_json(),
                        content_type=JSON, status=200)


@cross_domain_ajax
@require_http_methods(['GET', 'HEAD'])
def extract(request, calc_id, what):
    """
    Wrapper over the `oq extract` command. If `setting.LOCKDOWN` is true
    only calculations owned by the current user can be retrieved.
    """
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name, job.status):
        return HttpResponseForbidden()
    path = request.get_full_path()
    n = len(request.path_info)
    query_string = unquote_plus(path[n:])
    try:
        # read the data and save them on a temporary .npz file
        with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
            # NOTE: for some reason, in some cases the environment
            # variable TMPDIR is ignored, so we need to use
            # config.directory.custom_tmp if defined
            temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
            fd, fname = tempfile.mkstemp(
                prefix=what.replace('/', '-'), suffix='.npz', dir=temp_dir)
            os.close(fd)
            obj = _extract(ds, what + query_string)
            hdf5.save_npz(obj, fname)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        return HttpResponse(
            content='%s: %s in %s\n%s' %
            (exc.__class__.__name__, exc, path, tb),
            content_type='text/plain', status=500)

    # stream the data back
    stream = FileWrapper(open(fname, 'rb'))
    stream.close = lambda: (FileWrapper.close(stream), os.remove(fname))
    response = FileResponse(stream, content_type='application/octet-stream')
    response['Content-Disposition'] = (
        'attachment; filename=%s' % os.path.basename(fname))
    response['Content-Length'] = str(os.path.getsize(fname))
    return response


@cross_domain_ajax
@require_http_methods(['GET'])
def calc_datastore(request, job_id):
    """
    Download a full datastore file.

    :param request:
        `django.http.HttpRequest` object.
    :param job_id:
        The id of the requested datastore
    :returns:
        A `django.http.HttpResponse` containing the content
        of the requested artifact, if present, else throws a 404
    """
    job = logs.dbcmd('get_job', int(job_id))
    if job is None or not os.path.exists(job.ds_calc_dir + '.hdf5'):
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name, job.status):
        return HttpResponseForbidden()

    fname = job.ds_calc_dir + '.hdf5'
    response = FileResponse(
        FileWrapper(open(fname, 'rb')), content_type=HDF5)
    response['Content-Disposition'] = (
        'attachment; filename=%s' % os.path.basename(fname))
    response['Content-Length'] = str(os.path.getsize(fname))
    return response


def web_engine(request, **kwargs):
    application_mode = settings.APPLICATION_MODE
    # NOTE: application_mode is already added by the context processor
    params = {}
    if application_mode == 'AELO':
        params['aelo_form_labels'] = AELO_FORM_LABELS
        params['aelo_form_placeholders'] = AELO_FORM_PLACEHOLDERS
        params['asce_versions'] = (
            oqvalidation.OqParam.asce_version.validator.choices)
        params['default_asce_version'] = (
            oqvalidation.OqParam.asce_version.default)
    elif application_mode == 'ARISTOTLE':
        params['impact_form_labels'] = ARISTOTLE_FORM_LABELS
        params['impact_form_placeholders'] = ARISTOTLE_FORM_PLACEHOLDERS
        params['impact_default_usgs_id'] = \
            settings.ARISTOTLE_DEFAULT_USGS_ID
    return render(
        request, "engine/index.html", params)


@cross_domain_ajax
@require_http_methods(['GET'])
def web_engine_get_outputs(request, calc_id, **kwargs):
    application_mode = settings.APPLICATION_MODE
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        return HttpResponseNotFound()
    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        if 'png' in ds:
            # NOTE: only one hmap can be visualized currently
            hmaps = any([k.startswith('hmap') for k in ds['png']])
            avg_gmf = [k for k in ds['png'] if k.startswith('avg_gmf-')]
            assets = 'assets.png' in ds['png']
            hcurves = 'hcurves.png' in ds['png']
            # NOTE: remove "and 'All' in k" to show the individual plots
            disagg_by_src = [k for k in ds['png']
                             if k.startswith('disagg_by_src-') and 'All' in k]
            governing_mce = 'governing_mce.png' in ds['png']
        else:
            hmaps = assets = hcurves = governing_mce = False
            avg_gmf = []
            disagg_by_src = []
    size_mb = '?' if job.size_mb is None else '%.2f' % job.size_mb
    lon = lat = vs30 = site_name = None
    if application_mode == 'AELO':
        lon, lat = ds['oqparam'].sites[0][:2]  # e.g. [[-61.071, 14.686, 0.0]]
        vs30 = ds['oqparam'].override_vs30  # e.g. 760.0
        site_name = ds['oqparam'].description[9:]  # e.g. 'AELO for CCA'->'CCA'
    return render(request, "engine/get_outputs.html",
                  dict(calc_id=calc_id, size_mb=size_mb, hmaps=hmaps,
                       avg_gmf=avg_gmf, assets=assets, hcurves=hcurves,
                       disagg_by_src=disagg_by_src,
                       governing_mce=governing_mce,
                       lon=lon, lat=lat, vs30=vs30, site_name=site_name,)
                  )


def is_model_preliminary(ds):
    # TODO: it would be better having the model written explicitly into the
    # datastore
    model = ds['oqparam'].base_path.split(os.path.sep)[-2]
    if model in PRELIMINARY_MODELS:
        return True
    else:
        return False


def get_disp_val(val):
    # gets the value displayed in the webui according to the rounding rules
    if val >= 1.0:
        return '{:.2f}'.format(numpy.round(val, 2))
    elif val < 0.0001:
        return f'{val:.1f}'
    elif val < 0.01:
        return '{:.4f}'.format(numpy.round(val, 4))
    elif val < 0.1:
        return '{:.3f}'.format(numpy.round(val, 3))
    else:
        return '{:.2f}'.format(numpy.round(val, 2))


# this is extracting only the first site and it is okay
@cross_domain_ajax
@require_http_methods(['GET'])
def web_engine_get_outputs_aelo(request, calc_id, **kwargs):
    job = logs.dbcmd('get_job', calc_id)
    size_mb = '?' if job.size_mb is None else '%.2f' % job.size_mb
    asce07 = asce41 = None
    asce07_with_units = {}
    asce41_with_units = {}
    warnings = None
    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        if is_model_preliminary(ds):
            warnings = PRELIMINARY_MODEL_WARNING
        if 'asce07' in ds:
            try:
                asce07_js = ds['asce07'][0].decode('utf8')
            except ValueError:
                # NOTE: for backwards compatibility, read scalar
                asce07_js = ds['asce07'][()].decode('utf8')
            asce07 = json.loads(asce07_js)
            for key, value in asce07.items():
                if key not in ('PGA', 'Ss', 'S1'):
                    continue
                if not isinstance(value, float):
                    asce07_with_units[key] = value
                elif key in ('CRs', 'CR1'):
                    # NOTE: (-) stands for adimensional
                    asce07_with_units[key + ' (-)'] = get_disp_val(value)
                else:
                    asce07_with_units[key + ' (g)'] = get_disp_val(value)
        if 'asce41' in ds:
            try:
                asce41_js = ds['asce41'][0].decode('utf8')
            except ValueError:
                # NOTE: for backwards compatibility, read scalar
                asce41_js = ds['asce41'][()].decode('utf8')
            asce41 = json.loads(asce41_js)
            for key, value in asce41.items():
                if not key.startswith('BSE'):
                    continue
                if not isinstance(value, float):
                    asce41_with_units[key] = value
                else:
                    asce41_with_units[key + ' (g)'] = get_disp_val(value)
        lon, lat = ds['oqparam'].sites[0][:2]  # e.g. [[-61.071, 14.686, 0.0]]
        vs30 = ds['oqparam'].override_vs30  # e.g. 760.0
        site_name = ds['oqparam'].description[9:]  # e.g. 'AELO for CCA'->'CCA'
        try:
            asce_version = ds['oqparam'].asce_version
        except AttributeError:
            # for backwards compatibility on old calculations
            asce_version = oqvalidation.OqParam.asce_version.default
        try:
            calc_aelo_version = ds.get_attr('/', 'aelo_version')
        except KeyError:
            calc_aelo_version = '1.0.0'
        if 'warnings' in ds:
            ds_warnings = '\n'.join(s.decode('utf8') for s in ds['warnings'])
            if warnings is None:
                warnings = ds_warnings
            else:
                warnings += '\n' + ds_warnings
    return render(request, "engine/get_outputs_aelo.html",
                  dict(calc_id=calc_id, size_mb=size_mb,
                       asce07=asce07_with_units, asce41=asce41_with_units,
                       lon=lon, lat=lat, vs30=vs30, site_name=site_name,
                       calc_aelo_version=calc_aelo_version,
                       asce_version=asce_version,
                       warnings=warnings))


def format_time_delta(td):
    days = td.days
    seconds = td.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    # Format without microseconds
    formatted_time = f'{days} days, {hours:02}:{minutes:02}:{seconds:02}'
    return formatted_time


def determine_precision(weights):
    """
    Determine the minimum decimal places needed to represent the weights accurately
    """
    max_decimal_places = 0
    for weight in weights:
        str_weight = f"{weight:.10f}".rstrip("0")  # Remove trailing zeros
        decimal_places = str_weight[::-1].find('.')  # Count decimal places
        max_decimal_places = max(max_decimal_places, decimal_places)
    return max_decimal_places


@cross_domain_ajax
@require_http_methods(['GET'])
def web_engine_get_outputs_impact(request, calc_id):
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        return HttpResponseNotFound()
    description = job.description
    job_start_time = job.start_time
    job_start_time_str = job.start_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
    local_timestamp_str = None
    time_job_after_event = None
    time_job_after_event_str = None
    warnings = None
    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        try:
            losses = views.view('aggrisk', ds)
        except KeyError:
            max_avg_gmf = ds['avg_gmf'][0].max()
            losses = (f'The risk can not be computed since the hazard is too low:'
                      f' the maximum value of the average GMF is {max_avg_gmf:.5f}')
            losses_header = None
        else:
            losses_header = [
                f'{field}<br><i>{FIELD_DESCRIPTION[field]}</i>'
                if field in FIELD_DESCRIPTION
                else field.capitalize()
                for field in losses.dtype.names]
            weights_precision = determine_precision(losses['weight'])
        if 'png' in ds:
            avg_gmf = [k for k in ds['png'] if k.startswith('avg_gmf-')]
            assets = 'assets.png' in ds['png']
        else:
            assets = False
            avg_gmf = []
        oqparam = ds['oqparam']
        if hasattr(oqparam, 'local_timestamp'):
            local_timestamp_str = (
                oqparam.local_timestamp if oqparam.local_timestamp != 'None'
                else None)
    size_mb = '?' if job.size_mb is None else '%.2f' % job.size_mb
    if 'warnings' in ds:
        ds_warnings = '\n'.join(s.decode('utf8') for s in ds['warnings'])
        if warnings is None:
            warnings = ds_warnings
        else:
            warnings += '\n' + ds_warnings
    if local_timestamp_str is not None:
        local_timestamp = datetime.strptime(
            local_timestamp_str, '%Y-%m-%d %H:%M:%S%z')
        time_job_after_event = (
            job_start_time.replace(tzinfo=timezone.utc) - local_timestamp)
        time_job_after_event_str = format_time_delta(time_job_after_event)
    return render(request, "engine/get_outputs_impact.html",
                  dict(calc_id=calc_id, description=description,
                       local_timestamp=local_timestamp_str,
                       job_start_time=job_start_time_str,
                       time_job_after_event=time_job_after_event_str,
                       size_mb=size_mb, losses=losses,
                       losses_header=losses_header,
                       weights_precision=weights_precision,
                       avg_gmf=avg_gmf, assets=assets,
                       warnings=warnings))


@cross_domain_ajax
@require_http_methods(['GET'])
def download_aggrisk(request, calc_id):
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name, job.status):
        return HttpResponseForbidden()
    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        losses = views.view('aggrisk', ds)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="aggrisk_%s.csv"' % calc_id
        },
    )
    writer = csv.writer(response)
    writer.writerow(losses.dtype.names)
    for row in losses:
        writer.writerow(row)
    return response


@cross_domain_ajax
@require_http_methods(['GET'])
def extract_html_table(request, calc_id, name):
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name, job.status):
        return HttpResponseForbidden()
    try:
        with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
            table = _extract(ds, name)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        return HttpResponse(
            content='%s: %s in %s\n%s' %
            (exc.__class__.__name__, exc, name, tb),
            content_type='text/plain', status=400)
    table_html = table.to_html(classes="table table-striped", index=False)
    return render(request, 'engine/show_table.html',
                  {'table_name': name, 'table_html': table_html})


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def on_same_fs(request):
    """
    Accept a POST request to check access to a FS available by a client.

    :param request:
        `django.http.HttpRequest` object, containing mandatory parameters
        filename and checksum.
    """
    filename = request.POST['filename']
    checksum_in = request.POST['checksum']

    checksum = 0
    try:
        data = open(filename, 'rb').read(32)
        checksum = zlib.adler32(data, checksum) & 0xffffffff
        if checksum == int(checksum_in):
            return HttpResponse(content=json.dumps({'success': True}),
                                content_type=JSON, status=200)
    except (IOError, ValueError):
        pass

    return HttpResponse(content=json.dumps({'success': False}),
                        content_type=JSON, status=200)


@require_http_methods(['GET'])
def license(request, **kwargs):
    return render(request, "engine/license.html")


@require_http_methods(['GET'])
def aelo_changelog(request, **kwargs):
    aelo_changelog = base.get_aelo_changelog()
    aelo_changelog_html = aelo_changelog.to_html(
        index=False, escape=False, classes='changelog', border=0)
    return render(request, "engine/aelo_changelog.html",
                  dict(aelo_changelog=aelo_changelog_html))
