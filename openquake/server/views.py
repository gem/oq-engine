import functools
import StringIO
import json
import logging
import os
import shutil
import tempfile
import urlparse
import sys
import traceback

from xml.etree import ElementTree as etree

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from openquake import nrmllib
from openquake.engine import engine as oq_engine
from openquake.engine.db import models as oqe_models
from openquake.engine.export import hazard as hazard_export
from openquake.engine.export import risk as risk_export

from openquake.server import tasks, executor

METHOD_NOT_ALLOWED = 405
NOT_IMPLEMENTED = 501
JSON = 'application/json'

IGNORE_FIELDS = ('base_path', 'export_dir')
GEOM_FIELDS = ('region', 'sites', 'region_constraint', 'sites_disagg')
RISK_INPUTS = ('hazard_calculation', 'hazard_output')

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


def _calc_to_response_data(calc):
    """
    Extract the calculation parameters into a dictionary.
    """
    fields = [x.name for x in calc._meta.fields if x.name not in IGNORE_FIELDS]
    response_data = {}
    for field_name in fields:
        try:
            value = getattr(calc, field_name)
            if value is not None:
                if field_name in GEOM_FIELDS:
                    response_data[field_name] = json.loads(value.geojson)
                elif field_name in RISK_INPUTS:
                    response_data[field_name] = value.id
                else:
                    response_data[field_name] = value
        except AttributeError:
            # Better that we miss an attribute than crash.
            pass
    return response_data


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


def _prepare_job(request, job_factory, detect_job_file):
    """
    Creates a temporary directory, move uploaded files there and
    create a new oq-engine job by using the `job_factory` callable
    (e.g. oq_engine.job_from_file). The job file is selected using
    the `detect_job_file` callable which accepts in input a list
    holding all the filenames ending with .ini
    """
    temp_dir = tempfile.mkdtemp()

    if len(request.FILES.getlist('job_config')) > 1:
        raw_files = request.FILES.getlist('job_config')
    else:
        raw_files = request.FILES.values()

    files = []
    # Move each file to a new temp dir, using the upload file names
    # (not the temporary ones).
    for each_file in raw_files:
        new_path = os.path.join(temp_dir, each_file.name)
        shutil.move(each_file.temporary_file_path(), new_path)
        files.append(new_path)

    job_file = detect_job_file([f for f in files if f.endswith('.ini')])

    return job_factory(
        job_file, "platform", DEFAULT_LOG_LEVEL, []), temp_dir


