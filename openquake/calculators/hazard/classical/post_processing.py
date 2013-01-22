# -*- coding: utf-8 -*-
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

# Copyright (c) 2010-2012, GEM Foundation.
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

import openquake

from celery.task.sets import TaskSet
from scipy.stats import mstats


from openquake import logs
from openquake.db import models
from openquake.utils import config
from openquake.utils import tasks as utils_tasks
from openquake.utils.general import block_splitter


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


def get_post_processing_fn(key):
    """
    Given a key it returns a scientific function decorated with the
    persite_result_decorator
    """
    base_fns = {
        "mean_weighted": mean_curves_weighted,
        "quantile_weighted": quantile_curves_weighted,
        "mean": mean_curves,
        "quantile": quantile_curves}
    return persite_result_decorator(base_fns[key])


def persite_result_decorator(func):
    """
    Decorator function to calculate per-site result (e.g. mean
    curves). It creates a new function that fetch the curves with a
    reader object, compute the results, write them using a writer
    object.
    """

    def new_function(chunk_of_curves, writer, use_weights, *args, **kwargs):
        """
        :param chunk_of_curves is an object that implements the
          properties poes, weights, locations and curves_per_location

        :param writer:
          an object that can save the result.

        :param use_weights:
          True if weights should be passed to func

        :param *args, *kwargs:
          other arguments passed to the wrapped function
        """

        poe_matrix, weights, locations = _fetch_curves(chunk_of_curves)

        if use_weights:
            results = func(poe_matrix, weights, *args, **kwargs)
        else:
            results = func(poe_matrix, *args, **kwargs)

        _write_aggregate_results(writer, results, locations)

    return new_function


def _fetch_curves(chunk_of_curves):
    """
    Fetch the individual curves poes and their locations. See
    `persite_result_decorator` for more details
    """

    curves = chunk_of_curves.poes
    locations = numpy.array(chunk_of_curves.locations)
    weights = numpy.array(chunk_of_curves.weights)

    level_nr = len(curves[0])
    loc_nr = len(curves) / chunk_of_curves.curves_per_location
    poe_matrix = numpy.reshape(
        curves, (chunk_of_curves.curves_per_location, loc_nr, level_nr), 'F')

    return poe_matrix, weights, locations


def _write_aggregate_results(writer, results, locations):
    """
    Write `results` for each location in `locations` by using `writer`
    """
    with writer as w:
        for i, location in enumerate(locations):
            w.add_data(location, results[i].tolist())


def mean_curves(poe_matrix):
    """
    Calculate mean curves. Unweighted

    :param poe_matrix:
      a 3d matrix with shape given by (curves_per_location x
      number of locations x intensity measure levels)
    """
    return numpy.mean(poe_matrix, axis=0)


def mean_curves_weighted(poe_matrix, weights):
    """
    Calculate mean curves. Weighted version

    :param poe_matrix:
      a 3d matrix with shape given by (curves_per_location x
      number of locations x intensity measure levels)

    :param weights:
      a vector of weights with size equal to the number of
      curves per location
    """
    return numpy.average(poe_matrix, weights=weights, axis=0)


def quantile_curves(poe_matrix, quantile):
    """
    Compute quantile curves. Unweighted version

    :param poe_matrix:
      a 3d matrix with shape given by (curves_per_location x
      number of locations x intensity measure levels)

    :param quantile:
      The quantile considered by the computation
    """

    # mquantiles can not work on 3d matrixes, so we roll back the
    # location axis as first dimension, then we iterate on each
    # locations
    poe_matrixes = numpy.rollaxis(poe_matrix, 1, 0)
    return [mstats.mquantiles(curves, quantile, axis=0)[0]
            for curves in poe_matrixes]


def quantile_curves_weighted(poe_matrix, weights, quantile):
    """
    Compute quantile curves. Weighted version

    :param poe_matrix:
      a 3d matrix with shape given by (curves_per_location x
      number of locations x intensity measure levels)

    :param weights:
      a vector of weights with size equal to the number of
      curves per location

    :param quantile:
      The quantile considered by the computation
    """
    # NOTE(LB): Weights might be passed as a list of `decimal.Decimal`
    # types, and numpy.interp can't handle this (it throws TypeErrors).
    # So we explicitly cast to floats here before doing interpolation.
    weights = numpy.array(weights, dtype=numpy.float64)

    # Here, we expect that weight values sum to 1. A weight
    # describes the probability that a realization is expected
    # to occur.
    poe_matrixes = poe_matrix.transpose()
    ret = []
    for curves in poe_matrixes:  # iterate on locations
        result_curve = []
        for poes in curves:  # iterate on levels
            sorted_poe_idxs = numpy.argsort(poes)
            sorted_weights = weights[sorted_poe_idxs]
            sorted_poes = poes[sorted_poe_idxs]

            cum_weights = numpy.cumsum(sorted_weights)
            result_curve.append(
                numpy.interp(quantile, cum_weights, sorted_poes))
        ret.append(result_curve)
    return numpy.array(ret).transpose()


# Disabling "Unused argument 'job_id'" (this parameter is required by @oqtask):
# pylint: disable=W0613
@utils_tasks.oqtask
def do_post_process(job_id, post_processing_task):
    """
    Executing a post-processing work package. It could be a mean, quantile, or
    hazard map post-processing task.
    """
    func_key, func_args = post_processing_task
    func = get_post_processing_fn(func_key)
    # Disabling 'Used * or ** magic'
    # pylint: disable=W0142
    func(*func_args)
