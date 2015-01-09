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

import mock
import numpy
import unittest

from nose.plugins.attrib import attr

from openquake.engine.tests.utils import helpers

from openquake.engine.db import models
from openquake.engine.calculators.hazard import (
    post_processing as post_proc)


aaae = numpy.testing.assert_array_almost_equal


# package prefix used for mock.patching
MOCK_PREFIX = "openquake.commonlib.calculators.calc"


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
