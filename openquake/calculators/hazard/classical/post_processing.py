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

import numpy
from scipy.stats import mstats

from openquake.utils import tasks as utils_tasks


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


def compute_hazard_map(curves, imls, poes):
    """
    Given a set of hazard curve poes, interpolate a hazard map at the specified
    ``poe``.

    :param curves:
        2D array of floats. Each row represents a curve, where the values
        in the row are the PoEs (Probabilities of Exceedance) corresponding to
        ``imls``.

    :param imls:
    :param float poes:

    :returns:
        Numpy array of IML (Intensity Measure Level) values, one value for each
        input curve.
    """
    try:
        # if ``poes`` is a list of one element, unpack it to a scalar value
        if len(poes) == 1:
            [poes] = poes
    except TypeError:
        # We'll get a `TypeError` if ``poes`` is already a scalar.
        pass

    result = []
    imls = numpy.array(imls[::-1])

    for curve in curves:
        hmap_val = numpy.interp(poes, curve[::-1], imls)
        result.append(hmap_val)

    return numpy.array(result).transpose()
