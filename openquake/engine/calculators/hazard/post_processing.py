# -*- coding: utf-8 -*-
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

# Copyright (c) 2010-2014, GEM Foundation.
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

from itertools import izip

from openquake.commonlib.calculators import calc
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.writer import CacheInserter


_HAZ_MAP_DISP_NAME_MEAN_FMT = 'Mean Hazard map(%(poe)s) %(imt)s'
_HAZ_MAP_DISP_NAME_QUANTILE_FMT = (
    '%(quantile)s Quantile Hazard Map(%(poe)s) %(imt)s')
# Hazard maps for a specific end branch
_HAZ_MAP_DISP_NAME_FMT = 'Hazard Map(%(poe)s) %(imt)s rlz-%(rlz)s'

_UHS_DISP_NAME_MEAN_FMT = 'Mean UHS (%(poe)s)'
_UHS_DISP_NAME_QUANTILE_FMT = '%(quantile)s Quantile UHS (%(poe)s)'
_UHS_DISP_NAME_FMT = 'UHS (%(poe)s) rlz-%(rlz)s'


@tasks.oqtask
def hazard_curves_to_hazard_map(hazard_curves, poes, monitor):
    """
    Function to process a set of hazard curves into 1 hazard map for each PoE
    in ``poes``.

    Hazard map results are written directly to the database.

    :param hazard_curves:
        a list of
        :class:`hazard curves <openquake.engine.db.models.HazardCurve>`
    :param list poes:
        list of PoEs for which we want to iterpolate hazard maps
    :param monitor:
        monitor of the currently running job
    """
    job = models.OqJob.objects.get(id=monitor.job_id)
    for hc in hazard_curves:
        hcd = list(models.HazardCurveData.objects.all_curves_simple(
            filter_args=dict(hazard_curve=hc.id), order_by='location'
        ))
        imt = hc.imt
        if imt == 'SA':
            # if it's SA, include the period using the standard notation
            imt = 'SA(%s)' % hc.sa_period

        # Gather all of the curves and compute the maps, for all PoEs
        curves = [_poes for _, _, _poes in hcd]
        hazard_maps = calc.compute_hazard_maps(curves, hc.imls, poes)

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
                disp_name = _HAZ_MAP_DISP_NAME_MEAN_FMT % dict(
                    poe=poe, imt=imt)
            elif hc.statistics == 'quantile':
                disp_name = _HAZ_MAP_DISP_NAME_QUANTILE_FMT % dict(
                    poe=poe, imt=imt, quantile=hc.quantile)
            else:
                disp_name = _HAZ_MAP_DISP_NAME_FMT % dict(
                    poe=poe, imt=imt, rlz=hc.lt_realization.id)

            output = job.get_or_create_output(disp_name, 'hazard_map')

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
                lons=lons.tolist(),
                lats=lats.tolist(),
                imls=map_values.tolist(),
            )


def do_uhs_post_proc(job):
    """
    Compute and save (to the DB) Uniform Hazard Spectra for all hazard maps for
    the given ``job``.

    :param job:
        Instance of :class:`openquake.engine.db.models.OqJob`.
    """
    poes = job.get_param('poes')
    quantile_hazard_curves = job.get_param('quantile_hazard_curves', [])

    rlzs = models.LtRealization.objects.filter(
        lt_model__hazard_calculation=job)

    for poe in poes:
        maps_for_poe = models.HazardMap.objects.filter(
            output__oq_job=job, poe=poe
        )

        # mean (if defined)
        mean_maps = maps_for_poe.filter(statistics='mean')
        if mean_maps.count() > 0:
            mean_uhs = make_uhs(mean_maps)
            _save_uhs(job, mean_uhs, poe, statistics='mean')

        # quantiles (if defined)
        for quantile in quantile_hazard_curves:
            quantile_maps = maps_for_poe.filter(
                statistics='quantile', quantile=quantile
            )
            if quantile_maps:
                # they are missing if there is a single realization
                quantile_uhs = make_uhs(quantile_maps)
                _save_uhs(job, quantile_uhs, poe, statistics='quantile',
                          quantile=quantile)

        if job.get_param('individual_curves', True):
            # build a map for each logic tree branch
            for rlz in rlzs:
                rlz_maps = maps_for_poe.filter(
                    statistics=None, lt_realization=rlz
                )
                assert rlz_maps, \
                    'Could not find HazardMaps for rlz=%d' % rlz.id
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
    uhs = models.UHS(
        poe=poe,
        investigation_time=job.get_param('investigation_time'),
        periods=uhs_results['periods'],
    )
    if rlz is not None:
        uhs.lt_realization = rlz
        display_name = _UHS_DISP_NAME_FMT % dict(poe=poe, rlz=rlz.id)
    elif statistics is not None:
        uhs.statistics = statistics
        if statistics == 'quantile':
            uhs.quantile = quantile
            display_name = (_UHS_DISP_NAME_QUANTILE_FMT
                            % dict(poe=poe, quantile=quantile))
        else:  # mean
            display_name = _UHS_DISP_NAME_MEAN_FMT % dict(poe=poe)
    output = job.get_or_create_output(display_name, 'uh_spectra')
    uhs.output = output
    # This should fail if neither `lt_realization` nor `statistics` is defined:
    uhs.save()

    inserter = CacheInserter(models.UHSData, max_cache_size=10000)
    for lon, lat, imls in uhs_results['uh_spectra']:
        inserter.add(
            models.UHSData(
                uhs_id=uhs.id,
                imls='{%s}' % ','.join(str(x) for x in imls),
                location='POINT(%s %s)' % (lon, lat))
        )
    inserter.flush()
