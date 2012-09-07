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

    The setup of the output may involve the creation of object on
    the database.

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

    for imt in calculation.intensity_measure_types_and_levels:

        chunks_generator = curve_finder.individual_curves_chunks

        if calculation.should_compute_mean_curves():
            writer = writers['mean_curves'](job, imt)
            writer.create_aggregate_result()

            fn = _mean_curve_fn()

            for chunk_of_curves in chunks_generator(job, imt,
                                                    curves_per_task):
                tasks.append(fn)
                tasks_args.append((
                    chunk_of_curves, curves_per_location,
                    calculation.number_of_logic_tree_samples,
                    writer))

        if calculation.should_compute_quantile_functions():
            fn = _quantile_curve_fn()

            for quantile in calculation.quantile_hazard_curves:
                writer = writers['quantile_curves'](job, imt, quantile)
                writer.create_aggregate_result()

                for chunk_of_curves in chunks_generator(imt, curves_per_task):
                    tasks.append(fn)
                    tasks_args.append(
                        (quantile, chunk_of_curves, curves_per_location,
                         calculation.number_of_logic_tree_samples, writer))
            return tasks, tasks_args

    def _should_compute_mean_curves(self):
        """
        Return None if no mean curve calculation has been requested
        """
        return self._calculation.mean_hazard_curves

    def _should_compute_quantile_functions(self):
        """
        Return None if no quantile curve calculation has been requested
        """
        return self._calculation.quantile_hazard_curves

    def _should_be_distributed(self):
        """
        Return True if the calculation should be distributed
        """
        return self._curve_nr > self.__class__.DISTRIBUTION_THRESHOLD

def _curves_per_task(curve_finder, location_block_size):
        """
        Returns the number of curves calculated by each task
        """
    def __init__(self, job, calc,
                 location_block_size=None):
        self._location_block_size = (location_block_size or
                                     self.__class__.DEFAULT_CURVE_BLOCK_SIZE)
        self._job = job
        self._calculation = calc
        self._curves_per_location = calc.individual_curves_per_location()
        self._curve_nr = self._curve_finder.individual_curves_nr(self._job)


        
        return self._curves_per_location * self._location_block_size


class PerSiteResultCalculator(object):
    """
    Abstract class to calculate per-site result (e.g. mean curves).

    :attribute _curves_per_location
      the number of curves for each location considered for
      calculation

    :attribute _chunk_of_curves a list of individual curve chunks
      (usually spanning more locations). Each chunk is a function that
      actually fetches the curves when it is invoked. This function
      accept a parameter `field` that can be:

      "poes" to fetch the y values
      "wkb" to fetch the locations.

    :attribute _result_writer
      an object that can save the result.
      See `PostProcessor` for more details
    """

    def _should_consider_weights(self):
        """
        Return True if the calculation of aggregate result should
        consider the weight of the individual curves
        """
        return not (
            self.number_of_logic_tree_samples > 0)

    def __call__(self, ):
        """
        Fetch the curves, calculate the mean curves and save them
        """
        poe_matrix = self.fetch_curves()

        if self._use_weights:
            weights = self.fetch_weights()
        else:
            weights = None

        results = self.compute_results(poe_matrix, weights)

        with self._result_writer as writer:
            for i, location in enumerate(self.locations()):
                result = results[i]
                writer.add_data(location, result.tolist())

    def compute_results(self, poe_matrix, weights=None):
        """
        Abstract method. Given a 3d matrix with shape
        (curves_per_location x number of locations x levels))
        compute a result for each location.

        If `weigths` are given, the computation have to consider the
        weights for the individual contribution
        """
        raise NotImplementedError

    def locations(self):
        """
        A generator of locations in wkb format considered by the
        computation
        """
        locations = self._chunk_of_curves('wkb')
        distinct_locations = locations[::self._curves_per_location]

        for location in distinct_locations:
            yield location

    def fetch_weights(self):
        """
        Return a vector of weights of dimension equal to the number of
        curves per location
        """
        weights = self._chunk_of_curves('weight')

        return numpy.array(weights[0:self._curves_per_location])

    def fetch_curves(self):
        """
        Returns a 3d matrix with shape given by
        (curves_per_location x number of locations x levels))
        """
        curves = self._chunk_of_curves('poes')
        level_nr = len(curves[0])
        self._level_nr = level_nr
        loc_nr = len(curves) / self._curves_per_location
        return numpy.reshape(curves,
                             (self._curves_per_location, loc_nr, level_nr),
                             'F')


class MeanCurveCalculator(PerSiteResultCalculator):
    """
    Calculate mean curves.

    :attribute _result_writer
      an object that can save the result by calling #create_mean_curve

    See the base class doc for other attributes
    """
    def __init__(self, job, curves_per_location, chunk_of_curves,
                 curve_writer):
        super(MeanCurveCalculator, self).__init__(
            job, curves_per_location, chunk_of_curves, curve_writer)

    def compute_results(self, poe_matrix, weights=None):
        """
        Calculate all the mean curves in one shot
        """
        return numpy.average(poe_matrix, weights=weights, axis=0)


class QuantileCurveCalculator(PerSiteResultCalculator):
    """
    Compute quantile curves for a block of locations
    """
    def __init__(self, job, curves_per_location, chunk_of_curves, curve_writer,
                 quantile):
        super(QuantileCurveCalculator, self).__init__(
            job, curves_per_location, chunk_of_curves, curve_writer)

        self._quantile = quantile

    def compute_results(self, poe_matrix, weights=None):
        """
        Compute all the quantile function (for quantiles given by the
        attribute `quantile`) for each location in one shot
        """

        # mquantiles can not work on 3d matrixes, so we roll back the
        # location axis as first dimension, then we iterate on each
        # locations
        if not self._use_weights:
            poe_matrixes = numpy.rollaxis(poe_matrix, 1, 0)
            return [mstats.mquantiles(curves, self._quantile, axis=0)[0]
                    for curves in poe_matrixes]
        else:
            # Here, we expect that weight values sum to 1. A weight
            # describes the probability that a realization is expected
            # to occur.
            poe_matrixes = poe_matrix.transpose()
            ret = []
            for curves in poe_matrixes:  # iterate on locations
                result_curve = []
                for poes in curves:
                    sorted_poe_idxs = numpy.argsort(poes)
                    sorted_weights = weights[sorted_poe_idxs]
                    sorted_poes = poes[sorted_poe_idxs]

                    cum_weights = numpy.cumsum(sorted_weights)
                    result_curve.append(
                        numpy.interp(self._quantile, cum_weights, sorted_poes))
                ret.append(result_curve)
            return numpy.array(ret).transpose()
