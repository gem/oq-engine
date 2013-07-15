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
GEOM_FIELDS = ('region', 'sites')

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
    if not request.method == 'GET':
        return HttpResponse(status=METHOD_NOT_ALLOWED)

    response_data = _get_haz_calc_info(calc_id)

    return HttpResponse(content=json.dumps(response_data), content_type=JSON)


def _get_haz_calc_info(calc_id):
    job = oqe_models.OqJob.objects\
        .select_related()\
        .get(hazard_calculation=calc_id)

    hc = job.hazard_calculation
    fields = [x.name for x in hc._meta.fields if x.name not in IGNORE_FIELDS]
    response_data = {}
    for field_name in fields:
        try:
            value = getattr(hc, field_name)
            if value is not None:
                # TODO: special handling for geometry
                # convert it to geojson or wkt?
                if field_name in GEOM_FIELDS:
                    response_data[field_name] = json.loads(value.geojson)
                else:
                    response_data[field_name] = value
        except AttributeError:
            # Better that we miss an attribute than crash.
            pass

    response_data['status'] = job.status
    return response_data


def calc_risk(request):
    raise NotImplementedError


def calc_risk_info(request, calc_id):
    raise NotImplementedError
