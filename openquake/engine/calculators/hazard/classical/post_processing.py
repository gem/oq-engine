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

import math
import numpy

import openquake.engine

from celery.task.sets import TaskSet

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.utils import tasks as utils_tasks
from openquake.engine.utils.general import block_splitter


# Number of locations considered by each task
DEFAULT_LOCATIONS_PER_TASK = 1000


def setup_tasks(job, calculation, curve_finder, writers,
                locations_per_task=DEFAULT_LOCATIONS_PER_TASK):
    """
    Return the tasks for the post processing computation and setup
    the output.

    Each task is responsible to calculate the mean/quantile curve
    for a chunk of locations and for a specific intensity measure
    type.

    The setup of the output involves the creation of a aggregate
    result container object.

    :param job:
      The job associated with this computation

    :param calculation:
      An object holding the configuration of the calculation.
      It should implement the property intensity_measure_types_and_levels
      (returning a dictionary imt -> levels)
      the method #individual_curves_per_location

    :param curve_finder:
      An object used to query for individual hazard curves.
      It should implement the methods #individual_curve_nr and
      #individual_curve_chunks and #get_weights

    :param writers:
      An dictionary of ResultWriters classes.
      A ResultWriter is a context manager that implement the method
      #add_data and #create_aggregate_result. It flushes the
      results when it exits from the generated context

    :param locations_per_task:
      Number of locations processed by each task in the post process
      phase (optional)
    """

    tasks = []

    use_weights = calculation.number_of_logic_tree_samples == 0
    if use_weights:
        mean_curves_fn = "mean_weighted"
        quantile_curves_fn = "quantile_weighted"
    else:
        mean_curves_fn = "mean"
        quantile_curves_fn = "quantile"

    for imt in calculation.intensity_measure_types_and_levels:

        chunks = curve_finder.individual_curves_chunks(
            job, imt, locations_per_task)

        if calculation.should_compute_mean_curves():
            writer = writers['mean_curves'](job, imt)
            writer.create_aggregate_result()

            for chunk in chunks:
                tasks.append(
                    [mean_curves_fn, (chunk, writer, use_weights)])

        if calculation.should_compute_quantile_curves():
            for quantile in calculation.quantile_hazard_curves:
                writer = writers['quantile_curves'](job, imt, quantile)
                writer.create_aggregate_result()
                for chunk in chunks:
                    tasks.append(
                        [quantile_curves_fn,
                         (chunk, writer, use_weights, quantile)])
    return tasks


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


# Disabling 'invalid name'
# pylint: disable=C0103
hazard_curves_to_hazard_map_task = utils_tasks.oqtask(
    hazard_curves_to_hazard_map)
hazard_curves_to_hazard_map_task.ignore_result = False


def do_hazard_map_post_process(job):
    """
    Create and distribute tasks for processing hazard curves into hazard maps.

    :param job:
        A :class:`openquake.engine.db.models.OqJob` which has some hazard
        curves associated with it.
    """
    logs.LOG.debug('> Post-processing - Hazard Maps')
    block_size = int(config.get('hazard', 'concurrent_tasks'))

    poes = job.hazard_calculation.poes_hazard_maps

    # Stats for debug logging:
    hazard_curve_ids = models.HazardCurve.objects.filter(
        output__oq_job=job).values_list('id', flat=True)
    logs.LOG.debug('num haz curves: %s' % len(hazard_curve_ids))

    # Limit the number of concurrent tasks to the configured concurrency level:
    block_gen = block_splitter(hazard_curve_ids, block_size)
    total_blocks = int(math.ceil(len(hazard_curve_ids) / float(block_size)))

    for i, block in enumerate(block_gen):
        logs.LOG.debug('> Hazard post-processing block, %s of %s'
                       % (i + 1, total_blocks))

        if openquake.engine.no_distribute():
            # just execute the post-processing using the plain function form of
            # the task
            for hazard_curve_id in block:
                hazard_curves_to_hazard_map_task(job.id, hazard_curve_id, poes)
        else:
            tasks = []
            for hazard_curve_id in block:
                tasks.append(hazard_curves_to_hazard_map_task.subtask(
                    (job.id, hazard_curve_id, poes)))
            results = TaskSet(tasks=tasks).apply_async()

            utils_tasks._check_exception(results)

        logs.LOG.debug('< Done Hazard Map post-processing block, %s of %s'
                       % (i + 1, total_blocks))
    logs.LOG.debug('< Done post-processing - Hazard Maps')
