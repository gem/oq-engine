# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
from datetime import datetime
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

from openquake.baselib import hdf5, config
from openquake.baselib.general import groupby, gettemp, zipfiles, mp
from openquake.hazardlib import nrml, gsim, valid
from openquake.commonlib import readinput, oqvalidation, logs, datastore, dbapi
from openquake.calculators import base
from openquake.calculators.getters import NotFound
from openquake.calculators.export import export
from openquake.calculators.extract import extract as _extract
from openquake.engine import __version__ as oqversion
from openquake.engine.export import core
from openquake.engine import engine, aelo
from openquake.engine.aelo import get_params_from
from openquake.engine.export.core import DataStoreExportError
from openquake.server import utils

from django.conf import settings
from django.http import FileResponse
from django.urls import reverse
from wsgiref.util import FileWrapper

if settings.LOCKDOWN:
    from django.contrib.auth import authenticate, login, logout

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

AELO_FORM_PLACEHOLDERS = {
    'lon': 'Longitude',
    'lat': 'Latitude',
    'vs30': 'Vs30 (fixed at 760 m/s)',
    'siteid': 'Site name',
}

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
    tmp = config.directory.custom_tmp or tempfile.mkdtemp()
    calc_dir = os.path.join(tmp, 'calc_%d' % calc_id)
    os.mkdir(calc_dir)
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
    if not utils.user_has_permission(request, job.user_name):
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
        if not utils.user_has_permission(request, info['user_name']):
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
    calc_data = logs.dbcmd('get_calcs', request.GET,
                           utils.get_valid_users(request),
                           not utils.is_superuser(request), id)

    response_data = []
    username = psutil.Process(os.getpid()).username()
    for (hc_id, owner, status, calculation_mode, is_running, desc, pid,
         parent_id, size_mb, host) in calc_data:
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
        response_data.append(
            dict(id=hc_id, owner=owner,
                 calculation_mode=calculation_mode, status=status,
                 is_running=bool(is_running), description=desc, url=url,
                 parent_id=parent_id, abortable=abortable, size_mb=size_mb))

    # if id is specified the related dictionary is returned instead the list
    if id is not None:
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


def aelo_callback(job_id, job_owner_email, outputs_uri, inputs, exc=None):
    if not job_owner_email:
        return
    from_email = 'aelonoreply@openquake.org'
    to = [job_owner_email]
    reply_to = 'aelosupport@openquake.org'
    body = (f"Input values: lon = {inputs['lon']}, lat = {inputs['lat']},"
            f" vs30 = {inputs['vs30']}, siteid = {inputs['siteid']}\n\n")
    if exc:
        subject = f'Job {job_id} failed'
        body += f'There was an error running job {job_id}:\n{exc}'
    else:
        subject = f'Job {job_id} finished correctly'
        body += (f'Please find the results here:\n{outputs_uri}')
    EmailMessage(subject, body, from_email, to, reply_to=[reply_to]).send()


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def aelo_run(request):
    """
    Run an AELO calculation.

    :param request:
        a `django.http.HttpRequest` object containing lon, lat, vs30, siteid
    """
    validation_errs = {}
    invalid_inputs = []
    try:
        lon = valid.longitude(request.POST.get('lon'))
    except Exception as exc:
        validation_errs[AELO_FORM_PLACEHOLDERS['lon']] = str(exc)
        invalid_inputs.append('lon')
    try:
        lat = valid.latitude(request.POST.get('lat'))
    except Exception as exc:
        validation_errs[AELO_FORM_PLACEHOLDERS['lat']] = str(exc)
        invalid_inputs.append('lat')
    try:
        vs30 = valid.positivefloat(request.POST.get('vs30'))
    except Exception as exc:
        validation_errs[AELO_FORM_PLACEHOLDERS['vs30']] = str(exc)
        invalid_inputs.append('vs30')
    try:
        siteid = valid.simple_id(request.POST.get('siteid'))
    except Exception as exc:
        validation_errs[AELO_FORM_PLACEHOLDERS['siteid']] = str(exc)
        invalid_inputs.append('siteid')
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

    # build a LogContext object associated to a database job
    try:
        params = get_params_from(
            dict(lon=lon, lat=lat, vs30=vs30, siteid=siteid))
        logging.root.handlers = []  # avoid breaking the logs
    except Exception as exc:
        response_data = {'status': 'failed', 'error_cls': type(exc).__name__,
                         'error_msg': str(exc)}
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
        lon, lat, vs30, siteid, job_owner_email, outputs_uri_web, jobctx,
        aelo_callback)).start()
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
        if oq.sensitivity_analysis:
            logs.dbcmd('set_status', job.calc_id, 'deleted')  # hide it
            jobs = engine.create_jobs([job_ini], config.distribution.log_level,
                                      None, username, hc_id, True)
        else:
            dic = dict(calculation_mode=oq.calculation_mode,
                       description=oq.description, hazard_calculation_id=hc_id)
            logs.dbcmd('update_job', job.calc_id, dic)
            jobs = [job]
    except Exception as exc:
        tb = traceback.format_exc()
        logs.dbcmd('log', job.calc_id, datetime.utcnow(), 'CRITICAL',
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
        mp.Process(target=engine.run_jobs, args=(jobs,)).start()
    return job.calc_id


def save_pik(job, dirname):
    """
    Save a LogContext object in pickled format; returns the path to it
    """
    pathpik = os.path.join(dirname, 'calc%d.pik' % job.calc_id)
    with open(pathpik, 'wb') as f:
        pickle.dump(job, f)
    return pathpik


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
        if not utils.user_has_permission(request, info['user_name']):
            return HttpResponseForbidden()
    except dbapi.NotFound:
        return HttpResponseNotFound()
    base_url = _get_base_url(request)

    # NB: export_output has as keys the list (output_type, extension)
    # so this returns an ordered map output_type -> extensions such as
    # {'agg_loss_curve': ['xml', 'csv'], ...}
    output_types = groupby(export, lambda oe: oe[0],
                           lambda oes: [e for o, e in oes])
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
        if not utils.user_has_permission(request, job_user):
            return HttpResponseForbidden()
    except dbapi.NotFound:
        return HttpResponseNotFound()

    etype = request.GET.get('export_type')
    export_type = etype or DEFAULT_EXPORT_TYPE

    tmpdir = tempfile.mkdtemp()
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
def extract(request, calc_id, what):
    """
    Wrapper over the `oq extract` command. If `setting.LOCKDOWN` is true
    only calculations owned by the current user can be retrieved.
    """
    job = logs.dbcmd('get_job', int(calc_id))
    if job is None:
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name):
        return HttpResponseForbidden()
    path = request.get_full_path()
    n = len(request.path_info)
    query_string = unquote_plus(path[n:])
    try:
        # read the data and save them on a temporary .npz file
        with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
            fd, fname = tempfile.mkstemp(
                prefix=what.replace('/', '-'), suffix='.npz')
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
    if not utils.user_has_permission(request, job.user_name):
        return HttpResponseForbidden()

    fname = job.ds_calc_dir + '.hdf5'
    response = FileResponse(
        FileWrapper(open(fname, 'rb')), content_type=HDF5)
    response['Content-Disposition'] = (
        'attachment; filename=%s' % os.path.basename(fname))
    response['Content-Length'] = str(os.path.getsize(fname))
    return response


