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

from nose.plugins.attrib import attr
from scipy.stats import mstats

from tests.utils import helpers
from tests.utils.helpers import random_location_generator

from openquake.db import models
from openquake.calculators.hazard.classical import post_processing
from openquake.calculators.hazard.classical.post_processing import (
    setup_tasks, mean_curves, quantile_curves, persite_result_decorator,
    mean_curves_weighted, quantile_curves_weighted,
    hazard_curves_to_hazard_map)

aaae = numpy.testing.assert_array_almost_equal


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

    def test_compute_hazard_map(self):
        curves = [
            [0.8, 0.5, 0.1],
            [0.98, 0.15, 0.05],
            [0.6, 0.5, 0.4],
            [0.1, 0.01, 0.001],
            [0.8, 0.2, 0.1],
        ]
        imls = [0.005, 0.007, 0.0098]
        poe = 0.2

        expected = [[0.0091, 0.00687952, 0.0098, 0.005, 0.007]]

        actual = post_processing.compute_hazard_maps(curves, imls, poe)
        aaae(expected, actual)

    def test_compute_hazard_map_poes_list_of_one(self):
        curves = [
            [0.8, 0.5, 0.1],
            [0.98, 0.15, 0.05],
            [0.6, 0.5, 0.4],
            [0.1, 0.01, 0.001],
            [0.8, 0.2, 0.1],
        ]

        # NOTE(LB): Curves may be passed as a generator or iterator;
        # let's make sure that works, too.
        curves = iter(curves)

        imls = [0.005, 0.007, 0.0098]
        poe = [0.2]

        expected = [[0.0091, 0.00687952, 0.0098, 0.005, 0.007]]

        actual = post_processing.compute_hazard_maps(curves, imls, poe)
        aaae(expected, actual)

    def test_compute_hazard_map_multi_poe(self):
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

        actual = post_processing.compute_hazard_maps(curves, imls, poes)
        aaae(expected, actual)


class HazardMapTaskFuncTestCase(unittest.TestCase):

    MOCK_HAZARD_MAP = numpy.array([
        [0.0098, 0.0084],
        [0.0091, 0.00687952],
    ])

    TEST_POES = [0.1, 0.02]

    @classmethod
    def setUpClass(cls):
        cfg = helpers.get_data_path(
            'calculators/hazard/classical/haz_map_test_job2.ini')
        cls.job = helpers.run_hazard_job(cfg)
        models.JobStats.objects.create(oq_job=cls.job)

    def _test_maps(self, curve, hm_0_1, hm_0_02, lt_rlz=None):
        self.assertEqual(lt_rlz, hm_0_1.lt_realization)
        self.assertEqual(lt_rlz, hm_0_02.lt_realization)

        self.assertEqual(
            curve.investigation_time, hm_0_1.investigation_time)
        self.assertEqual(
            curve.investigation_time, hm_0_02.investigation_time)

        self.assertEqual(curve.imt, hm_0_1.imt)
        self.assertEqual(curve.imt, hm_0_02.imt)

        self.assertEqual(curve.statistics, hm_0_1.statistics)
        self.assertEqual(curve.statistics, hm_0_02.statistics)

        self.assertEqual(curve.quantile, hm_0_1.quantile)
        self.assertEqual(curve.quantile, hm_0_02.quantile)

        self.assertIsNone(hm_0_1.sa_period)
        self.assertIsNone(hm_0_02.sa_period)

        self.assertIsNone(hm_0_1.sa_damping)
        self.assertIsNone(hm_0_02.sa_damping)

        self.assertEqual(0.1, hm_0_1.poe)
        self.assertEqual(0.02, hm_0_02.poe)

        aaae([0.0, 0.001], hm_0_1.lons)
        aaae([0.0, 0.001], hm_0_1.lats)
        # our mock hazard map results:
        aaae([0.0098, 0.0084], hm_0_1.imls)

        aaae([0.0, 0.001], hm_0_02.lons)
        aaae([0.0, 0.001], hm_0_02.lats)
        # our mock hazard map results:
        aaae([0.0091, 0.00687952], hm_0_02.imls)

    def test_hazard_curves_to_hazard_map_logic_tree(self):
        lt_haz_curves = models.HazardCurve.objects.filter(
            output__oq_job=self.job,
            lt_realization__isnull=False)

        with mock.patch('%s.compute_hazard_maps' % MOCK_PREFIX) as compute:
            compute.return_value = self.MOCK_HAZARD_MAP

            for curve in lt_haz_curves:
                hazard_curves_to_hazard_map(
                    self.job.id, curve.id, self.TEST_POES)

                lt_rlz = curve.lt_realization
                # There should be two maps: 1 for each PoE
                hm_0_1, hm_0_02 = models.HazardMap.objects.filter(
                    output__oq_job=self.job,
                    lt_realization=lt_rlz).order_by('-poe')

                self._test_maps(curve, hm_0_1, hm_0_02, lt_rlz=lt_rlz)

    def test_hazard_curves_to_hazard_map_mean(self):
        mean_haz_curves = models.HazardCurve.objects.filter(
            output__oq_job=self.job,
            statistics='mean')

        with mock.patch('%s.compute_hazard_maps' % MOCK_PREFIX) as compute:
            compute.return_value = self.MOCK_HAZARD_MAP

            for curve in mean_haz_curves:
                hazard_curves_to_hazard_map(
                    self.job.id, curve.id, self.TEST_POES)

                hm_0_1, hm_0_02 = models.HazardMap.objects.filter(
                    output__oq_job=self.job,
                    statistics='mean').order_by('-poe')

                self._test_maps(curve, hm_0_1, hm_0_02)

    def test_hazard_curves_to_hazard_map_quantile(self):
        with mock.patch('%s.compute_hazard_maps' % MOCK_PREFIX) as compute:
            compute.return_value = self.MOCK_HAZARD_MAP

            for quantile in (0.1, 0.9):
                quantile_haz_curves = models.HazardCurve.objects.filter(
                    output__oq_job=self.job,
                    statistics='quantile',
                    quantile=quantile)

                for curve in quantile_haz_curves:
                    hazard_curves_to_hazard_map(
                        self.job.id, curve.id, self.TEST_POES)

                    hm_0_1, hm_0_02 = models.HazardMap.objects.filter(
                        output__oq_job=self.job,
                        statistics='quantile',
                        quantile=quantile).order_by('-poe')

                    self._test_maps(curve, hm_0_1, hm_0_02)


