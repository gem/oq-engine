# -*- coding: utf-8 -*-
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Post processing functionality for the classical PSHA hazard calculator.
E.g. mean and quantile curves.
"""

import numpy

from django.db import transaction
from itertools import izip

from openquake.engine import logs
from openquake.engine.calculators.hazard.general import CURVE_CACHE_SIZE
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.writer import CacheInserter


# Number of locations considered by each task
DEFAULT_LOCATIONS_PER_TASK = 1000


def compute_hazard_maps(curves, imls, poes):
    """
    Given a set of hazard curve poes, interpolate a hazard map at the specified
    ``poe``.

    :param curves:
        2D array of floats. Each row represents a curve, where the values
        in the row are the PoEs (Probabilities of Exceedance) corresponding to
        ``imls``. Each curve corresponds to a geographical location.
    :param imls:
        Intensity Measure Levels associated with these hazard ``curves``. Type
        should be an array-like of floats.
    :param float poes:
        Value(s) on which to interpolate a hazard map from the input
        ``curves``. Can be an array-like or scalar value (for a single PoE).

    :returns:
        A 2D numpy array of hazard map data. Each element/row in the resulting
        array represents the interpolated map for each ``poes`` value
        specified. If ``poes`` is just a single scalar value, the result array
        will have a length of 1.

        The results are structure this way so it is easy to iterate over the
        hazard map results, and in a consistent way (no matter how many
        ``poes`` values are specified).
    """
    poes = numpy.array(poes)

    if len(poes.shape) == 0:
        # ``poes`` was passed in as a scalar;
        # convert it to 1D array of 1 element
        poes = poes.reshape(1)

    result = []
    imls = numpy.array(imls[::-1])

    for curve in curves:
        hmap_val = numpy.interp(poes, curve[::-1], imls)
        result.append(hmap_val)

    return numpy.array(result).transpose()


_HAZ_MAP_DISP_NAME_MEAN_FMT = 'hazard-map(%(poe)s)-%(imt)s-mean'
_HAZ_MAP_DISP_NAME_QUANTILE_FMT = (
    'hazard-map(%(poe)s)-%(imt)s-quantile(%(quantile)s)')
# Hazard maps for a specific end branch
_HAZ_MAP_DISP_NAME_FMT = 'hazard-map(%(poe)s)-%(imt)s-rlz-%(rlz)s'

_UHS_DISP_NAME_MEAN_FMT = 'uhs-(%(poe)s)-mean'
_UHS_DISP_NAME_QUANTILE_FMT = 'uhs-(%(poe)s)-quantile(%(quantile)s)'
_UHS_DISP_NAME_FMT = 'uhs-(%(poe)s)-rlz-%(rlz)s'


# Silencing 'Too many local variables'
# pylint: disable=R0914
def hazard_curves_to_hazard_map(job_id, hazard_curve_id, poes):
    """
    Function to process a set of hazard curves into 1 hazard map for each PoE
    in ``poes``.

    Hazard map results are written directly to the database.

    :param int job_id:
        ID of the current :class:`openquake.engine.db.models.OqJob`.
    :param int hazard_curve_id:
        ID of a set of
        :class:`hazard curves <openquake.engine.db.models.HazardCurve>`.
    :param list poes:
        List of PoEs for which we want to iterpolate hazard maps.
    """
    job = models.OqJob.objects.get(id=job_id)
    hc = models.HazardCurve.objects.get(id=hazard_curve_id)

    hcd = models.HazardCurveData.objects.all_curves_simple(
        filter_args=dict(hazard_curve=hc.id), order_by='location'
    )
    hcd = list(hcd)

    imt = hc.imt
    if imt == 'SA':
        # if it's SA, include the period using the standard notation
        imt = 'SA(%s)' % hc.sa_period

    # Gather all of the curves and compute the maps, for all PoEs
    curves = (poes for _, _, poes in hcd)
    hazard_maps = compute_hazard_maps(curves, hc.imls, poes)

    # Prepare the maps to be saved to the DB
    for i, poe in enumerate(poes):
        map_values = hazard_maps[i]
        lons = numpy.empty(map_values.shape)
        lats = numpy.empty(map_values.shape)

        for loc_idx, _ in enumerate(map_values):
            lons[loc_idx] = hcd[loc_idx][0]
            lats[loc_idx] = hcd[loc_idx][1]

        # Create 'Output' records for the map for this PoE
        if hc.statistics == 'mean':
            disp_name = _HAZ_MAP_DISP_NAME_MEAN_FMT % dict(poe=poe, imt=imt)
        elif hc.statistics == 'quantile':
            disp_name = _HAZ_MAP_DISP_NAME_QUANTILE_FMT % dict(
                poe=poe, imt=imt, quantile=hc.quantile)
        else:
            disp_name = _HAZ_MAP_DISP_NAME_FMT % dict(
                poe=poe, imt=imt, rlz=hc.lt_realization.id)

        output = models.Output.objects.create_output(
            job, disp_name, 'hazard_map'
        )
        # Save the complete hazard map
        models.HazardMap.objects.create(
            output=output,
            lt_realization=hc.lt_realization,
            investigation_time=hc.investigation_time,
            imt=hc.imt,
            statistics=hc.statistics,
            quantile=hc.quantile,
            sa_period=hc.sa_period,
            sa_damping=hc.sa_damping,
            poe=poe,
            lons=lons,
            lats=lats,
            imls=map_values,
        )

hazard_curves_to_hazard_map_task = tasks.oqtask(hazard_curves_to_hazard_map)


def hazard_curves_to_hazard_map_task_arg_gen(job):
    """
    Yield task arguments for processing hazard curves into hazard maps.

    :param job:
        A :class:`openquake.engine.db.models.OqJob` which has some hazard
        curves associated with it.
    """
    poes = job.hazard_calculation.poes

    hazard_curve_ids = models.HazardCurve.objects.filter(
        output__oq_job=job, imt__isnull=False).values_list('id', flat=True)
    logs.LOG.debug('num haz curves: %d', len(hazard_curve_ids))

    for hazard_curve_id in hazard_curve_ids:
        yield job.id, hazard_curve_id, poes


def do_uhs_post_proc(job):
    """
    Compute and save (to the DB) Uniform Hazard Spectra for all hazard maps for
    the given ``job``.

    :param job:
        Instance of :class:`openquake.engine.db.models.OqJob`.
    """
    hc = job.hazard_calculation

    rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)

    for poe in hc.poes:
        maps_for_poe = models.HazardMap.objects.filter(
            output__oq_job=job, poe=poe
        )

        # mean (if defined)
        mean_maps = maps_for_poe.filter(statistics='mean')
        if mean_maps.count() > 0:
            mean_uhs = make_uhs(mean_maps)
            _save_uhs(job, mean_uhs, poe, statistics='mean')

        # quantiles (if defined)
        for quantile in hc.quantile_hazard_curves:
            quantile_maps = maps_for_poe.filter(
                statistics='quantile', quantile=quantile
            )
            quantile_uhs = make_uhs(quantile_maps)
            _save_uhs(job, quantile_uhs, poe, statistics='quantile',
                      quantile=quantile)

        # for each logic tree branch:
        for rlz in rlzs:
            rlz_maps = maps_for_poe.filter(
                statistics=None, lt_realization=rlz
            )
            rlz_uhs = make_uhs(rlz_maps)
            _save_uhs(job, rlz_uhs, poe, rlz=rlz)


def make_uhs(maps):
    """
    Make Uniform Hazard Spectra curves for each location.

    It is assumed that the `lons` and `lats` for each of the ``maps`` are
    uniform.

    :param maps:
        A sequence of :class:`openquake.engine.db.models.HazardMap` objects, or
        equivalent objects with the same fields attributes.
    :returns:
        A `dict` with two values::
            * periods: a list of the SA periods from all of the ``maps``,
              sorted ascendingly
            * uh_spectra: a list of triples (lon, lat, imls), where `imls`
              is a `tuple` of the IMLs from all maps for each of the `periods`
    """
    result = dict()
    result['periods'] = []

    # filter out non-PGA -SA maps
    maps = [x for x in maps if x.imt in ('PGA', 'SA')]

    # give PGA maps an sa_period of 0.0
    # this is slightly hackish, but makes the sorting simple
    for each_map in maps:
        if each_map.imt == 'PGA':
            each_map.sa_period = 0.0

    # sort the maps by period:
    sorted_maps = sorted(maps, key=lambda m: m.sa_period)

    # start constructing the results:
    result['periods'] = [x.sa_period for x in sorted_maps]

    # assume the `lons` and `lats` are uniform for all maps
    lons = sorted_maps[0].lons
    lats = sorted_maps[0].lats

    result['uh_spectra'] = []
    imls_list = izip(*(x.imls for x in sorted_maps))
    for lon, lat, imls in izip(lons, lats, imls_list):
        result['uh_spectra'].append((lon, lat, imls))

    return result


def _save_uhs(job, uhs_results, poe, rlz=None, statistics=None, quantile=None):
    """
    Save computed UHS data to the DB.

    UHS results can be either for an end branch or for mean or quantile
    statistics.

    :param job:
        :class:`openquake.engine.db.models.OqJob` instance to be associated
        with the results.
    :param uhs_results:
        UHS computation results structured like the output of :func:`make_uhs`.
    :param float poe:
        Probability of exceedance of the hazard maps from which these UH
        Spectra were produced.
    :param rlz:
        :class:`openquake.engine.db.models.LtRealization`. Specify only if
        these results are for an end branch.
    :param statistics:
        'mean' or 'quantile'. Specify only if these are statistical results.
    :param float quantile:
        Specify only if ``statistics`` == 'quantile'.
    """
    output = models.Output(
        oq_job=job,
        output_type='uh_spectra'
    )
    uhs = models.UHS(
        poe=poe,
        investigation_time=job.hazard_calculation.investigation_time,
        periods=uhs_results['periods'],
    )
    if rlz is not None:
        uhs.lt_realization = rlz
        output.display_name = _UHS_DISP_NAME_FMT % dict(poe=poe, rlz=rlz.id)
    elif statistics is not None:
        uhs.statistics = statistics
        if statistics == 'quantile':
            uhs.quantile = quantile
            output.display_name = (_UHS_DISP_NAME_QUANTILE_FMT
                                   % dict(poe=poe, quantile=quantile))
        else:
            # mean
            output.display_name = _UHS_DISP_NAME_MEAN_FMT % dict(poe=poe)
    output.save()
    uhs.output = output
    # This should fail if neither `lt_realization` nor `statistics` is defined:
    uhs.save()

    with transaction.commit_on_success(using='reslt_writer'):
        inserter = CacheInserter(models.UHSData, CURVE_CACHE_SIZE)
        for lon, lat, imls in uhs_results['uh_spectra']:
            inserter.add(
                models.UHSData(
                    uhs_id=uhs.id,
                    imls='{%s}' % ','.join(str(x) for x in imls),
                    location='POINT(%s %s)' % (lon, lat))
            )
        inserter.flush()
