import StringIO
import json
import logging
import urlparse

from django.http import HttpResponse
from openquake.engine import engine as oq_engine
from openquake.engine.db import models as oqe_models
from openquake.engine.export import hazard as hazard_export
from openquake.engine.export import risk as risk_export

METHOD_NOT_ALLOWED = 405
NOT_IMPLEMENTED = 501
JSON = 'application/json'

IGNORE_FIELDS = ('base_path', 'export_dir', 'owner')
GEOM_FIELDS = ('region', 'sites', 'region_constraint', 'sites_disagg')
RISK_INPUTS = ('hazard_calculation', 'hazard_output')

#: For exporting calculation outputs, the client can request a specific format
#: (xml, geojson, csv, etc.). If the client does not specify give them (NRML)
#: XML by default.
DEFAULT_EXPORT_TYPE = 'xml'

LOGGER = logging.getLogger('openquakeserver')


class allowed_methods(object):
    """
    Use as a view decorator to strictly enforce HTTP request types.

    It works like this:

    .. code-block:: python

        @allowed_methods(('GET', 'POST'))
        def some_view(request):
            # code goes here

        @ allowed_methods(('DELETE', ))
        def some_other_view(request):
            # code goes here
    """

    def __init__(self, methods):
        self.methods = methods

    def __call__(self, func):
        def wrapped(request, *args, **kwargs):
            if not request.method in self.methods:
                return HttpResponse(status=METHOD_NOT_ALLOWED)
            else:
                return func(request, *args, **kwargs)
        return wrapped


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


@allowed_methods(('GET', ))
def calc_hazard(request):
    """
    Get a list of risk calculations and report their id, status, description,
    and a url where more detailed information can be accessed.

    Responses are in JSON.
    """
    base_url = _get_base_url(request)

    haz_calc_data = _get_haz_calcs()

    response_data = []
    for hc_id, status, desc in haz_calc_data:
        url = urlparse.urljoin(base_url, 'v1/calc/hazard/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


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


@allowed_methods(('GET', ))
def calc_hazard_info(request, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    response_data = _get_haz_calc_info(calc_id)

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


@allowed_methods(('GET', ))
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


@allowed_methods(('GET', ))
def get_hazard_result(request, result_id):
    """
    Download a specific hazard result, by ``result_id``.

    Parameters for the GET request can include an `export_type`, such as 'xml',
    'geojson', 'csv', etc.
    """
    return _get_result(request, result_id, hazard_export.export)


@allowed_methods(('GET', ))
def calc_risk(request):
    """
    Get a list of risk calculations and report their id, status, description,
    and a url where more detailed information can be accessed.

    Responses are in JSON.
    """
    base_url = _get_base_url(request)

    risk_calc_data = _get_risk_calcs()

    response_data = []
    for hc_id, status, desc in risk_calc_data:
        url = urlparse.urljoin(base_url, 'v1/calc/risk/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


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


@allowed_methods(('GET', ))
def calc_risk_info(request, calc_id):
    """
    Get a JSON blob containing all of parameters for the given calculation
    (specified by ``calc_id``). Also includes the current job status (
    executing, complete, etc.).
    """
    response_data = _get_risk_calc_info(calc_id)

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


@allowed_methods(('GET', ))
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


@allowed_methods(('GET', ))
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
        # Throw back a 501 if the exact export parameters are not supported
        return HttpResponse(err.message, status=NOT_IMPLEMENTED)

    # Just in case the original StringIO object was closed:
    resp_content = StringIO.StringIO()
    resp_content.writelines(content.buflist)
    del content

    # TODO(LB): A possible necessary optimization--in the future--would be to
    # iteratively stream large files.
    # TODO(LB): Large files could pose a memory consumption problem.
    resp_value = resp_content.getvalue()
    resp_content.close()
    return HttpResponse(resp_value)
