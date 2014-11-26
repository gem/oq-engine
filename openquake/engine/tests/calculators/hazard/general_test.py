# -*- coding: utf-8 -*-
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


import unittest
import mock

from openquake.commonlib.valid import SiteParam

from openquake.engine import engine
from openquake.engine.calculators.hazard import general
from openquake.engine.calculators import calculators
from openquake.engine.db import models

from openquake.engine.tests.utils import helpers


class ParseRiskModelsTestCase(unittest.TestCase):
    def test(self):
        # check that if risk models are provided, then the sites
        # and the imls are got from there
        cfg = helpers.get_data_path('classical_job-sd-imt.ini')
        job = engine.job_from_file(cfg, helpers.default_user())
        job.is_running = True
        job.save()

        calc = calculators(job)
        calc.parse_risk_model()

        self.assertEqual(['PGA'],
                         list(calc.hc.intensity_measure_types_and_levels))

        self.assertEqual(3, calc.job.exposuremodel.exposuredata_set.count())

        return job


class InitializeSourcesTestCase(unittest.TestCase):
    # this is a based on a demo with 3 realizations, 2 sources and 2 sites
    @classmethod
    def setUpClass(cls):
        cfg = helpers.get_data_path(
            'calculators/hazard/classical/haz_map_test_job.ini')
        job = helpers.get_job(cfg)
        models.JobStats.objects.create(oq_job=job)
        cls.calc = calculators(job)
        cls.calc.initialize_site_collection()
        num_sites = len(cls.calc.site_collection)
        assert num_sites == 2, num_sites

    def test_filtering_sources(self):
        self.calc.initialize_sources()
        m1, m2, m3 = models.LtSourceModel.objects.filter(
            hazard_calculation=self.calc.job)
        self.assertEqual(
            [m1.get_num_sources(), m2.get_num_sources(), m3.get_num_sources()],
            [1, 1, 1])


class CalculationLimitsTestCase(unittest.TestCase):
    def test_check_limits_classical(self):
        # this is a based on a demo with 3 realizations, 2 sites and 4 rlzs
        cfg = helpers.get_data_path(
            'calculators/hazard/classical/haz_map_test_job.ini')
        job = helpers.get_job(cfg)
        models.JobStats.objects.create(oq_job=job)
        calc = calculators(job)
        input_weight, output_weight = calc.pre_execute()
        self.assertEqual(input_weight, 225)
        self.assertEqual(output_weight, 24)

        calc.max_input_weight = 1
        with self.assertRaises(general.InputWeightLimit):
            calc.check_limits(input_weight, output_weight)

        calc.max_input_weight = 1000
        calc.max_output_weight = 1
        with self.assertRaises(general.OutputWeightLimit):
            calc.check_limits(input_weight, output_weight)

    def test_check_limits_event_based(self):
        # this is a based on a demo with 2 realizations, 5 ses,
        # 2 imt and 121 sites
        cfg = helpers.get_data_path(
            'event_based_hazard/job.ini')
        job = helpers.get_job(cfg)
        models.JobStats.objects.create(oq_job=job)
        calc = calculators(job)
        input_weight, output_weight = calc.pre_execute()
        self.assertEqual(input_weight, 1352.75)
        self.assertAlmostEqual(output_weight, 1210.0)
        # NB: 12.1 = 121 sites * 2 IMT * 2 rlzs * 5 SES * 50/100


class NonEmptyQuantileTestCase(unittest.TestCase):
    # you cannot compute the quantiles if there is only 1 realization
    def test(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        with mock.patch('openquake.engine.logs.LOG.warn') as warn:
            helpers.run_job(cfg, number_of_logic_tree_samples=1,
                            quantile_hazard_curves='0.1 0.2',
                            hazard_maps='', uniform_hazard_spectra='')
        msg = warn.call_args[0][0]
        self.assertEqual(
            msg, 'There is only one realization, the configuration'
            ' parameter quantile_hazard_curves should not be set')


class ClosestSiteModelTestCase(unittest.TestCase):

    def test_closest_site_model(self):
        # This test scenario is the following:
        # Site model data nodes arranged 2 degrees apart (longitudinally) along
        # the same parallel (indicated below by 'd' characters).
        #
        # The sites of interest are located at (-0.0000001, 0) and
        # (0.0000001, 0) (from left to right).
        # Sites of interest are indicated by 's' characters.
        #
        # To illustrate, a super high-tech nethack-style diagram:
        #
        # -1.........0.........1
        #  d        s s        d

        sm1 = SiteParam(
            measured=True, vs30=0.0000001,
            z1pt0=0.0000001, z2pt5=0.0000001, lon=-1, lat=0)
        sm2 = SiteParam(
            measured=False, vs30=0.0000002,
            z1pt0=0.0000002, z2pt5=0.0000002, lon=1, lat=0)

        job = models.OqJob.objects.create(user_name="openquake")
        siteparams = general.SiteModelParams(job, [sm1, sm2])

        res1 = siteparams.get_closest(-0.0000001, 0)
        res2 = siteparams.get_closest(0.0000001, 0)

        self.assertEqual((res1.location.x, res1.location.y),
                         (sm1.lon, sm1.lat))
        self.assertEqual((res2.location.x, res2.location.y),
                         (sm2.lon, sm2.lat))