def _is_source_model(tempfile):
    """
    Return true if an uploaded NRML file is a seismic source model.
    """
    tree = etree.iterparse(tempfile, events=('start', 'end'))
    # pop off the first elements, which should be a <nrml> element
    # and something else
    _, nrml_elem = tree.next()
    _, model_elem = tree.next()

    assert nrml_elem.tag == '{%s}nrml' % nrmllib.NAMESPACE, (
        "Input file is not a NRML artifact"
    )

    if model_elem.tag == '{%s}sourceModel' % nrmllib.NAMESPACE:
        return True
    return False


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_info(request, job_type, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    try:
        response_data = _get_calc_info(job_type, calc_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


# helper function to get job info and calculation params from the
# oq-engine DB, as a dictionary
def _get_calc_info(job_type, calc_id):
    if job_type == 'hazard':
        job = oqe_models.OqJob.objects\
            .select_related()\
            .get(hazard_calculation=calc_id)
        calc = job.hazard_calculation
    else:  # risk
        job = oqe_models.OqJob.objects\
            .select_related()\
            .get(risk_calculation=calc_id)
        calc = job.risk_calculation

    response_data = _calc_to_response_data(calc)
    response_data['status'] = job.status
    return response_data


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
        url = urlparse.urljoin(base_url, 'v1/calc/%s/%d' % (job_type, hc_id))
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


@csrf_exempt
@cross_domain_ajax
@require_http_methods(['POST'])
def run_calc(request, job_type):
    """
    Run a calculation.

    :param request:
        a `django.http.HttpRequest` object.
    :param job_type:
        string 'hazard' or 'risk'
    """
    callback_url = request.POST.get('callback_url')
    foreign_calc_id = request.POST.get('foreign_calculation_id')

    if request.POST.get('hazard_output_id'):
        hazard_output_id = int(request.POST.get('hazard_output_id'))
        hazard_calculation_id = None
    else:
        hazard_output_id = None
        hazard_calculation_id = request.POST.get('hazard_calculation_id')

    try:
        job, temp_dir = _prepare_job(
            request, functools.partial(
                oq_engine.job_from_file,
                hazard_output_id=hazard_output_id,
                hazard_calculation_id=hazard_calculation_id),
            create_detect_job_file("job.ini", "job_risk.ini"))
    except:  # catch errors in the job_from_file phase
        etype, exc, tb = sys.exc_info()
        einfo = "".join(traceback.format_tb(tb))
        einfo += '%s: %s' % (etype.__name__, exc)
        tasks.update_calculation(callback_url, status="failed", einfo=einfo)
        raise

    calc = job.calculation
    executor.submit(
        tasks.run_calc, job_type, calc.id, temp_dir,
        callback_url=callback_url,
        foreign_calc_id=foreign_calc_id,
        dbname=request.POST['database'])
    try:
        response_data = _get_calc_info(job_type, calc.id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


def _get_calcs(job_type):
    """
    Helper function for get job+calculation data from the oq-engine database.

    Gets all calculation records available.
    """
    if job_type == 'risk':
        return oqe_models.OqJob.objects\
            .select_related()\
            .filter(risk_calculation__isnull=False)\
            .values_list('risk_calculation',
                         'status',
                         'risk_calculation__description')
    else:
        return oqe_models.OqJob.objects\
            .select_related()\
            .filter(hazard_calculation__isnull=False)\
            .values_list('hazard_calculation',
                         'status',
                         'hazard_calculation__description')


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_results(request, job_type, calc_id):
    """
    Get a summarized list of calculation results for a given ``calc_id``.
    Result is a JSON array of objects containing the following attributes:

        * id
        * name
        * type (hazard_curve, hazard_map, etc.)
        * url (the exact url where the full result can be accessed)
    """
    calc_class = oqe_models.RiskCalculation if job_type == 'risk' \
        else oqe_models.HazardCalculation
    # If the specified calculation doesn't exist OR is not yet complete,
    # throw back a 404.
    try:
        calc = calc_class.objects.get(id=calc_id)
        if not calc.oqjob.status == 'complete':
            return HttpResponseNotFound()
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    base_url = _get_base_url(request)

    results = oq_engine.get_outputs(job_type, calc_id)
    if not results:
        return HttpResponseNotFound()

    response_data = []
    for result in results:
        url = urlparse.urljoin(base_url,
                               'v1/calc/%s/result/%d' % (job_type, result.id))
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
def get_result(request, job_type, result_id):
    """
    Download a specific result, by ``result_id``.

    Parameters for the GET request can include an `export_type`, such as 'xml',
    'geojson', 'csv', etc.
    """
    return _get_result(
        request, result_id,
        risk_export.export if job_type == 'risk' else hazard_export.export)


def _get_result(request, result_id, export_fn):
    """
    The common abstracted functionality for getting hazard or risk results.
    The functionality is the same, except for the hazard/risk specific
    ``export_fn``.

    :param request:
        `django.http.HttpRequest` object. Can contain a `export_type` GET
        param (the default is 'xml' if no param is specified).
    :param result_id:
        The id of the requested artifact.
    :param export_fn:
        Export function, which accepts the following params:

            * result_id (int)
            * target (a file path or file-like)
            * export_type (option kwarg)

    :returns:
        If the requested ``result_id`` is not available in the format
        designated by the `export_type`.

        Otherwise, return a `django.http.HttpResponse` containing the content
        of the requested artifact.
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

    export_type = request.GET.get('export_type', DEFAULT_EXPORT_TYPE)

    content = StringIO.StringIO()
    try:
        content = export_fn(result_id, content, export_type=export_type)
    except NotImplementedError, err:
        # Throw back a 404 if the exact export parameters are not supported
        return HttpResponseNotFound(err.message)

    # Just in case the original StringIO object was closed:
    resp_content = StringIO.StringIO()
    # NOTE(LB): We assume that `content` was written to by using normal
    # file-like `write` calls; thus, the buflist should be populated with all
    # of the content. The exporter/writer might have closed the file object (if
    # so, we cannot read from it normally) so instead we should look at the
    # buflist.
    # NOTE(LB): This might be a really stupid implementation, but it's the best
    # I could come up with so far.
    resp_content.writelines(content.buflist)
    del content

    # TODO(LB): A possible necessary optimization--in the future--would be to
    # iteratively stream large files.
    # TODO(LB): Large files could pose a memory consumption problem.
    # TODO(LB): We also may want to limit the maximum file size of results sent
    # via http.
    resp_value = resp_content.getvalue()
    resp_content.close()
    # TODO: Need to look at `content_type`, otherwise XML gets treated at HTML
    # in the browser
    content_type = EXPORT_CONTENT_TYPE_MAP.get(export_type,
                                               DEFAULT_CONTENT_TYPE)
    return HttpResponse(resp_value, content_type=content_type)
