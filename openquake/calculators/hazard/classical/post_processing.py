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
from scipy.stats.mstats import mquantiles


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

    :attribute _result_writer
      An object used to save aggregate results.
      It should implement the methods #create_mean_curve and
      #create_quantile_curves

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
                 curve_finder=None, curve_writer=None, task_handler=None):
        self._calculation = hc
        self._curve_finder = curve_finder
        self._result_writer = curve_writer
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

        for imt in self._calculation.intensity_measure_types_and_levels:
            self._result_writer.imt = imt

            chunks_of_curves = self._curve_finder.individual_curves_chunks(
                imt, curves_per_task)

            if self.should_compute_mean_curves():
                for chunk_of_curves in chunks_of_curves:
                    self._task_handler.enqueue(
                        MeanCurveCalculator,
                        curves_per_location=self._curves_per_location,
                        chunk_of_curves=chunk_of_curves,
                        curve_writer=self._result_writer)

            if self.should_compute_quantile_functions():
                for chunk_of_curves in chunks_of_curves:
                    for quantile in self._calculation.quantile_hazard_curves:
                        self._task_handler.enqueue(
                            QuantileCurveCalculator,
                            curves_per_location=self._curves_per_location,
                            chunk_of_curves=chunk_of_curves,
                            curve_writer=self._result_writer,
                            quantile=quantile)

    def run(self):
        """
        Execute the calculation using the task queue handler
        """
        if self.should_be_distributed():
            self._task_handler.apply_async()
            self._task_handler.wait_for_results()
        else:
            self._task_handler.apply()

    def should_compute_mean_curves(self):
        """
        Returns None if no mean curve calculation has been requested
        """
        return self._calculation.mean_hazard_curves

    def should_compute_quantile_functions(self):
        """
        Returns None if no quantile curve calculation has been requested
        """
        return self._calculation.quantile_hazard_curves

    def should_be_distributed(self):
        """
        Returns True if the calculation should be distributed
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
      accept a parameter `field` that can be "poes" to fetch the y
      values and "location" the fetch the x values.

    :attribute _result_writer
      an object that can save the result
    """
    def __init__(self, curves_per_location, chunk_of_curves,
                 curve_writer):
        self._chunk_of_curves = chunk_of_curves
        self._curves_per_location = curves_per_location
        self._result_writer = curve_writer

    def run(self):
        """
        Fetch the curves, calculate the mean curves and save them
        """
        poe_matrix = self.fetch_curves()

        results = self.compute_results(poe_matrix)

        for i, location in enumerate(self.locations()):
            result = results[i]
            self.save_result(location, result)

    def compute_results(self, poe_matrix):
        """
        Abstract method. Given a 3d matrix with shape
        (curves_per_location x number of locations x levels))
        compute a result for each location
        """
        raise NotImplementedError

    def save_result(self, location, result):
        """
        Abstract method. Given a `result` at `location` it saves the result
        """
        raise NotImplementedError

    def locations(self):
        """
        A generator of locations considered by the computation
        """
        locations = self._chunk_of_curves('location')
        distinct_locations = locations[::self._curves_per_location]
        for location in distinct_locations:
            yield location

    def fetch_curves(self):
        """
        Returns a 3d matrix with shape given by
        (curves_per_location x number of locations x levels))
        """
        curves = self._chunk_of_curves('poes')
        level_nr = len(curves[0])
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
    def __init__(self, curves_per_location, chunk_of_curves,
                 curve_writer):
        super(MeanCurveCalculator, self).__init__(
            curves_per_location,
            chunk_of_curves,
            curve_writer)

    def compute_results(self, poe_matrix):
        """
        Calculate all the mean curves in one shot
        """
        return numpy.mean(poe_matrix, axis=0)

    def save_result(self, location, mean_curve):
        """
        Save the mean curve.
        """
        self._result_writer.create_mean_curve(location, mean_curve)


class QuantileCurveCalculator(PerSiteResultCalculator):
    """
    Compute quantile curves for a block of locations
    """
    def __init__(self, curves_per_location, chunk_of_curves, curve_writer,
                 quantile):
        super(QuantileCurveCalculator, self).__init__(
            curves_per_location,
            chunk_of_curves,
            curve_writer)

        self._quantile = quantile

    def compute_results(self, poe_matrix):
        """
        Compute all the quantile function (for quantiles given by the
        attribute `quantile`) for each location in one shot
        """

        # mquantiles can not work on 3d matrixes, so we roll back the
        # location axis as first dimension, then we iterate on each
        # locations
        poe_matrixes = numpy.rollaxis(poe_matrix, 1, 0)
        return [mquantiles(curves, self._quantile, axis=0)[0]
                for curves in poe_matrixes]

    def save_result(self, location, quantile_curve):
        """
        Save a quantile curve
        """
        self._result_writer.create_quantile_curve(location,
                                                 self._quantile,
                                                 quantile_curve)
