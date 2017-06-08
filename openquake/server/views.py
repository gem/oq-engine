# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
import logging
import os
import getpass
import tempfile
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
import re

from xml.parsers.expat import ExpatError
from django.http import (
    HttpResponse, HttpResponseNotFound, HttpResponseBadRequest)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

from openquake.baselib.general import groupby, writetmp
from openquake.baselib.python3compat import unicode
from openquake.baselib.parallel import Starmap, safely_call
from openquake.hazardlib import nrml, gsim
from openquake.risklib import read_nrml

from openquake.commonlib import readinput, oqvalidation, logs, datastore
from openquake.calculators.export import export
from openquake.engine import __version__ as oqversion
from openquake.engine.export import core
from openquake.engine import engine
from openquake.engine.export.core import DataStoreExportError
from openquake.server import executor, utils, dbapi

from django.conf import settings
if settings.LOCKDOWN:
    from django.contrib.auth import authenticate, login, logout
try:
    from django.http import FileResponse  # Django >= 1.8
except ImportError:
    from django.http import StreamingHttpResponse as FileResponse
try:
    from wsgiref.util import FileWrapper  # Django >= 1.9
except ImportError:
    from django.core.servers.basehttp import FileWrapper

read_nrml.update_validators()  # update risk validators

METHOD_NOT_ALLOWED = 405
NOT_IMPLEMENTED = 501

XML = 'application/xml'
JSON = 'application/json'
HDF5 = 'application/x-hdf'

DEFAULT_LOG_LEVEL = 'info'

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


def _prepare_job(request, candidates):
    """
    Creates a temporary directory, move uploaded files there and
    select the job file by looking at the candidate names.

    :returns: full path of the job_file
    """
    temp_dir = tempfile.mkdtemp()
    inifiles = []
    arch = request.FILES.get('archive')
    if arch is None:
        # move each file to a new temp dir, using the upload file names,
        # not the temporary ones
        for each_file in request.FILES.values():
            new_path = os.path.join(temp_dir, each_file.name)
            shutil.move(each_file.temporary_file_path(), new_path)
            if each_file.name in candidates:
                inifiles.append(new_path)
        return inifiles
    # else extract the files from the archive into temp_dir
    return readinput.extract_from_zip(arch, candidates)


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
def get_available_gsims(request):
    """
    Return a list of strings with the available GSIMs
    """
    gsims = list(gsim.get_available_gsims())
    return HttpResponse(content=json.dumps(gsims), content_type=JSON)


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
    xml_file = writetmp(xml_text, suffix='.xml')
    try:
        nrml.parse(xml_file)
    except ExpatError as exc:
        return _make_response(error_msg=str(exc),
                              error_line=exc.lineno,
                              valid=False)
    except Exception as exc:
        # get the exception message
        exc_msg = exc.args[0]
        if isinstance(exc_msg, bytes):
            exc_msg = exc_msg.decode('utf-8')   # make it a unicode object
        elif isinstance(exc_msg, unicode):
            pass
        else:
            # if it is another kind of object, it is not obvious a priori how
            # to extract the error line from it
            return _make_response(
                error_msg=unicode(exc_msg), error_line=None, valid=False)
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


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_info(request, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    try:
        info = logs.dbcmd('calc_info', calc_id)
    except dbapi.NotFound:
        return HttpResponseNotFound()
    return HttpResponse(content=json.dumps(info), content_type=JSON)


@require_http_methods(['GET'])
@cross_domain_ajax
def calc(request, id=None):
    """
    Get a list of calculations and report their id, status, job_type,
    is_running, description, and a url where more detailed information
    can be accessed. This is called several times by the Javascript.

    Responses are in JSON.
    """
    base_url = _get_base_url(request)

    user = utils.get_user_data(request)

    calc_data = logs.dbcmd('get_calcs', request.GET,
                           user['name'], user['acl_on'], id)

    response_data = []
    for hc_id, owner, status, job_type, is_running, desc in calc_data:
        url = urlparse.urljoin(base_url, 'v1/calc/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, owner=owner, status=status, job_type=job_type,
                 is_running=bool(is_running), description=desc, url=url))

    # if id is specified the related dictionary is returned instead the list
    if id is not None:
        [response_data] = response_data

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def calc_remove(request, calc_id):
    """
    Remove the calculation id
    """
    user = utils.get_user_data(request)['name']
    try:
        message = logs.dbcmd('del_calc', calc_id, user)
    except dbapi.NotFound:
        return HttpResponseNotFound()
    if isinstance(message, list):  # list of removed files
        return HttpResponse(content=json.dumps(message),
                            content_type=JSON, status=200)
    else:  # FIXME: the error is not passed properly to the javascript
        logging.error(message)
        return HttpResponse(content=message,
                            content_type='text/plain', status=500)


def log_to_json(log):
    """Convert a log record into a list of strings"""
    return [log.timestamp.isoformat()[:22],
            log.level, log.process, log.message]


