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

import functools
import numpy
from scipy.stats import mstats


# Number of locations considered by each task
DEFAULT_LOCATIONS_PER_TASK = 100


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

    :param job
      The job associated with this computation

    :param calculation
      An object holding the configuration of the calculation.
      It should implement the property intensity_measure_types_and_levels
      (returning a dictionary imt -> levels)
      the method #individual_curves_per_location

    :param locations_per_task
      Number of locations processed by each task in the post process
      phase (optional)

    :param curve_finder
      An object used to query for individual hazard curves.
      It should implement the methods #individual_curve_nr and
      #individual_curve_chunks

    :param writers
      An dictionary of ResultWriters classes.
      A ResultWriter is a context manager that implement the method
      #add_data and #create_aggregate_result. It flushes the
      results when it exits from the generated context
    """

    curves_per_location = calculation.individual_curves_per_location()
    curves_per_task = curves_per_location * locations_per_task
    tasks, tasks_args = [], []
    mean_curve_fn = persite_result_decorator(mean_curves)

    for imt in calculation.intensity_measure_types_and_levels:

        if calculation.should_compute_mean_curves():
            writer = writers['mean_curves'](job, imt)
            writer.create_aggregate_result()

            for chunk_of_curves in (
                    curve_finder.individual_curves_chunks(job, imt,
                                                          curves_per_task)):
                tasks.append(mean_curve_fn)
                tasks_args.append((
                    chunk_of_curves, curves_per_location,
                    calculation.number_of_logic_tree_samples,
                    writer))

        if calculation.should_compute_quantile_curves():
            for quantile in calculation.quantile_hazard_curves:
                quantile_curve_fn = persite_result_decorator(
                    functools.partial(quantile_curves, quantile=quantile))
                writer = writers['quantile_curves'](job, imt, quantile)
                writer.create_aggregate_result()

                for chunk_of_curves in (
                        curve_finder.individual_curves_chunks(
                            imt, curves_per_task)):
                    tasks.append(quantile_curve_fn)
                    tasks_args.append(
                        (chunk_of_curves, curves_per_location,
                         calculation.number_of_logic_tree_samples, writer,
                         quantile))
        return tasks, tasks_args


def persite_result_decorator(func):
    """
    Decorator function to calculate per-site result (e.g. mean
    curves). It creates a new function that fetch the curves with a
    reader object, compute the results, write them using a writer
    object
    """
    def new_function(chunk_of_curves, curves_per_location,
                     number_of_logic_tree_samples, writer, *args, **kwargs):
        """
        :param curves_per_location
        the number of curves for each location considered for
        calculation

        :param chunk_of_curves a list of individual curve chunks
        (usually spanning more locations). Each chunk is a function that
        actually fetches the curves when it is invoked. This function
        accept a parameter `field` that can be:

        "poes" to fetch the y values
        "wkb" to fetch the locations.

        :param number_of_logic_tree_samples
        The number of logic tree samples of the computation. If
        non-zero, weights are not considered

        :param writer
        an object that can save the result.
        """

        poe_matrix, weights, locations = _fetch_curves(
            chunk_of_curves, curves_per_location, number_of_logic_tree_samples)

        results = func(poe_matrix, weights, *args, **kwargs)

        _write_aggregate_results(writer, results, locations)

    return new_function


def _fetch_curves(chunk_of_curves, curves_per_location,
                  number_of_logic_tree_samples):
    curves = chunk_of_curves('poes')
    level_nr, loc_nr = len(curves[0]), len(curves) / curves_per_location
    poe_matrix = numpy.reshape(
        curves, (curves_per_location, loc_nr, level_nr), 'F')

    if number_of_logic_tree_samples:
        weights = None
    else:
        weights = numpy.array(
            chunk_of_curves('weight')[0:curves_per_location])

    # get a list of distinct locations in wkb format
    locations = chunk_of_curves('wkb')[::curves_per_location]

    return poe_matrix, weights, locations


def _write_aggregate_results(writer, results, locations):
    with writer as w:
        for i, location in enumerate(locations):
            w.add_data(location, results[i].tolist())


def mean_curves(poe_matrix, weights):
    """
    Calculate mean curves.

    :param poe_matrix
      a 3d matrix with shape given by (curves_per_location x
      number of locations x intensity measure levels)

    :param weights
      a vector of weights with size equal to the number of
      curves per location
    """
    return numpy.average(poe_matrix, weights=weights, axis=0)


def quantile_curves(poe_matrix, weights, quantile):
    """
    Compute quantile curves

    :param quantile
      The quantile considered by the computation

    :param poe_matrix
      a 3d matrix with shape given by (curves_per_location x
      number of locations x intensity measure levels)

    :param weights
      a vector of weights with size equal to the number of
      curves per location
    """

    # mquantiles can not work on 3d matrixes, so we roll back the
    # location axis as first dimension, then we iterate on each
    # locations
    if weights is None:
        poe_matrixes = numpy.rollaxis(poe_matrix, 1, 0)
        return [mstats.mquantiles(curves, quantile, axis=0)[0]
                for curves in poe_matrixes]
    else:
        # Here, we expect that weight values sum to 1. A weight
        # describes the probability that a realization is expected
        # to occur.
        poe_matrixes = poe_matrix.transpose()
        ret = []
        for curves in poe_matrixes:  # iterate on locations
            result_curve = []
            for poes in curves:  # iterate on individual curves
                sorted_poe_idxs = numpy.argsort(poes)
                sorted_weights = weights[sorted_poe_idxs]
                sorted_poes = poes[sorted_poe_idxs]

                cum_weights = numpy.cumsum(sorted_weights)
                result_curve.append(
                    numpy.interp(quantile, cum_weights, sorted_poes))
                ret.append(result_curve)
        return numpy.array(ret).transpose()
