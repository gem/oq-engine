# -*- coding: utf-8 -*-
# unittest.TestCase base class does not honor the following coding
# convention
# pylint: disable=C0103,R0904
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
Test classical calculator post processing features
"""

import random
import numpy
import unittest
import itertools
import math
import mock

from tests.utils.helpers import random_location_generator

from openquake.calculators.hazard.classical.post_processing import (
    setup_tasks, mean_curves, quantile_curves, persite_result_decorator)


class PostProcessingTestCase(unittest.TestCase):
    """
    Tests the mean and quantile curves calculation.
    """

    MAX_LOCATION_NR = 50
    MAX_CURVES_PER_LOCATION = 10
    MAX_LEVEL_NR = 10
    SIGMA = 0.001

    def setUp(self):
        self.location_nr = random.randint(1, self.__class__.MAX_LOCATION_NR)
        self.curves_per_location = random.randint(
            1,
            self.__class__.MAX_CURVES_PER_LOCATION)
        self.level_nr = random.randint(1, self.__class__.MAX_LEVEL_NR)
        self.curve_db, self.location_db = _curve_db(
            self.location_nr,
            self.level_nr,
            self.curves_per_location,
            self.__class__.SIGMA)

        self.curve_writer = SimpleCurveWriter()

    def test_mean(self):
        getter = curve_chunks_getter(self.curve_db)

        mean_calculator = persite_result_decorator(
            mean_curves)

        mean_calculator(getter, self.curves_per_location, 0, self.curve_writer)

        self.assertAlmostEqual(self.location_nr, len(self.curve_writer.curves))
        locations = [v['wkb'] for v in self.curve_writer.curves]

        expected_mean_curves = [
            dict(wkb=locations[i],
                 poes=[1. / (1 + i + j)
                       for j in range(0, self.level_nr)])
            for i in range(0, self.location_nr)]

        for i in range(0, self.location_nr):
            self.assertEqual(
                expected_mean_curves[i]['wkb'],
                self.curve_writer.curves[i]['wkb'])
            numpy.testing.assert_allclose(
                expected_mean_curves[i]['poes'],
                self.curve_writer.curves[i]['poes'],
                atol=self.__class__.SIGMA * 10)

    def test_mean_with_weights(self):
        self._setup_with_presets()
        getter = curve_chunks_getter(self.curve_db)

        mean_calculator = persite_result_decorator(
            mean_curves)
        mean_calculator(getter, self.curves_per_location, 0, self.curve_writer)

        expected_mean_curves = [
            numpy.array([0.909707, 0.882379, 0.849248]),
            numpy.array([0.912911, 0.85602, 0.771468])
            ]

        for i in range(0, self.location_nr):
            numpy.testing.assert_allclose(
                expected_mean_curves[i],
                self.curve_writer.curves[i]['poes'])

    def _setup_with_presets(self):
        """
        Setup a curve database with "real" data
        """
        self.location_nr = 2
        self.curves_per_location = 3
        self.level_nr = 3
        self.location_db = [random_location_generator(),
                            random_location_generator()]
        self.curve_db = [
            dict(wkb=self.location_db[0],
                 weight=0.5,
                 poes=numpy.array([9.9996e-01, 9.9962e-01, 9.9674e-01])),
            dict(wkb=self.location_db[0],
                 weight=0.3,
                 poes=numpy.array([6.9909e-01, 6.0859e-01, 5.0328e-01])),
            dict(wkb=self.location_db[0],
                 weight=0.2,
                 poes=numpy.array([1.0000e+00, 9.9996e-01, 9.9947e-01])),
            dict(wkb=self.location_db[1],
                 weight=0.5,
                 poes=numpy.array([9.1873e-01, 8.6697e-01, 7.8992e-01])),
            dict(wkb=self.location_db[1],
                 weight=0.3,
                 poes=numpy.array([8.9556e-01, 8.3045e-01, 7.3646e-01])),
            dict(wkb=self.location_db[1],
                 weight=0.2,
                 poes=numpy.array([9.2439e-01, 8.6700e-01, 7.7785e-01]))]

    def test_quantile(self):
        getter = curve_chunks_getter(self.curve_db)

        quantile_fn = persite_result_decorator(
            quantile_curves)

        quantile_fn(getter, self.curves_per_location, 0, self.curve_writer,
                    quantile=0.5)
        self.assertAlmostEqual(self.location_nr, len(self.curve_writer.curves))

        expected_quantile_curves = [
            dict(wkb=location,
                 poes=[1. / (1 + i + j) for j in range(0, self.level_nr)])
            for i, location in enumerate(self.location_db)]

        for i in range(0, self.location_nr):
            self.assertEqual(
                expected_quantile_curves[i]['wkb'],
                self.curve_writer.curves[i]['wkb'])
            numpy.testing.assert_allclose(
                expected_quantile_curves[i]['poes'],
                self.curve_writer.curves[i]['poes'],
                atol=self.__class__.SIGMA * 10)

    def test_quantile_with_weights(self):
        self._setup_with_presets()
        getter = curve_chunks_getter(self.curve_db)

        quantile_fn = persite_result_decorator(
            quantile_curves)

        quantile_fn(getter, self.curves_per_location, 1, self.curve_writer,
                    quantile=0.5)
        self.assertAlmostEqual(self.location_nr, len(self.curve_writer.curves))

        expected_quantile_curves = [
            numpy.array([0.69909, 0.60859, 0.50328]),
            numpy.array([0.89556, 0.83045, 0.73646])
            ]

        for i in range(0, self.location_nr):
            numpy.testing.assert_allclose(
                expected_quantile_curves[i],
                self.curve_writer.curves[i]['poes'])

    def test_persite_result_decorator(self):
        getter = curve_chunks_getter(self.curve_db)

        func = mock.Mock()

        prefix = "openquake.calculators.hazard.classical.post_processing"
        with mock.patch(prefix + '._fetch_curves') as fc:
            with mock.patch(
                    prefix + '._write_aggregate_results') as war:
                fc.return_value = (1, 2, 3)

                new_func = persite_result_decorator(func)

                a_value = random.random()
                new_func(
                    getter,
                    self.curves_per_location,
                    0,
                    self.curve_writer, ya_arg=a_value)

                self.assertEqual(1, fc.call_count)
                self.assertEqual(1, war.call_count)
                self.assertEqual(1, func.call_count)


class PostProcessorTestCase(unittest.TestCase):
    """
    Tests that the post processing setup the right number of tasks
    """
    def setUp(self):
        self.curves_per_location = 10
        location_nr = 10
        curve_nr = location_nr * self.curves_per_location
        self.chunk_size = 1 + curve_nr / 5

        self.writers = dict(mean_curves=mock.Mock(),
                            quantile_curves=mock.Mock())

        curve_db = _curve_db(location_nr, 1,
                                      self.curves_per_location, 0)

        self.a_chunk_getter = curve_chunks_getter(curve_db[0: self.chunk_size])
        self.task_nr = math.ceil(curve_nr / float(self.chunk_size))
        self.chunk_getters = list(itertools.repeat(
            self.a_chunk_getter, int(self.task_nr)))

        self.curve_finder = mock.Mock()
        self.curve_finder.individual_curve_nr = mock.Mock(
            return_value=curve_nr)

        self.curve_finder.individual_curves_chunks = mock.Mock(
            return_value=self.chunk_getters)

    def test_initialize_both_calculation_with_2imt(self):
        """
        Test that #initialize method has divided properly the main
        task with 2 imts and both mean and quantile calculation
        """

        # Arrange
        calculation = mock.Mock()
        calculation.individual_curves_per_location = mock.Mock(
            return_value=self.curves_per_location)

        calculation.intensity_measure_types_and_levels = {
            'PGA': range(1, 10),
            'SA(10)': range(1, 10)
            }
        calculation.mean_hazard_curves = True
        calculation.quantile_hazard_curves = [0.5, 0.3]
        calculation.should_compute_hazard_curves.return_value = True

        # Act
        tasks, tasks_args = setup_tasks(
            mock.Mock(), calculation, self.curve_finder, self.writers,
            self.chunk_size)

        # Assert
        expected_task_nr = 2 * (1 + 2) * self.task_nr
        self.assertEqual(expected_task_nr, len(tasks))
        self.assertEqual(expected_task_nr, len(tasks_args))

    def test_initialize_one_calculation_with_1imt(self):
        """
        Test that #initialize method has divided properly the main
        task with 1 imt and only mean curves
        """

        # Arrange
        calculation = mock.Mock()
        calculation.individual_curves_per_location = mock.Mock(
            return_value=self.curves_per_location)

        calculation.intensity_measure_types_and_levels = {
            'SA(10)': range(1, 10)
            }
        calculation.mean_hazard_curves = True
        calculation.should_compute_quantile_curves.return_value = None

        # Act
        tasks, tasks_args = setup_tasks(
            mock.Mock(), calculation, self.curve_finder, self.writers,
            self.chunk_size)

        # Assert
        self.assertEqual(self.task_nr, len(tasks))
        self.assertEqual(self.task_nr, len(tasks_args))


def curve_chunks_getter(db):
    """
    Simple curve chunks getter. Returns a function that extracts
    curve fields from a dictionary
    """
    return (lambda field: [curve[field] for curve in db])


class SimpleCurveWriter(object):
    """
    Simple imt-agnostic Curve Writer that stores curves in a list of
    dictionaries.
    """
    def __init__(self):
        self.curves = []
        self.imt = None

    def __exit__(self, *args, **kwargs):
        """
        No action taken. Needed to just implement the aggregate result
        writer protocol
        """
        pass

    def __enter__(self):
        """
        No action taken. Needed to just implement the aggregate result
        writer protocol
        """
        return self

    def add_data(self, location, poes):
        """
        Save a mean/quantile curve
        """
        self.curves.append(dict(wkb=location,
                                poes=poes))


def _curve_db(location_nr, level_nr, curves_per_location, sigma):
    """
    Create a random db of curves stored in a list of dictionaries
    """
    curve_db = []
    location_db = []

    weights = [1.0 for _ in range(0, curves_per_location)]
    weights = [w / sum(weights) for w in weights]

    for i in range(0, location_nr):
        location = random_location_generator()
        # individual curve poes set with a gauss distribution with
        # mean set to [1 / (1 + i + j) for j in level_indexes].
        # So we can easily calculate mean and 0.5 quantile
        location_db.append(location.wkb)
        for j in range(0, curves_per_location):
            poes = []
            for k in range(0, level_nr):
                poe = random.gauss(1.0 / (1 + i + k), sigma)
                poes.append(min(1, poe))
            curve_db.append(
                dict(wkb=location.wkb,
                     weight=weights[j],
                     poes=numpy.array(poes)))
    return curve_db, location_db


def _curve_db_with_weights(location_nr, level_nr,
                                    curves_per_location):
    """
    Setup a curve db with random weights
    """
    curve_db = []
    location_db = []

    weights = [random.random() for _ in range(0, curves_per_location)]
    weights = [w / sum(weights) for w in weights]

    for _ in range(0, location_nr):
        location = random_location_generator()
        location_db.append(location.wkb)
        for j in range(0, curves_per_location):
            poes = []
            for k in range(0, level_nr):
                poes.append(min(1, 1.0 / (1 + k)))
            curve_db.append(
                dict(wkb=location.wkb,
                     weight=weights[j],
                     poes=numpy.array(poes)))
    return curve_db, location_db, weights
