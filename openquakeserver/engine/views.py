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

IGNORE_FIELDS = ('base_path', 'export_dir', 'owner')
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


# csrf_excempt so we post to the view without necessarily having a form
@csrf_exempt
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
            {'post_url': request.path, 'form': form}
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

        # We need to explicitly load all source model input files before the
        # calculation is run. They need to be stored in the database (not on
        # the filesystem) before we start the job. Otherwise, the calculation
        # will attempt to load these models "too late" from the filesystem,
        # at which point we will fail since each calculation is run by a remote
        # worker which does not necessarily have access to the same file
        # system.
        # See :func:`_load_source_models` for more details.
        _load_source_models(sorted(files.values()), job.owner, hc.id)

        # Before running the calculation, clean up the temp dir.
        shutil.rmtree(temp_dir)
        tasks.run_hazard_calc.apply_async((hc.id, ))

        return redirect('/v1/calc/hazard/%s' % hc.id)


def _load_source_models(files, owner, hc_id):
    """
    Given a list of file paths to any type of hazard input models, check if
    they are source models (which are soft-linked in a source model logic tree,
    and will otherwise get missed when a calculation profile is loaded) and if
    they are, load them into the oq-engine DB and link them to the calculation
    profile given by ``hc_id``.

    :param list files:
        List of input model file paths.
    :param owner:
        Owner DB record object. See :class:`openquake.engine.db.models.OqUser`.
    :param int hc_id:
        Hazard calculation ID.
    """
    for input_model in files:
        # Check if it is a source model.
        if _is_source_model(open(input_model, 'r')):
            # Load it into the DB.
            oq_engine.get_or_create_input(
                input_model,
                'source',
                owner,
                haz_calc_id=hc_id,
            )


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


@require_http_methods(['GET'])
def get_hazard_result(request, result_id):
    """
    Download a specific hazard result, by ``result_id``.

    Parameters for the GET request can include an `export_type`, such as 'xml',
    'geojson', 'csv', etc.
    """
    return _get_result(request, result_id, hazard_export.export)


@require_http_methods(['GET'])
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
            {'post_url': request.path, 'form': form}
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
        tasks.run_risk_calc.apply_async((rc.id, ))

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
    export_type = request.GET.get('export_type', DEFAULT_EXPORT_TYPE)

    content = StringIO.StringIO()
    try:
        content = export_fn(result_id, content, export_type=export_type)
    except NotImplementedError, err:
        # Throw back a 404 if the exact export parameters are not supported
        return HttpResponseNotFound(err.message)

    # Just in case the original StringIO object was closed:
    resp_content = StringIO.StringIO()
    resp_content.writelines(content.buflist)
    del content

    # TODO(LB): A possible necessary optimization--in the future--would be to
    # iteratively stream large files.
    # TODO(LB): Large files could pose a memory consumption problem.
    resp_value = resp_content.getvalue()
    resp_content.close()
    # TODO: Need to look at `content_type`, otherwise XML gets treated at HTML
    # in the browser
    content_type = EXPORT_CONTENT_TYPE_MAP.get(export_type,
                                               DEFAULT_CONTENT_TYPE)
    return HttpResponse(resp_value, content_type=content_type)
