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

import decimal
import itertools
import math
import mock
import numpy
import random
import unittest

from tests.utils.helpers import random_location_generator

from openquake.calculators.hazard.classical.post_processing import (
    setup_tasks, mean_curves, quantile_curves, persite_result_decorator,
    mean_curves_weighted, quantile_curves_weighted, compute_hazard_map)


# package prefix used for mock.patching
MOCK_PREFIX = "openquake.calculators.hazard.classical.post_processing"


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
        chunk = curve_chunks_getter(
            self.curve_db, self.location_db, self.curves_per_location)

        mean_fn = persite_result_decorator(mean_curves)

        mean_fn(chunk, self.curve_writer, False)

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

    def test_quantile(self):
        chunk = curve_chunks_getter(
            self.curve_db, self.location_db, self.curves_per_location)

        quantile_fn = persite_result_decorator(quantile_curves)

        quantile_fn(chunk, self.curve_writer, False, quantile=0.5)
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

    def test_persite_result_decorator(self):
        chunk = curve_chunks_getter(
            self.curve_db, self.location_db, self.curves_per_location)

        func = mock.Mock()

        with mock.patch(MOCK_PREFIX + '._fetch_curves') as fc:
            with mock.patch(
                    MOCK_PREFIX + '._write_aggregate_results') as war:
                fc.return_value = (1, 2, 3)

                new_func = persite_result_decorator(func)

                a_value = random.random()
                new_func(chunk, self.curve_writer, True, ya_arg=a_value)

                self.assertEqual(1, fc.call_count)
                self.assertEqual(1, war.call_count)
                self.assertEqual(1, func.call_count)


class PostProcessingWithWeight(unittest.TestCase):
    """
    Tests the calculation when full path enumeration occurs and
    weights should be considered
    """
    def setUp(self):
        """
        Setup a curve database with presets data
        """
        self.location_nr = 2
        self.curves_per_location = 3
        self.level_nr = 3
        self.location_db = [random_location_generator().wkb,
                            random_location_generator().wkb]
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
        self.curve_writer = SimpleCurveWriter()

    def test_mean_with_weights(self):
        chunk = curve_chunks_getter(
            self.curve_db, self.location_db, self.curves_per_location)

        mean_fn = persite_result_decorator(mean_curves_weighted)
        mean_fn(chunk, self.curve_writer, True)

        expected_mean_curves = [
            numpy.array([0.909707, 0.882379, 0.849248]),
            numpy.array([0.912911, 0.85602, 0.771468])]

        for i in range(0, self.location_nr):
            numpy.testing.assert_allclose(
                expected_mean_curves[i],
                self.curve_writer.curves[i]['poes'])

    def test_quantile_with_weights(self):
        chunk = curve_chunks_getter(
            self.curve_db, self.location_db, self.curves_per_location)

        quantile_fn = persite_result_decorator(quantile_curves_weighted)

        quantile_fn(chunk, self.curve_writer, True, quantile=0.3)
        self.assertAlmostEqual(self.location_nr, len(self.curve_writer.curves))

        expected_quantile_curves = [
            numpy.array([0.69909, 0.60859, 0.50328]),
            numpy.array([0.89556, 0.83045, 0.73646])
            ]

        for i in range(0, self.location_nr):
            numpy.testing.assert_allclose(
                expected_quantile_curves[i],
                self.curve_writer.curves[i]['poes'])

    def test_weighted_quantile_with_decimal_weights(self):
        # NOTE(LB): This is a test for a bug I found.
        # In the case of end-branch enumeration with _more_ than 1 branch,
        # numpy.interp (used in `quantile_curves_weighted`) cannot handle the
        # `weights` input properly. `weights` is passed as a list of
        # `decimal.Decimal` types. Numpy throws back this error:
        # TypeError: array cannot be safely cast to required type
        # This doesn't appear to be a problem when there is only a single end
        # branch in the logic tree (and so the single weight is
        # decimal.Decimal(1.0)).
        input_curves = numpy.array([
            [[0.99996, 0.99962, 0.99674],
            [0.91873, 0.86697, 0.78992]],

            [[0.69909, 0.60859, 0.50328],
            [0.89556, 0.83045, 0.73646]],

            [[1.0, 0.99996, 0.99947],
            [0.92439, 0.867, 0.77785]]
        ])

        expected_curves = [
            numpy.array([0.69909, 0.60859, 0.50328]),
            numpy.array([0.89556, 0.83045, 0.73646])
        ]

        weights = [decimal.Decimal(x) for x in (0.5, 0.3, 0.2)]
        quantile = 0.3

        actual_curves = quantile_curves_weighted(
            input_curves, weights, quantile)

        numpy.testing.assert_array_almost_equal(expected_curves, actual_curves)


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

        curve_db, location_db = _curve_db(location_nr, 1,
                                          self.curves_per_location, 0)

        self.a_chunk_getter = curve_chunks_getter(
            curve_db[0: self.chunk_size], location_db,
            self.curves_per_location)
        self.task_nr = math.ceil(curve_nr / float(self.chunk_size))
        self.chunk_getters = list(itertools.repeat(
            self.a_chunk_getter, int(self.task_nr)))

        self.curve_finder = mock.Mock()
        self.curve_finder.individual_curve_nr = mock.Mock(
            return_value=curve_nr)

        self.curve_finder.individual_curves_chunks = mock.Mock(
            return_value=self.chunk_getters)

    def test_setup_tasks_with_2imt(self):
        """
        setup_tasks should creat tasks for 2 imt and for mean and
        quantile calculation
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
        tasks = setup_tasks(
            mock.Mock(), calculation, self.curve_finder, self.writers,
            self.chunk_size)

        # Assert
        self.assertEqual(30, len(tasks))
        self.assertEqual(2, self.writers['mean_curves'].call_count)
        self.assertEqual(4, self.writers['quantile_curves'].call_count)

    def test_setup_tasks_with_1imt(self):
        """
        setup_tasks should create tasks for 1 imt and mean curves
        calculation
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
        tasks = setup_tasks(
            mock.Mock(), calculation, self.curve_finder, self.writers,
            self.chunk_size)

        # Assert
        self.assertEqual(5, len(tasks))
        self.assertEqual(
            1, self.writers['mean_curves'].call_count)
        self.assertEqual(
            0, self.writers['quantile_curves'].call_count)


