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

from django.db import transaction
from itertools import izip

from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.writer import CacheInserter

# cutoff value for the poe
EPSILON = 1E-30

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

        The results are structured this way so that it is easy to iterate over
        the hazard map results in a consistent way, no matter how many
        ``poes`` values are specified.
    """
    poes = numpy.array(poes)

    if len(poes.shape) == 0:
        # ``poes`` was passed in as a scalar;
        # convert it to 1D array of 1 element
        poes = poes.reshape(1)

    result = []
    imls = numpy.log(numpy.array(imls[::-1]))

    for curve in curves:
        # the hazard curve, having replaced the too small poes with EPSILON
        curve_cutoff = [max(poe, EPSILON) for poe in curve[::-1]]
        hmap_val = []
        for poe in poes:
            # special case when the interpolation poe is bigger than the
            # maximum, i.e the iml must be smaller than the minumum
            if poe > curve_cutoff[-1]:  # the greatest poes in the curve
                # extrapolate the iml to zero as per
                # https://bugs.launchpad.net/oq-engine/+bug/1292093
                # a consequence is that if all poes are zero any poe > 0
                # is big and the hmap goes automatically to zero
                hmap_val.append(0)
            else:
                # exp-log interpolation, to reduce numerical errors
                # see https://bugs.launchpad.net/oq-engine/+bug/1252770
                val = numpy.exp(
                    numpy.interp(
                        numpy.log(poe), numpy.log(curve_cutoff), imls))
                hmap_val.append(val)

        result.append(hmap_val)
    return numpy.array(result).transpose()


_HAZ_MAP_DISP_NAME_MEAN_FMT = 'Mean Hazard map(%(poe)s) %(imt)s'
_HAZ_MAP_DISP_NAME_QUANTILE_FMT = (
    '%(quantile)s Quantile Hazard Map(%(poe)s) %(imt)s')
# Hazard maps for a specific end branch
_HAZ_MAP_DISP_NAME_FMT = 'Hazard Map(%(poe)s) %(imt)s rlz-%(rlz)s'

_UHS_DISP_NAME_MEAN_FMT = 'Mean UHS (%(poe)s)'
_UHS_DISP_NAME_QUANTILE_FMT = '%(quantile)s Quantile UHS (%(poe)s)'
_UHS_DISP_NAME_FMT = 'UHS (%(poe)s) rlz-%(rlz)s'


@tasks.oqtask
def hazard_curves_to_hazard_map(job_id, hazard_curves, poes):
    """
    Function to process a set of hazard curves into 1 hazard map for each PoE
    in ``poes``.

    Hazard map results are written directly to the database.

    :param int job_id:
        ID of the current :class:`openquake.engine.db.models.OqJob`.
    :param hazard_curves:
        a list of
        :class:`hazard curves <openquake.engine.db.models.HazardCurve>`.
    :param list poes:
        List of PoEs for which we want to iterpolate hazard maps.
    """
    job = models.OqJob.objects.get(id=job_id)
    for hc in hazard_curves:
        hcd = list(models.HazardCurveData.objects.all_curves_simple(
            filter_args=dict(hazard_curve=hc.id), order_by='location'
        ))
        imt = hc.imt
        if imt == 'SA':
            # if it's SA, include the period using the standard notation
            imt = 'SA(%s)' % hc.sa_period

        # Gather all of the curves and compute the maps, for all PoEs
        curves = (_poes for _, _, _poes in hcd)
        hazard_maps = compute_hazard_maps(curves, hc.imls, poes)

        with transaction.commit_on_success(using='job_init'):
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
    output = models.Output(
        oq_job=job,
        output_type='uh_spectra'
    )
    uhs = models.UHS(
        poe=poe,
        investigation_time=job.get_param('investigation_time'),
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

    with transaction.commit_on_success(using='job_init'):
        inserter = CacheInserter(models.UHSData, max_cache_size=10000)
        for lon, lat, imls in uhs_results['uh_spectra']:
            inserter.add(
                models.UHSData(
                    uhs_id=uhs.id,
                    imls='{%s}' % ','.join(str(x) for x in imls),
                    location='POINT(%s %s)' % (lon, lat))
            )
        inserter.flush()
