import zipfile
import shutil
import json
import logging
import os
import tempfile
import urlparse

from xml.etree import ElementTree as etree

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from openquake.commonlib import nrml
from openquake.engine import engine as oq_engine, __version__ as oqversion
from openquake.engine.db import models as oqe_models
from openquake.engine.export import core
from openquake.engine.utils.tasks import safely_call
from openquake.server import tasks, executor

METHOD_NOT_ALLOWED = 405
NOT_IMPLEMENTED = 501
JSON = 'application/json'

DEFAULT_LOG_LEVEL = 'progress'

#: For exporting calculation outputs, the client can request a specific format
#: (xml, geojson, csv, etc.). If the client does not specify give them (NRML)
#: XML by default.
DEFAULT_EXPORT_TYPE = 'xml'

EXPORT_CONTENT_TYPE_MAP = dict(xml='application/xml',
                               geojson='application/json')
DEFAULT_CONTENT_TYPE = 'text/plain'

LOGGER = logging.getLogger('openquake.server')

ACCESS_HEADERS = {'Access-Control-Allow-Origin': '*',
                  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                  'Access-Control-Max-Age': 1000,
                  'Access-Control-Allow-Headers': '*'}


# Credit for this decorator to https://gist.github.com/aschem/1308865.
def cross_domain_ajax(func):
    def wrap(request, *args, **kwargs):
        # Firefox sends 'OPTIONS' request for cross-domain javascript call.
        if not request.method == "OPTIONS":
            response = func(request, *args, **kwargs)
        else:
            response = HttpResponse()
        for k, v in ACCESS_HEADERS.iteritems():
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


def create_detect_job_file(*candidates):
    def detect_job_file(files):
        for candidate in candidates:
            try:
                file_idx = [os.path.basename(f)
                            for f in files].index(candidate)
                return files[file_idx]
            except ValueError:
                pass
        raise RuntimeError("No job file found in %s for %s" % (
            str(files), str(candidates)))
    return detect_job_file


def _prepare_job(request, hazard_output_id, hazard_job_id,
                 detect_job_file):
    """
    Creates a temporary directory, move uploaded files there and
    select the job file by using the `detect_job_file` callable which
    accepts in input a list holding all the filenames ending with .ini

    :returns: job_file and temp_dir
    """
    temp_dir = tempfile.mkdtemp()
    files = []

    try:
        archive = zipfile.ZipFile(request.FILES['archive'])
    except KeyError:
        # move each file to a new temp dir, using the upload file names,
        # not the temporary ones
        for each_file in request.FILES.values():
            new_path = os.path.join(temp_dir, each_file.name)
            shutil.move(each_file.temporary_file_path(), new_path)
            files.append(new_path)
    else:  # extract the files from the archive into temp_dir
        archive.extractall(temp_dir)
        archive.close()
        for fname in os.listdir(temp_dir):
            files.append(os.path.join(temp_dir, fname))
    job_file = detect_job_file([f for f in files if f.endswith('.ini')])
    return job_file, temp_dir


def _is_source_model(tempfile):
    """
    Return true if an uploaded NRML file is a seismic source model.
    """
    tree = etree.iterparse(tempfile, events=('start', 'end'))
    # pop off the first elements, which should be a <nrml> element
    # and something else
    _, nrml_elem = tree.next()
    _, model_elem = tree.next()

    assert nrml_elem.tag == '{%s}nrml' % nrml.NAMESPACE, (
        "Input file is not a NRML artifact"
    )

    if model_elem.tag == '{%s}sourceModel' % nrml.NAMESPACE:
        return True
    return False