def curve_chunks_getter(curve_db, location_db, curves_per_location):
    """
    A simple chunks_getter that returns all the curves into the db
    """
    return SimpleCurveFinder(curve_db, location_db, curves_per_location)


class SimpleCurveFinder(object):
    """
    A simple object that implements the curve finder protocol needed
    by the post_processing module
    """
    def __init__(self, curve_db, location_db, curves_per_location):
        self.curve_db = curve_db
        self.locations = location_db
        self.curves_per_location = curves_per_location
        self.poes = [c['poes'] for c in curve_db]
        self.weights = [c['weight'] for c in curve_db][0:curves_per_location]


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


class HazardMapsTestCase(unittest.TestCase):
    pass

    def test_compute_hazard_map(self):
        aaae = numpy.testing.assert_array_almost_equal

        curves = [
            [0.8, 0.5, 0.1],
            [0.98, 0.15, 0.05],
            [0.6, 0.5, 0.4],
            [0.1, 0.01, 0.001],
            [0.8, 0.2, 0.1],
        ]
        imls = [0.005, 0.007, 0.0098]
        poe = 0.2

        expected = [0.0091, 0.00687952, 0.0098, 0.005, 0.007]

        actual = compute_hazard_map(curves, imls, poe)
        aaae(expected, actual)

    def test_compute_hazard_map_poes_list_of_one(self):
        aaae = numpy.testing.assert_array_almost_equal

        curves = [
            [0.8, 0.5, 0.1],
            [0.98, 0.15, 0.05],
            [0.6, 0.5, 0.4],
            [0.1, 0.01, 0.001],
            [0.8, 0.2, 0.1],
        ]
        imls = [0.005, 0.007, 0.0098]
        poe = [0.2]

        expected = [0.0091, 0.00687952, 0.0098, 0.005, 0.007]

        actual = compute_hazard_map(curves, imls, poe)
        aaae(expected, actual)


    def test_compute_hazard_map_multi_poe(self):
        aaae = numpy.testing.assert_array_almost_equal

        curves = [
            [0.8, 0.5, 0.1],
            [0.98, 0.15, 0.05],
            [0.6, 0.5, 0.4],
            [0.1, 0.01, 0.001],
            [0.8, 0.2, 0.1],
        ]
        imls = [0.005, 0.007, 0.0098]
        poes = [0.1, 0.2]

        expected = [
            [0.0098, 0.0084, 0.0098, 0.005, 0.0098],
            [0.0091, 0.00687952, 0.0098, 0.005, 0.007],
        ]

        actual = compute_hazard_map(curves, imls, poes)
        aaae(expected, actual)
