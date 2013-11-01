import StringIO
import json
import logging
import os
import shutil
import tempfile
import urlparse

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openquake import nrmllib
from openquake.engine import engine as oq_engine
from openquake.engine.db import models as oqe_models
from openquake.engine.export import hazard as hazard_export
from openquake.engine.export import risk as risk_export
from xml.etree import ElementTree as etree

from engine import forms
from engine import tasks

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

LOGGER = logging.getLogger('openquakeserver')

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


@cross_domain_ajax
@require_http_methods(['GET'])
def calc_hazard(request):
    """
    Get a list of risk calculations and report their id, status, description,
    and a url where more detailed information can be accessed.

    Responses are in JSON.
    """
    base_url = _get_base_url(request)

    haz_calc_data = _get_haz_calcs()
    if not haz_calc_data:
        return HttpResponseNotFound()

    response_data = []
    for hc_id, status, desc in haz_calc_data:
        url = urlparse.urljoin(base_url, 'v1/calc/hazard/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


@csrf_exempt
# NOTE(LB): Needed in order to use this service in the oq-platform.
# We can probably remove this later if we can properly fix
# authentication.
# See https://bugs.launchpad.net/oq-platform/+bug/1234350
@cross_domain_ajax
@require_http_methods(['GET', 'POST'])
def run_hazard_calc(request):
    """
    Run a calculation.

    A 'GET' will simply return a form for uploading calculation input files.

    A 'POST' (from the form) will load the calculation profile and enqueue
    the calculation job. Once in queue, the view will respond with a summary of
    the calculation, like what is implemented in `/v1/calc/hazard/:calc_id`.
    """
    if request.method == 'GET':
        form = forms.HazardForm()
        return render(
            request,
            'run_calc.html',
            {'post_url': request.build_absolute_uri(), 'form': form}
        )
    else:
        # POST: run a new calculation
        temp_dir = tempfile.mkdtemp()
        files = {}
        # Move each file to a new temp dir, using the upload file names
        # (not the temporary ones).
        for key, each_file in request.FILES.iteritems():
            new_path = os.path.join(temp_dir, each_file.name)
            shutil.move(each_file.temporary_file_path(), new_path)
            files[key] = new_path

        job_file = files.pop('job_config')
        job = oq_engine.haz_job_from_file(
            job_file, request.user.username, DEFAULT_LOG_LEVEL, []
        )
        hc = job.hazard_calculation

        migration_callback_url = request.POST.get('migration_callback_url')
        owner_user = request.POST.get('owner_user')

        base_url = _get_base_url(request)
        tasks.run_hazard_calc.apply_async(
            (hc.id, ),
            dict(migration_callback_url=migration_callback_url,
                 owner_user=owner_user,
                 results_url=urlparse.urljoin(
                     base_url, 'v1/calc/hazard/%s/results' % hc.id
                 ))
        )

        return redirect('/v1/calc/hazard/%s' % hc.id)


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


def _get_haz_calcs():
    """
    Helper function for get job+calculation data from the oq-engine database.

    Gets all hazard calculation records available.
    """
    return oqe_models.OqJob.objects\
        .select_related()\
        .filter(hazard_calculation__isnull=False)\
        .values_list('hazard_calculation',
                     'status',
                     'hazard_calculation__description')


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_hazard_info(request, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    try:
        response_data = _get_haz_calc_info(calc_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


def _get_haz_calc_info(calc_id):
    """
    Helper function to get job info and hazard calculation params from the
    oq-engine DB, as a dictionary.
    """
    job = oqe_models.OqJob.objects\
        .select_related()\
        .get(hazard_calculation=calc_id)

    hc = job.hazard_calculation
    response_data = _calc_to_response_data(hc)

    response_data['status'] = job.status
    return response_data


@cross_domain_ajax
@require_http_methods(['GET'])
def calc_hazard_results(request, calc_id):
    """
    Get a summarized list of hazard calculation results for a given
    ``calc_id``. Result is a JSON array of objects containing the following
    attributes:

        * id
        * name
        * type (hazard_curve, hazard_map, etc.)
        * url (the exact url where the full result can be accessed)
    """
    # If the specified calculation doesn't exist OR is not yet complete,
    # throw back a 404.
    try:
        calc = oqe_models.HazardCalculation.objects.get(id=calc_id)
        if not calc.oqjob.status == 'complete':
            return HttpResponseNotFound()
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    base_url = _get_base_url(request)

    results = oq_engine.get_hazard_outputs(calc_id)
    if not results:
        return HttpResponseNotFound()

    response_data = []
    for result in results:
        url = urlparse.urljoin(base_url,
                               'v1/calc/hazard/result/%d' % result.id)
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
def get_hazard_result(request, result_id):
    """
    Download a specific hazard result, by ``result_id``.

    Parameters for the GET request can include an `export_type`, such as 'xml',
    'geojson', 'csv', etc.
    """
    return _get_result(request, result_id, hazard_export.export)


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_risk(request):
    """
    Get a list of risk calculations and report their id, status, description,
    and a url where more detailed information can be accessed.

    Responses are in JSON.
    """
    base_url = _get_base_url(request)

    risk_calc_data = _get_risk_calcs()
    if not risk_calc_data:
        return HttpResponseNotFound()

    response_data = []
    for hc_id, status, desc in risk_calc_data:
        url = urlparse.urljoin(base_url, 'v1/calc/risk/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


@csrf_exempt
# NOTE(LB): Needed in order to use this service in the oq-platform.
# We can probably remove this later if we can properly fix
# authentication.
# See https://bugs.launchpad.net/oq-platform/+bug/1234350
@cross_domain_ajax
@require_http_methods(['GET', 'POST'])
def run_risk_calc(request):
    """
    Run a calculation.

    Similar to :func:`run_hazard_calc`, except that an additional POST param
    must be included. This param is either the `hazard_calc` or
    `hazard_result`, the value of which must be the corresponding ID.
    """
    if request.method == 'GET':
        form = forms.RiskForm()
        return render(
            request,
            'run_calc.html',
            {'post_url': request.build_absolute_uri(), 'form': form}
        )
    else:
        # POST: run a new calculation
        temp_dir = tempfile.mkdtemp()
        files = {}
        for key, each_file in request.FILES.iteritems():
            new_path = os.path.join(temp_dir, each_file.name)
            shutil.move(each_file.temporary_file_path(), new_path)
            files[key] = new_path

        job_file = files.pop('job_config')
        job = oq_engine.risk_job_from_file(
            job_file, request.user.username, DEFAULT_LOG_LEVEL, [],
            hazard_calculation_id=request.POST.get('hazard_calc'),
            hazard_output_id=request.POST.get('hazard_result'),
        )
        rc = job.risk_calculation

        # Before running the calculation, clean up the temp dir.
        shutil.rmtree(temp_dir)

        migration_callback_url = request.POST.get('migration_callback_url')
        owner_user = request.POST.get('owner_user')

        base_url = _get_base_url(request)
        tasks.run_risk_calc.apply_async(
            (rc.id, ),
            dict(migration_callback_url=migration_callback_url,
                 owner_user=owner_user,
                 results_url=urlparse.urljoin(
                     base_url, 'v1/calc/risk/%s/results' % rc.id
                 ))
        )

        return redirect('/v1/calc/risk/%s' % rc.id)


def _get_risk_calcs():
    """
    Helper function for get job+calculation data from the oq-engine database.

    Gets all risk calculation records available.
    """
    return oqe_models.OqJob.objects\
        .select_related()\
        .filter(risk_calculation__isnull=False)\
        .values_list('risk_calculation',
                     'status',
                     'risk_calculation__description')


@cross_domain_ajax
@require_http_methods(['GET'])
def calc_risk_info(request, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    try:
        response_data = _get_risk_calc_info(calc_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


def _get_risk_calc_info(calc_id):
    """
    Helper function to get job info and hazard calculation params from the
    oq-engine DB, as a dictionary.
    """
    job = oqe_models.OqJob.objects\
        .select_related()\
        .get(risk_calculation=calc_id)

    rc = job.risk_calculation
    response_data = _calc_to_response_data(rc)

    response_data['status'] = job.status
    return response_data


@require_http_methods(['GET'])
@cross_domain_ajax
def calc_risk_results(request, calc_id):
    """
    Get a summarized list of risk calculation results for a given
    ``calc_id``. Result is a JSON array of objects containing the following
    attributes:

        * id
        * name
        * type (hazard_curve, hazard_map, etc.)
        * url (the exact url where the full result can be accessed)
    """
    # If the specified calculation doesn't exist OR is not yet complete,
    # throw back a 404.
    try:
        calc = oqe_models.RiskCalculation.objects.get(id=calc_id)
        if not calc.oqjob.status == 'complete':
            return HttpResponseNotFound()
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    base_url = _get_base_url(request)

    results = oq_engine.get_risk_outputs(calc_id)
    if not results:
        return HttpResponseNotFound()

    response_data = []
    for result in results:
        url = urlparse.urljoin(base_url,
                               'v1/calc/risk/result/%d' % result.id)
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
def get_risk_result(request, result_id):
    """
    Download a specific hazard result, by ``result_id``.

    Parameters for the GET request can include an `export_type`, such as 'xml',
    'geojson', 'csv', etc.
    """
    return _get_result(request, result_id, risk_export.export)


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
