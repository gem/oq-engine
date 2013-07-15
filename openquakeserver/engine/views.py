import json
import logging
import os
import urlparse

from django.http import HttpResponse
from django.conf import settings

from openquake.engine.db import models as oqe_models
from openquake.engine import settings as oqe_settings

METHOD_NOT_ALLOWED = 405
JSON = 'application/json'

IGNORE_FIELDS = ('base_path', 'export_dir', 'owner')
GEOM_FIELDS = ('region', 'sites', 'region_constraint', 'sites_disagg')

LOGGER = logging.getLogger('openquakeserver')


def calc_hazard(request):
    """
    The following request types are supported:

        * GET: List hazard calculations.

    Responses are in JSON.
    """
    if not request.method == 'GET':
        return HttpResponse(status=METHOD_NOT_ALLOWED)

    base_url = 'http://%s' % request.META['HTTP_HOST']

    haz_calc_data = _get_haz_calcs()

    response_data = []
    for hc_id, status, desc in haz_calc_data:
        url = urlparse.urljoin(base_url, 'calc/hazard/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


def _get_haz_calcs():
    return oqe_models.OqJob.objects\
        .select_related()\
        .filter(hazard_calculation__isnull=False)\
        .values_list('hazard_calculation',
                     'status',
                     'hazard_calculation__description')


def calc_hazard_info(request, calc_id):
    raise NotImplementedError


def calc_risk(request):
    """
    The following request types are supported:

        * GET: List risk calculations.

    Responses are in JSON.
    """
    if not request.method == 'GET':
        return HttpResponse(status=METHOD_NOT_ALLOWED)

    base_url = 'http://%s' % request.META['HTTP_HOST']

    risk_calc_data = _get_risk_calcs()

    response_data = []
    for hc_id, status, desc in risk_calc_data:
        url = urlparse.urljoin(base_url, 'calc/risk/%d' % hc_id)
        response_data.append(
            dict(id=hc_id, status=status, description=desc, url=url)
        )

    return HttpResponse(content=json.dumps(response_data),
                        content_type=JSON)


def _get_risk_calcs():
    return oqe_models.OqJob.objects\
        .select_related()\
        .filter(risk_calculation__isnull=False)\
        .values_list('risk_calculation',
                     'status',
                     'risk_calculation__description')


def calc_risk_info(request, calc_id):
    raise NotImplementedError