class Bug1086719TestCase(unittest.TestCase):
    """
    Tests for bug https://bugs.launchpad.net/openquake/+bug/1086719.

    Here's a brief summary of the bug:

    With certain calculation parameters, hazard map creation was causing
    calculations to crash. The issue was isolated to an uncommitted
    transaction.
    """

    @attr('slow')
    def test(self):
        # The bug can be reproduced with any hazard calculation profile which
        # the following parameters set:
        #
        # * number_of_logic_tree_samples = 1
        # * mean_hazard_curves = false
        # * quantile_hazard_curves =
        # * poes_hazard_maps = at least one PoE
        cfg = helpers.get_data_path(
            'calculators/hazard/classical/haz_map_1rlz_no_stats.ini'
        )
        retcode = helpers.run_hazard_job_sp(cfg, silence=True)
        self.assertEqual(0, retcode)


class MeanCurveTestCase(unittest.TestCase):

    def test_compute_mean_curve(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]

        expected_mean_curve = numpy.array([0.83, 0.67333333, 0.54333333, 0.17])
        numpy.testing.assert_allclose(
            expected_mean_curve, post_processing.compute_mean_curve(curves))

    def test_compute_mean_curve_weighted(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = [0.5, 0.3, 0.2]

        expected_mean_curve = numpy.array([0.885, 0.735, 0.586, 0.213])
        numpy.testing.assert_allclose(
            expected_mean_curve,
            post_processing.compute_mean_curve(curves, weights=weights))

    def test_compute_mean_curve_weights_None(self):
        # If all weight values are None, ignore the weights altogether
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = [None, None, None]

        expected_mean_curve = numpy.array([0.83, 0.67333333, 0.54333333, 0.17])
        numpy.testing.assert_allclose(
            expected_mean_curve,
            post_processing.compute_mean_curve(curves, weights=weights))

    def test_compute_mean_curve_invalid_weights(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = [0.6, None, 0.4]

        self.assertRaises(
            ValueError, post_processing.compute_mean_curve, curves, weights
        )


class QuantileCurveTestCase(unittest.TestCase):

    def test_compute_quantile_curve(self):
        expected_curve = numpy.array([
            9.9178000e-01, 9.8892000e-01, 9.6903000e-01, 9.4030000e-01,
            8.8405000e-01, 7.8782000e-01, 6.4897250e-01, 4.8284250e-01,
            3.4531500e-01, 3.2337000e-01, 1.8880500e-01, 9.5574000e-02,
            4.3707250e-02, 1.9643000e-02, 8.1923000e-03, 2.9157000e-03,
            7.9955000e-04, 1.5233000e-04, 1.5582000e-05])

        quantile = 0.75

        curves = [
            [9.8161000e-01, 9.7837000e-01, 9.5579000e-01, 9.2555000e-01,
             8.7052000e-01, 7.8214000e-01, 6.5708000e-01, 5.0526000e-01,
             3.7044000e-01, 3.4740000e-01, 2.0502000e-01, 1.0506000e-01,
             4.6531000e-02, 1.7548000e-02, 5.4791000e-03, 1.3377000e-03,
             2.2489000e-04, 2.2345000e-05, 4.2696000e-07],
            [9.7309000e-01, 9.6857000e-01, 9.3853000e-01, 9.0089000e-01,
             8.3673000e-01, 7.4057000e-01, 6.1272000e-01, 4.6467000e-01,
             3.3694000e-01, 3.1536000e-01, 1.8340000e-01, 9.2412000e-02,
             4.0202000e-02, 1.4900000e-02, 4.5924000e-03, 1.1126000e-03,
             1.8647000e-04, 1.8882000e-05, 4.7123000e-07],
            [9.9178000e-01, 9.8892000e-01, 9.6903000e-01, 9.4030000e-01,
             8.8405000e-01, 7.8782000e-01, 6.4627000e-01, 4.7537000e-01,
             3.3168000e-01, 3.0827000e-01, 1.7279000e-01, 8.8360000e-02,
             4.2766000e-02, 1.9643000e-02, 8.1923000e-03, 2.9157000e-03,
             7.9955000e-04, 1.5233000e-04, 1.5582000e-05],
            [9.8885000e-01, 9.8505000e-01, 9.5972000e-01, 9.2494000e-01,
             8.6030000e-01, 7.5574000e-01, 6.1009000e-01, 4.4217000e-01,
             3.0543000e-01, 2.8345000e-01, 1.5760000e-01, 8.0225000e-02,
             3.8681000e-02, 1.7637000e-02, 7.2685000e-03, 2.5474000e-03,
             6.8347000e-04, 1.2596000e-04, 1.2853000e-05],
            [9.9178000e-01, 9.8892000e-01, 9.6903000e-01, 9.4030000e-01,
             8.8405000e-01, 7.8782000e-01, 6.4627000e-01, 4.7537000e-01,
             3.3168000e-01, 3.0827000e-01, 1.7279000e-01, 8.8360000e-02,
             4.2766000e-02, 1.9643000e-02, 8.1923000e-03, 2.9157000e-03,
             7.9955000e-04, 1.5233000e-04, 1.5582000e-05],
        ]
        actual_curve = post_processing.compute_quantile_curve(curves, quantile)

        # TODO(LB): Check with our hazard experts to see if this is reasonable
        # tolerance. Better yet, get a fresh set of test data. (This test data
        # was just copied verbatim from from some old tests in
        # `tests/hazard_test.py`.
        numpy.testing.assert_allclose(expected_curve, actual_curve, atol=0.005)

        # Since this implementation is an optimized but equivalent version of
        # scipy's `mquantiles`, compare algorithms just to prove they are the
        # same:
        scipy_curve = mstats.mquantiles(curves, prob=quantile, axis=0)[0]
        numpy.testing.assert_allclose(scipy_curve, actual_curve)

    def test_compute_weighted_quantile_curve_case1(self):
        expected_curve = numpy.array([0.69909, 0.60859, 0.50328])

        quantile = 0.3

        curves = [
            [9.9996e-01, 9.9962e-01, 9.9674e-01],
            [6.9909e-01, 6.0859e-01, 5.0328e-01],
            [1.0000e+00, 9.9996e-01, 9.9947e-01],
        ]
        weights = [0.5, 0.3, 0.2]

        actual_curve = post_processing.compute_weighted_quantile_curve(
            curves, weights, quantile)

        numpy.testing.assert_allclose(expected_curve, actual_curve)

    def test_compute_weighted_quantile_curve_case2(self):
        expected_curve = numpy.array([0.89556, 0.83045, 0.73646])

        quantile = 0.3

        curves = [
            [9.2439e-01, 8.6700e-01, 7.7785e-01],
            [8.9556e-01, 8.3045e-01, 7.3646e-01],
            [9.1873e-01, 8.6697e-01, 7.8992e-01],
        ]
        weights = [0.2, 0.3, 0.5]

        actual_curve = post_processing.compute_weighted_quantile_curve(
            curves, weights, quantile)

        numpy.testing.assert_allclose(expected_curve, actual_curve)
