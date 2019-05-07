# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import sys
import tempfile
import subprocess
import threading
import traceback
import signal
import zlib
import pickle
import urllib.parse as urlparse
import re
import numpy
import psutil
from urllib.parse import unquote_plus
from xml.parsers.expat import ExpatError
from django.http import (
    HttpResponse, HttpResponseNotFound, HttpResponseBadRequest,
    HttpResponseForbidden)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

from openquake.baselib import datastore
from openquake.baselib.general import groupby, gettemp, zipfiles
from openquake.baselib.parallel import safely_call
from openquake.hazardlib import nrml, gsim

from openquake.commonlib import readinput, oqvalidation, logs
from openquake.calculators.export import export
from openquake.calculators.extract import extract as _extract
from openquake.engine import __version__ as oqversion
from openquake.engine.export import core
from openquake.engine import engine
from openquake.engine.export.core import DataStoreExportError
from openquake.server import utils, dbapi

from django.conf import settings
from django.http import FileResponse
from wsgiref.util import FileWrapper

if settings.LOCKDOWN:
    from django.contrib.auth import authenticate, login, logout


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
    calc_data = logs.dbcmd('get_calcs', request.GET,
                           utils.get_valid_users(request),
                           utils.get_acl_on(request), id)

    response_data = []
    username = psutil.Process(os.getpid()).username()
    for (hc_id, owner, status, calculation_mode, is_running, desc, pid,
         parent_id, size_mb) in calc_data:
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

    if not utils.user_has_permission(request, job.user_name):
        message = {'error': ('User %s has no permission to abort job %s' %
                             (job.user_name, job.id))}
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
    hazard_job_id = request.POST.get('hazard_job_id')

    if hazard_job_id:
        hazard_job_id = int(hazard_job_id)
        candidates = ("job_risk.ini", "job.ini")
    else:
        candidates = ("job_hazard.ini", "job_haz.ini", "job.ini")
    result = safely_call(_prepare_job, (request, candidates))
    if result.tb_str:
        return HttpResponse(json.dumps(result.tb_str.splitlines()),
                            content_type=JSON, status=500)
    inifiles = result.get()
    if not inifiles:
        msg = 'Could not find any file of the form %s' % str(candidates)
        logging.error(msg)
        return HttpResponse(content=json.dumps([msg]), content_type=JSON,
                            status=500)

    user = utils.get_user(request)
    try:
        job_id, pid = submit_job(inifiles[0], user, hazard_job_id)
    except Exception as exc:  # no job created, for instance missing .xml file
        # get the exception message
        exc_msg = str(exc)
        logging.error(exc_msg)
        response_data = exc_msg.splitlines()
        status = 500
    else:
        response_data = dict(job_id=job_id, status='created', pid=pid)
        status = 200
    return HttpResponse(content=json.dumps(response_data), content_type=JSON,
                        status=status)


RUNCALC = '''\
import os, sys, pickle
from openquake.commonlib import logs
from openquake.engine import engine
if __name__ == '__main__':
    oqparam = pickle.loads(%(pik)r)
    logs.init(%(job_id)s)
    with logs.handle(%(job_id)s):
        engine.run_calc(
            %(job_id)s, oqparam, '', %(hazard_job_id)s,
           username='%(username)s')
    os.remove(__file__)
'''


def submit_job(job_ini, username, hazard_job_id=None):
    """
    Create a job object from the given job.ini file in the job directory
    and run it in a new process. Returns the job ID and PID.
    """
    job_id = logs.init('job')
    oq = engine.job_from_file(
        job_ini, job_id, username, hazard_calculation_id=hazard_job_id)
    pik = pickle.dumps(oq, protocol=0)  # human readable protocol
    code = RUNCALC % dict(job_id=job_id, hazard_job_id=hazard_job_id, pik=pik,
                          username=username)
    tmp_py = gettemp(code, suffix='.py')
    # print(code, tmp_py)  # useful when debugging
    devnull = subprocess.DEVNULL
    popen = subprocess.Popen([sys.executable, tmp_py],
                             stdin=devnull, stdout=devnull, stderr=devnull)
    threading.Thread(target=popen.wait).start()
    logs.dbcmd('update_job', job_id, {'pid': popen.pid})
    return job_id, popen.pid


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

    try:
        # read the data and save them on a temporary .npz file
        with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
            fd, fname = tempfile.mkstemp(
                prefix=what.replace('/', '-'), suffix='.npz')
            os.close(fd)
            n = len(request.path_info)
            query_string = unquote_plus(request.get_full_path()[n:])
            aw = _extract(ds, what + query_string)
            a = {}
            for key, val in vars(aw).items():
                key = str(key)  # can be a numpy.bytes_
                if isinstance(val, str):
                    # without this oq extract would fail
                    a[key] = numpy.array(val.encode('utf-8'))
                elif isinstance(val, dict):
                    # this is hack: we are losing the values
                    a[key] = list(val)
                else:
                    a[key] = val
            numpy.savez_compressed(fname, **a)
    except Exception as exc:
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        return HttpResponse(
            content='%s: %s\n%s' % (exc.__class__.__name__, exc, tb),
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
    if job is None:
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


@cross_domain_ajax
@require_http_methods(['GET'])
def calc_oqparam(request, job_id):
    """
    Return the calculation parameters as a JSON
    """
    job = logs.dbcmd('get_job', int(job_id))
    if job is None:
        return HttpResponseNotFound()
    if not utils.user_has_permission(request, job.user_name):
        return HttpResponseForbidden()

    with datastore.read(job.ds_calc_dir + '.hdf5') as ds:
        oq = ds['oqparam']
    return HttpResponse(content=json.dumps(vars(oq)), content_type=JSON)


def web_engine(request, **kwargs):
    return render(request, "engine/index.html",
                  dict())


@cross_domain_ajax
@require_http_methods(['GET'])
def web_engine_get_outputs(request, calc_id, **kwargs):
    job = logs.dbcmd('get_job', calc_id)
    size_mb = '?' if job.size_mb is None else '%.2f' % job.size_mb
    return render(request, "engine/get_outputs.html",
                  dict(calc_id=calc_id, size_mb=size_mb))


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