def web_engine(request, **kwargs):
    application_mode = settings.APPLICATION_MODE.upper()
    params = {'application_mode': application_mode}
    if application_mode == 'AELO':
        params['aelo_form_placeholders'] = AELO_FORM_PLACEHOLDERS
    return render(
        request, "engine/index.html", params)


@cross_domain_ajax
@require_http_methods(['GET'])
def web_engine_get_outputs(request, calc_id, **kwargs):
    application_mode = settings.APPLICATION_MODE.upper()
    job = logs.dbcmd('get_job', calc_id)
    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        if 'png' in ds:
            # NOTE: only one hmap can be visualized currently
            hmaps = any([k.startswith('hmap') for k in ds['png']])
            hcurves = 'hcurves.png' in ds['png']
            disagg_by_src = [k for k in ds['png']
                             if k.startswith('disagg_by_src-')]
            governing_mce = 'governing_mce.png' in ds['png']
        else:
            hmaps = hcurves = governing_mce = False
            disagg_by_src = []
    size_mb = '?' if job.size_mb is None else '%.2f' % job.size_mb
    return render(request, "engine/get_outputs.html",
                  dict(calc_id=calc_id, size_mb=size_mb, hmaps=hmaps,
                       hcurves=hcurves,
                       disagg_by_src=disagg_by_src,
                       governing_mce=governing_mce,
                       application_mode=application_mode))


@cross_domain_ajax
@require_http_methods(['GET'])
def web_engine_get_outputs_aelo(request, calc_id, **kwargs):
    job = logs.dbcmd('get_job', calc_id)
    size_mb = '?' if job.size_mb is None else '%.2f' % job.size_mb
    asce7 = asce41 = None
    asce7_with_units = {}
    asce41_with_units = {}
    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        if 'asce7' in ds:
            asce7_js = ds['asce7'][()].decode('utf8')
            asce7 = json.loads(asce7_js)
            for key, value in asce7.items():
                if not isinstance(value, float):
                    asce7_with_units[key] = value
                elif key in ('CRS', 'CR1'):
                    # NOTE: (-) stands for adimensional
                    asce7_with_units[key + ' (-)'] = value
                else:
                    asce7_with_units[key + ' (g)'] = value
        if 'asce41' in ds:
            asce41_js = ds['asce41'][()].decode('utf8')
            asce41 = json.loads(asce41_js)
            for key, value in asce41.items():
                asce41_with_units[key + ' (g)'] = value
        low_hazard = asce7 is None or asce41 is None
    return render(request, "engine/get_outputs_aelo.html",
                  dict(calc_id=calc_id, size_mb=size_mb,
                       asce7=asce7_with_units, asce41=asce41_with_units,
                       low_hazard=low_hazard))


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