@cross_domain_ajax
@require_http_methods(['GET'])
def get_engine_version(request):
    """
    Return a string with the openquake.engine version
    """
    return HttpResponse(oqversion)


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_info(request, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    try:
        calc = oqe_models.OqJob.objects.get(pk=calc_id)
        response_data = vars(calc.get_oqparam())
        response_data['status'] = calc.status
        response_data['start_time'] = str(calc.jobstats.start_time)
        response_data['stop_time'] = str(calc.jobstats.stop_time)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


@require_http_methods(['GET'])
@cross_domain_ajax
def calc(request, job_type):
    """
    Get a list of calculations and report their id, status, description,
    and a url where more detailed information can be accessed.

    Responses are in JSON.
    """
    base_url = _get_base_url(request)

    calc_data = _get_calcs(job_type)
    if not calc_data:
        return HttpResponseNotFound()

    response_data = []
    for hc_id, status, desc in calc_data:
        url = urlparse.urljoin(base_url, 'v1/calc/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def run_calc(request):
    """
    Run a calculation.

    :param request:
        a `django.http.HttpRequest` object.
    """
    callback_url = request.POST.get('callback_url')
    foreign_calc_id = request.POST.get('foreign_calculation_id')

    hazard_output_id = request.POST.get('hazard_output_id')
    hazard_job_id = request.POST.get('hazard_job_id')

    is_risk = hazard_output_id or hazard_job_id
    if is_risk:
        detect_job_file = create_detect_job_file("job_risk.ini", "job.ini")
    else:
        detect_job_file = create_detect_job_file("job_hazard.ini", "job.ini")
    einfo, exctype = safely_call(
        _prepare_job, (request, hazard_output_id, hazard_job_id,
                       detect_job_file))
    if exctype:
        tasks.update_calculation(callback_url, status="failed", einfo=einfo)
        raise exctype(einfo)
    else:
        job_file, temp_dir = einfo
    job, _fut = submit_job(job_file, temp_dir, request.POST['database'],
                           callback_url, foreign_calc_id,
                           hazard_output_id, hazard_job_id)
    try:
        calc = oqe_models.OqJob.objects.get(pk=job.id)
        response_data = vars(calc.get_oqparam())
        response_data['status'] = calc.status
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


def submit_job(job_file, temp_dir, dbname,
               callback_url=None, foreign_calc_id=None,
               hazard_output_id=None, hazard_job_id=None,
               logfile=None):
    """
    Create a job object from the given job.ini file in the job directory
    and submit it to the job queue.
    """
    job, exctype = safely_call(
        oq_engine.job_from_file, (job_file, "platform", DEFAULT_LOG_LEVEL, '',
                                  hazard_output_id, hazard_job_id))
    if exctype:
        tasks.update_calculation(callback_url, status="failed", einfo=job)
        raise exctype(job)

    future = executor.submit(
        tasks.safely_call, tasks.run_calc, job.id, temp_dir,
        callback_url, foreign_calc_id, dbname, logfile)
    return job, future


def _get_calcs(job_type):
    """
    Helper function for get job+calculation data from the oq-engine database.

    Gets all calculation records available.
    """
    job_params = oqe_models.JobParam.objects.filter(
        name='description', job__user_name='platform',
        job__hazard_calculation__isnull=job_type == 'hazard')
    return [(jp.job.id, jp.job.status, jp.value) for jp in job_params]


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
        oqjob = oqe_models.OqJob.objects.get(id=calc_id)
        if not oqjob.status == 'complete':
            return HttpResponseNotFound()
    except ObjectDoesNotExist:
        return HttpResponseNotFound()
    base_url = _get_base_url(request)

    results = oq_engine.get_outputs(calc_id)
    if not results:
        return HttpResponseNotFound()

    response_data = []
    for result in results:
        url = urlparse.urljoin(base_url, 'v1/calc/result/%d' % result.id)
        datum = dict(
            id=result.id,
            name=result.display_name,
            type=result.output_type,
            url=url,
        )
        response_data.append(datum)

    return HttpResponse(content=json.dumps(response_data))


@cross_domain_ajax
@require_http_methods(['GET'])
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
        output = oqe_models.Output.objects.get(id=result_id)
        job = output.oq_job
        if not job.status == 'complete':
            return HttpResponseNotFound()
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    etype = request.GET.get('export_type')
    export_type = etype or DEFAULT_EXPORT_TYPE

    tmpdir = tempfile.mkdtemp()
    exported = core.export(result_id, tmpdir, export_type=export_type)
    if exported is None:
        # Throw back a 404 if the exact export parameters are not supported
        return HttpResponseNotFound(
            'export_type=%s is not supported for output_type=%s' %
            (export_type, output.output_type))

    content_type = EXPORT_CONTENT_TYPE_MAP.get(
        export_type, DEFAULT_CONTENT_TYPE)
    try:
        fname = 'output-%s-%s' % (result_id, os.path.basename(exported))
        data = open(exported).read()
        response = HttpResponse(data, content_type=content_type)
        response['Content-Length'] = len(data)
        if etype:  # download as a file
            response['Content-Disposition'] = 'attachment; filename=%s' % fname
        return response
    finally:
        shutil.rmtree(tmpdir)
