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

from openquake.engine import engine
from openquake.engine.calculators.hazard import general
from openquake.engine.utils import get_calculator_class
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

        haz_calc = job.hazard_calculation
        calc = get_calculator_class('hazard', haz_calc.calculation_mode)(job)
        calc.parse_risk_models()

        self.assertEqual(['PGA'], calc.hc.get_imts())

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
        hc = job.hazard_calculation
        cls.calc = get_calculator_class('hazard', hc.calculation_mode)(job)
        cls.calc.store_sites()
        assert len(hc.site_collection) == 2, len(hc.site_collection)

    def test_filtering_sources(self):
        self.calc.initialize_sources()
        m1, m2, m3 = models.LtSourceModel.objects.filter(
            hazard_calculation=self.calc.job)
        self.assertEqual(
            [m1.get_num_sources(), m2.get_num_sources(), m3.get_num_sources()],
            [2, 2, 2])
        self.calc.process_sources()
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
        hc = job.hazard_calculation
        calc = get_calculator_class('hazard', hc.calculation_mode)(job)
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
        hc = job.hazard_calculation
        calc = get_calculator_class('hazard', hc.calculation_mode)(job)
        input_weight, output_weight = calc.pre_execute()
        self.assertEqual(input_weight, 1352.75)
        self.assertAlmostEqual(output_weight, 12.1)
        # NB: 12.1 = 121 sites * 2 IMT * 2 rlzs * 5 SES * 50/10000 years


class NonEmptyQuantileTestCase(unittest.TestCase):
    # you cannot compute the quantiles if there is only 1 realization
    def test(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        with mock.patch('openquake.engine.logs.LOG.warn') as warn:
            helpers.run_job(cfg, number_of_logic_tree_samples=1,
                            quantile_hazard_curves='0.1 0.2',
                            hazard_maps=None, uniform_hazard_spectra=None)
        msg = warn.call_args[0][0]
        self.assertEqual(
            msg, 'There is only one realization, the configuration'
            ' parameter quantile_hazard_curves should not be set')
