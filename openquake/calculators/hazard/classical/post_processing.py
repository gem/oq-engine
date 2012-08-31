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
"""

import numpy
from scipy.stats import mstats


class PostProcessor(object):
    """Calculate post-processing per-site aggregate results. E.g. mean
    and quantile curves.

    Implements the Command pattern where the commands are instances
    for computing the post-processing output

    The instances of this class should used with the following protocol:
    a_post_processor = PostProcessor(...)
    a_post_processor.initialize() # divide the calculation in subtasks
    a_post_processor.run() # execute subtasks

    :attribute _calculation
      The hazard calculation object with the configuration of the calculation

    :attribute _curve_finder
      An object used to query for individual hazard curves.
      It should implement the methods #individual_curve_nr and
      #individual_curve_chunks

    :attribute _result_writer_factory
      An object used to create ResultWriters.
      It should implement #create_mean_curve_writer and
      #create_quantile_curve_writer

      A ResultWriter is a context manager that implement the method
      #add_data and #create_aggregate_result. It could flush the
      results when it exits from the generated context

    :attribute _task_handler
      An object used to distribute the post process in subtasks.
      It should implement the method #enqueue, #apply_async, #wait_for_results
      and #apply
    """

    # Number of locations processed by each task in the post process phase
    CURVE_BLOCK_SIZE = 100

    # minimum number of curves to be processed with a distributed queue
    DISTRIBUTION_THRESHOLD = 1000

    def __init__(self, hc,
                 curve_finder, result_writer_factory, task_handler):
        self._calculation = hc
        self._curve_finder = curve_finder
        self._result_writer_factory = result_writer_factory
        self._task_handler = task_handler
        self._curves_per_location = hc.individual_curves_per_location()

    def initialize(self):
        """
        Divide the whole computation in tasks.

        Each task is responsible to calculate the mean/quantile curve
        for a chunk of curves and for a specific intensity measure
        type.
        """

        curves_per_task = self.curves_per_task()

        writer_factory = self._result_writer_factory

        for imt in self._calculation.intensity_measure_types_and_levels:

            chunks_generator = self._curve_finder.individual_curves_chunks

            if self.should_compute_mean_curves():
                writer = writer_factory.create_mean_curve_writer(imt)
                writer.create_aggregate_result()

                for chunk_of_curves in chunks_generator(
                        imt, curves_per_task):
                    self._task_handler.enqueue(
                        MeanCurveCalculator,
                        curves_per_location=self._curves_per_location,
                        chunk_of_curves=chunk_of_curves,
                        curve_writer=writer,
                        use_weights=self.should_consider_weights())

            if self.should_compute_quantile_functions():
                for quantile in self._calculation.quantile_hazard_curves:
                    writer = writer_factory.create_quantile_curve_writer(
                        imt, quantile)
                    writer.create_aggregate_result()

                    for chunk_of_curves in chunks_generator(imt,
                                                            curves_per_task):
                        self._task_handler.enqueue(
                            QuantileCurveCalculator,
                            curves_per_location=self._curves_per_location,
                            chunk_of_curves=chunk_of_curves,
                            curve_writer=writer,
                            quantile=quantile,
                            use_weights=self.should_consider_weights())

    def run(self):
        """
        Execute the calculation using the task queue handler. If the
        taskset is too big, it distributes the computation, otherwise
        it is performed locally
        """
        if self.should_be_distributed():
            self._task_handler.apply_async()
            self._task_handler.wait_for_results()
        else:
            self._task_handler.apply()

    def should_consider_weights(self):
        """
        Return True if the calculation of aggregate result should
        consider the weight of the individual curves
        """
        return not (self._calculation.number_of_logic_tree_samples > 0)

    def should_compute_mean_curves(self):
        """
        Return None if no mean curve calculation has been requested
        """
        return self._calculation.mean_hazard_curves

    def should_compute_quantile_functions(self):
        """
        Return None if no quantile curve calculation has been requested
        """
        return self._calculation.quantile_hazard_curves

    def should_be_distributed(self):
        """
        Return True if the calculation should be distributed
        """
        curve_nr = self._curve_finder.individual_curves_nr()
        return curve_nr > self.__class__.DISTRIBUTION_THRESHOLD

    def curves_per_task(self):
        """
        Returns the number of curves calculated by each task
        """
        block_size = self.__class__.CURVE_BLOCK_SIZE
        chunk_size = self._curves_per_location
        return block_size * chunk_size


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

    :attribute _use_weights
      a boolean that indicates if the aggregate values should be
      computed by weighting the individual contributes.
      We remark that weight values are required to sum to 1
    """
    def __init__(self, curves_per_location, chunk_of_curves,
                 curve_writer, use_weights=False):
        self._chunk_of_curves = chunk_of_curves
        self._curves_per_location = curves_per_location
        self._result_writer = curve_writer
        self._use_weights = use_weights
        self._level_nr = None

    def run(self):
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


class PerSiteCurveCalculator(PerSiteResultCalculator):
    """
    Abstract class that defines methods to get and store per site
    curve aggregate data
    """

    def compute_results(self, poe_matrix, weights=None):
        raise NotImplementedError

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


class MeanCurveCalculator(PerSiteCurveCalculator):
    """
    Calculate mean curves.

    :attribute _result_writer
      an object that can save the result by calling #create_mean_curve

    See the base class doc for other attributes
    """
    def __init__(self, curves_per_location, chunk_of_curves,
                 curve_writer, use_weights=False):
        super(MeanCurveCalculator, self).__init__(
            curves_per_location,
            chunk_of_curves,
            curve_writer,
            use_weights=use_weights)

    def compute_results(self, poe_matrix, weights=None):
        """
        Calculate all the mean curves in one shot
        """
        return numpy.average(poe_matrix, weights=weights, axis=0)


class QuantileCurveCalculator(PerSiteCurveCalculator):
    """
    Compute quantile curves for a block of locations
    """
    def __init__(self, curves_per_location, chunk_of_curves, curve_writer,
                 quantile, use_weights=None):
        super(QuantileCurveCalculator, self).__init__(
            curves_per_location,
            chunk_of_curves,
            curve_writer,
            use_weights=use_weights)

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