@require_http_methods(['GET'])
@cross_domain_ajax
def get_log_slice(request, calc_id, start, stop):
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
def get_log_size(request, calc_id):
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
def run_calc(request):
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
    hazard_job_id = request.POST.get('hazard_job_id')

    if hazard_job_id:
        hazard_job_id = int(hazard_job_id)
        candidates = ("job_risk.ini", "job.ini")
    else:
        candidates = ("job_hazard.ini", "job_haz.ini", "job.ini")
    einfo, exctype, monitor = safely_call(_prepare_job, (request, candidates))
    if exctype:
        return HttpResponse(json.dumps(einfo.splitlines()),
                            content_type=JSON, status=500)
    if not einfo:
        msg = 'Could not find any file of the form %s' % str(candidates)
        logging.error(msg)
        return HttpResponse(content=json.dumps([msg]), content_type=JSON,
                            status=500)

    user = utils.get_user_data(request)
    try:
        job_id, fut = submit_job(einfo[0], user['name'], hazard_job_id)
        # restart the process pool at the end of each job
        fut .add_done_callback(lambda f: Starmap.restart())
    except Exception as exc:  # no job created, for instance missing .xml file
        # get the exception message
        exc_msg = str(exc)
        logging.error(exc_msg)
        response_data = exc_msg.splitlines()
        status = 500
    else:
        response_data = dict(job_id=job_id, status='created')
        status = 200
    return HttpResponse(content=json.dumps(response_data), content_type=JSON,
                        status=status)


def submit_job(job_ini, user_name, hazard_job_id=None,
               loglevel=DEFAULT_LOG_LEVEL, logfile=None, exports=''):
    """
    Create a job object from the given job.ini file in the job directory
    and submit it to the job queue. Returns the job ID.
    """
    job_id, oqparam = engine.job_from_file(job_ini, user_name, hazard_job_id)
    fut = executor.submit(engine.run_calc, job_id, oqparam, loglevel,
                          logfile, exports, hazard_job_id)
    return job_id, fut


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
    user = utils.get_user_data(request)

    # If the specified calculation doesn't exist OR is not yet complete,
    # throw back a 404.
    try:
        info = logs.dbcmd('calc_info', calc_id)
        if user['acl_on'] and info['user_name'] != user['name']:
            return HttpResponseNotFound()
    except dbapi.NotFound:
        return HttpResponseNotFound()
    base_url = _get_base_url(request)

    # NB: export_output has as keys the list (output_type, extension)
    # so this returns an ordered map output_type -> extensions such as
    # OrderedDict([('agg_loss_curve', ['xml', 'csv']), ...])
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
            outtypes=outtypes, url=url)
        response_data.append(datum)

    return HttpResponse(content=json.dumps(response_data))


@require_http_methods(['GET'])
@cross_domain_ajax
def get_traceback(request, calc_id):
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
def get_result(request, result_id):
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
        job_id, job_status, datadir, ds_key = logs.dbcmd(
            'get_result', result_id)
        if not job_status == 'complete':
            return HttpResponseNotFound()
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
    if exported is None:
        # Throw back a 404 if the exact export parameters are not supported
        return HttpResponseNotFound(
            'export_type=%s is not supported for %s' % (export_type, ds_key))

    content_type = EXPORT_CONTENT_TYPE_MAP.get(
        export_type, DEFAULT_CONTENT_TYPE)

    bname = os.path.basename(exported)
    if bname.startswith('.'):
        # the "." is added by `export_from_db`, strip it
        bname = bname[1:]
    fname = 'output-%s-%s' % (result_id, bname)
    # 'b' is needed when running the WebUI on Windows
    stream = FileWrapper(open(exported, 'rb'))
    stream.close = lambda: (
        FileWrapper.close(stream), shutil.rmtree(tmpdir))
    response = FileResponse(stream, content_type=content_type)
    response['Content-Disposition'] = (
        'attachment; filename=%s' % os.path.basename(fname))
    return response


@cross_domain_ajax
@require_http_methods(['GET'])
def get_datastore(request, job_id):
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
    try:
        job = logs.dbcmd('get_job', int(job_id), getpass.getuser())
    except dbapi.NotFound:
        return HttpResponseNotFound()

    fname = job.ds_calc_dir + '.hdf5'
    response = FileResponse(
        FileWrapper(open(fname, 'rb')), content_type=HDF5)
    response['Content-Disposition'] = (
        'attachment; filename=%s' % os.path.basename(fname))
    return response


@cross_domain_ajax
@require_http_methods(['GET'])
def get_oqparam(request, job_id):
    """
    Return the calculation parameters as a JSON
    """
    try:
        job = logs.dbcmd('get_job', int(job_id), getpass.getuser())
    except dbapi.NotFound:
        return HttpResponseNotFound()
    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        oq = ds['oqparam']
    return HttpResponse(content=json.dumps(vars(oq)), content_type=JSON)


def web_engine(request, **kwargs):
    return render(request, "engine/index.html",
                  dict())


@cross_domain_ajax
@require_http_methods(['GET'])
def web_engine_get_outputs(request, calc_id, **kwargs):
    return render(request, "engine/get_outputs.html",
                  dict([('calc_id', calc_id)]))


@require_http_methods(['GET'])
def license(request, **kwargs):
    return render(request, "engine/license.html")