do_post_process.ignore_result = False


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
        ID of the current :class:`openquake.db.models.OqJob`.
    :param int hazard_curve_id:
        ID of a set of
        :class:`hazard curves <openquake.db.models.HazardCurve>`.
    :param list poes:
        List of PoEs for which we want to iterpolate hazard maps.
    """
    job = models.OqJob.objects.get(id=job_id)

    hc = models.HazardCurve.objects.get(id=hazard_curve_id)
    hcd = hc.hazardcurvedata_set.order_by('location')

    curves = (curve.poes for curve in hcd)
    hazard_maps = compute_hazard_maps(curves, hc.imls, poes)

    for i, poe in enumerate(poes):
        imls = hazard_maps[i]
        lons = numpy.empty(imls.shape)
        lats = numpy.empty(imls.shape)

        for j, _ in enumerate(imls):
            location = hcd[j].location
            lons[j] = location.x
            lats[j] = location.y

        imt = hc.imt
        if imt == 'SA':
            # if it's SA, include the period using the standard notation
            imt = 'SA(%s)' % hc.sa_period

        # save the hazard map
        # create `Output` first:
        if hc.statistics == 'mean':
            disp_name = _HAZ_MAP_DISP_NAME_MEAN_FMT % dict(poe=poe, imt=imt)
        elif hc.statistics == 'quantile':
            disp_name = _HAZ_MAP_DISP_NAME_QUANTILE_FMT % dict(
                poe=poe, imt=imt, quantile=hc.quantile)
        else:
            disp_name = _HAZ_MAP_DISP_NAME_FMT % dict(
                poe=poe, imt=imt, rlz=hc.lt_realization.id)

        output = models.Output.objects.create_output(
            job, disp_name, 'hazard_map')

        # now create and store the hazard map
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
            imls=imls,
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
        A :class:`openquake.db.models.OqJob` which has some hazard curves
        associated with it.
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

        if openquake.no_distribute():
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


def compute_mean_curve(curves, weights=None):
    """
    Compute the mean or weighted average of a set of curves.

    :param curves:
        2D array-like collection of hazard curve PoE values. Each element
        should be a sequence of PoE `float` values. Example::

            [[0.5, 0.4, 0.3], [0.6, 0.59, 0.1]]

        .. note::
            This data represents the curves for all realizations for a given
            site and IMT.

    :param weights:
        List or numpy array of weights, 1 weight value for each of the input
        ``curves``. This is only used for weighted averages.

    :returns:
        A curve representing the mean/average (or weighted average, in case
        ``weights`` are specified) of all the input ``curves``.
    """
    # Weights
    if weights is not None:
        # If all of the weights are None, don't compute a weighted average
        if set(weights) == set([None]):
            weights = None
        elif any([x is None for x in weights]):
            # a subset of the weights are None
            # this is invalid
            raise ValueError('`None` value found in weights: %s' % weights)

    return numpy.average(curves, weights=weights, axis=0)


def compute_weighted_quantile_curve(curves, weights, quantile):
    """
    Compute the weighted quantile aggregate of a set of curves. This method is
    used in the case where hazard curves are computed using the logic tree
    end-branch enumeration approach. In this case, the weights are explicit.

    :param curves:
        2D array-like of curve PoEs. Each row represents the PoEs for a single
        curve
    :param weights:
        Array-like of weights, 1 for each input curve.
    :param quantile:
        Quantile value to calculate. Should in the range [0.0, 1.0].

    :returns:
        A numpy array representing the quantile aggregate of the input
        ``curves`` and ``quantile``, weighting each curve with the specified
        ``weights``.
    """
    # Each curve needs to be associated with a weight:
    assert len(weights) == len(curves)
    # NOTE(LB): Weights might be passed as a list of `decimal.Decimal`
    # types, and numpy.interp can't handle this (it throws TypeErrors).
    # So we explicitly cast to floats here before doing interpolation.
    weights = numpy.array(weights, dtype=numpy.float64)

    result_curve = []

    np_curves = numpy.array(curves)
    np_weights = numpy.array(weights)

    for poes in np_curves.transpose():
        sorted_poe_idxs = numpy.argsort(poes)
        sorted_weights = np_weights[sorted_poe_idxs]
        sorted_poes = poes[sorted_poe_idxs]

        # cumulative sum of weights:
        cum_weights = numpy.cumsum(sorted_weights)

        result_curve.append(numpy.interp(quantile, cum_weights, sorted_poes))

    return numpy.array(result_curve)


def compute_quantile_curve(curves, quantile):
    """
    Compute the quantile aggregate of a set of curves. This method is used in
    the case where hazard curves are computed using the Monte-Carlo logic tree
    sampling approach. In this case, the weights are implicit.

    :param curves:
        2D array-like collection of hazard curve PoE values. Each element
        should be a sequence of PoE `float` values. Example::

            [[0.5, 0.4, 0.3], [0.6, 0.59, 0.1]]
    :param float quantile:
        The quantile value. We expected a value in the range [0.0, 1.0].

    :returns:
        A numpy array representing the quantile aggregate of the input
        ``curves`` and ``quantile``.
    """
    # this implementation is an alternative to:
    # return numpy.array(mstats.mquantiles(curves, prob=quantile, axis=0))[0]

    # more or less copied from the scipy mquantiles function, just special
    # cased for what we need (and about 6x faster)

    arr = numpy.array(curves)

    p = numpy.array(quantile)
    m = 0.4 + p * 0.2

    n = len(arr)
    aleph = n * p + m
    k = numpy.floor(aleph.clip(1, n - 1)).astype(int)
    gamma = (aleph - k).clip(0, 1)

    data = numpy.sort(arr, axis=0).transpose()
    return (1.0 - gamma) * data[:, k - 1] + gamma * data[:, k]
