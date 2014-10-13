# -*- coding: utf-8 -*-
# unittest.TestCase base class does not honor the following coding
# convention
# pylint: disable=C0103,R0904
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

# Copyright (c) 2010-2014, GEM Foundation.
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
import mock
import numpy
import unittest

from nose.plugins.attrib import attr
from scipy.stats import mstats

from openquake.engine.tests.utils import helpers

from openquake.engine.db import models
from openquake.engine.calculators import post_processing
from openquake.engine.calculators.hazard import (
    post_processing as post_proc)


aaae = numpy.testing.assert_array_almost_equal


# package prefix used for mock.patching
MOCK_PREFIX = "openquake.engine.calculators.hazard.post_processing"


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

        expected = [[0.00847798, 0.00664814, 0.0098, 0, 0.007]]
        actual = post_proc.compute_hazard_maps(curves, imls, poe)
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
        expected = [[0.00847798, 0.00664814, 0.0098, 0, 0.007]]
        actual = post_proc.compute_hazard_maps(curves, imls, poe)
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
            [0.0098, 0.00792555, 0.0098, 0.005,  0.0098],
            [0.00847798, 0.00664814, 0.0098, 0, 0.007]
        ]
        actual = post_proc.compute_hazard_maps(curves, imls, poes)
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
        cls.job = helpers.run_job(cfg).job
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

    @attr('slow')
    def test_hazard_curves_to_hazard_map_logic_tree(self):
        lt_haz_curves = models.HazardCurve.objects.filter(
            output__oq_job=self.job,
            imt__isnull=False,
            lt_realization__isnull=False)

        with mock.patch('%s.compute_hazard_maps' % MOCK_PREFIX) as compute:
            compute.return_value = self.MOCK_HAZARD_MAP

            for curve in lt_haz_curves:
                post_proc.hazard_curves_to_hazard_map.task_func(
                    self.job.id, [curve], self.TEST_POES)

                lt_rlz = curve.lt_realization
                # There should be two maps: 1 for each PoE
                hm_0_1, hm_0_02 = models.HazardMap.objects.filter(
                    output__oq_job=self.job,
                    lt_realization=lt_rlz).order_by('-poe')

                self._test_maps(curve, hm_0_1, hm_0_02, lt_rlz=lt_rlz)

    @attr('slow')
    def test_hazard_curves_to_hazard_map_mean(self):
        mean_haz_curves = models.HazardCurve.objects.filter(
            output__oq_job=self.job,
            imt__isnull=False,
            statistics='mean')

        with mock.patch('%s.compute_hazard_maps' % MOCK_PREFIX) as compute:
            compute.return_value = self.MOCK_HAZARD_MAP

            for curve in mean_haz_curves:
                post_proc.hazard_curves_to_hazard_map.task_func(
                    self.job.id, [curve], self.TEST_POES)

                hm_0_1, hm_0_02 = models.HazardMap.objects.filter(
                    output__oq_job=self.job,
                    statistics='mean').order_by('-poe')

                self._test_maps(curve, hm_0_1, hm_0_02)

    @attr('slow')
    def test_hazard_curves_to_hazard_map_quantile(self):
        with mock.patch('%s.compute_hazard_maps' % MOCK_PREFIX) as compute:
            compute.return_value = self.MOCK_HAZARD_MAP

            for quantile in (0.1, 0.9):
                quantile_haz_curves = models.HazardCurve.objects.filter(
                    output__oq_job=self.job,
                    imt__isnull=False,
                    statistics='quantile',
                    quantile=quantile)

                for curve in quantile_haz_curves:
                    post_proc.hazard_curves_to_hazard_map.task_func(
                        self.job.id, [curve], self.TEST_POES)

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
        # * poes = at least one PoE
        cfg = helpers.get_data_path(
            'calculators/hazard/classical/haz_map_1rlz_no_stats.ini'
        )
        job = helpers.run_job(cfg).job
        self.assertEqual(job.status, 'complete')


class MeanCurveTestCase(unittest.TestCase):

    def test_compute_mean_curve(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]

        expected_mean_curve = numpy.array([0.83, 0.67333333, 0.54333333, 0.17])
        numpy.testing.assert_allclose(
            expected_mean_curve, post_processing.mean_curve(curves))

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
            post_processing.mean_curve(curves, weights=weights))

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
            post_processing.mean_curve(curves, weights=weights))

    def test_compute_mean_curve_invalid_weights(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = [0.6, None, 0.4]

        self.assertRaises(
            ValueError, post_processing.mean_curve, curves, weights
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
        actual_curve = post_processing.quantile_curve(curves, quantile)

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

        actual_curve = post_processing.weighted_quantile_curve(
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

        actual_curve = post_processing.weighted_quantile_curve(
            curves, weights, quantile)

        numpy.testing.assert_allclose(expected_curve, actual_curve)

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
        # This test ensures that `weighted_quantile_curve` works when weights
        # are passed as `Decimal` types.
        expected_curve = numpy.array([0.89556, 0.83045, 0.73646])

        quantile = 0.3

        curves = [
            [9.2439e-01, 8.6700e-01, 7.7785e-01],
            [8.9556e-01, 8.3045e-01, 7.3646e-01],
            [9.1873e-01, 8.6697e-01, 7.8992e-01],
        ]
        weights = [decimal.Decimal(x) for x in ('0.2', '0.3', '0.5')]

        actual_curve = post_processing.weighted_quantile_curve(
            curves, weights, quantile)

        numpy.testing.assert_allclose(expected_curve, actual_curve)


class UHSTestCase(unittest.TestCase):

    def setUp(self):
        self.lons = [0.0, 1.0, 2.0]
        self.lats = [6.0, 7.0, 8.0]
        map1_imls = [0.01, 0.02, 0.03]
        map2_imls = [0.05, 0.10, 0.15]
        map3_imls = [1.25, 2.17828, 3.14]

        self.map1 = models.HazardMap(
            imt='PGA',
            poe=0.1,
            lons=list(self.lons),
            lats=list(self.lats),
            imls=map1_imls,
        )

        self.map2 = models.HazardMap(
            imt='SA',
            sa_period=0.025,
            poe=0.1,
            lons=list(self.lons),
            lats=list(self.lats),
            imls=map2_imls,
        )

        self.map3 = models.HazardMap(
            imt='SA',
            sa_period=0.1,
            poe=0.1,
            lons=list(self.lons),
            lats=list(self.lats),
            imls=map3_imls,
        )

        # an invalid map type for calculating UHS
        self.map_pgv = models.HazardMap(
            imt='PGV',
            poe=0.1,
            lons=list(self.lons),
            lats=list(self.lats),
            imls=[0.0, 0.0, 0.0],
        )

    def test_make_uhs(self):
        # intentionally out of order to set sorting
        # the PGV map will get filtered out/ignored
        maps = [self.map2, self.map_pgv, self.map3, self.map1]

        # they need to be sorted in ascending order by SA period
        # PGA is considered to be SA period = 0.0
        expected = {
            'periods': [0.0, 0.025, 0.1],  # again, 0.0 is PGA
            'uh_spectra': [
                # triples of (lon, lat, [imls])
                (0.0, 6.0, (0.01, 0.05, 1.25)),
                (1.0, 7.0, (0.02, 0.10, 2.17828)),
                (2.0, 8.0, (0.030, 0.15, 3.14)),
            ]
        }

        actual = post_proc.make_uhs(maps)

        self.assertEqual(expected, actual)
