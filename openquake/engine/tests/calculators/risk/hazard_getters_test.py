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


import numpy
from openquake.engine.tests.utils import helpers
import unittest
import cPickle as pickle

from openquake.engine.db import models
from openquake.engine.calculators.risk import hazard_getters
from openquake.engine.calculators.risk.base import RiskCalculator

from openquake.engine.tests.utils.helpers import get_data_path


class HazardCurveGetterTestCase(unittest.TestCase):

    hazard_demo = get_data_path('simple_fault_demo_hazard/job.ini')
    risk_demo = get_data_path('classical_psha_based_risk/job.ini')
    hazard_output_type = 'curve'
    getter_class = hazard_getters.HazardCurveGetter
    taxonomy = 'VF'
    imt = 'PGA'

    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            self.risk_demo, self.hazard_demo, self.hazard_output_type)

        # need to run pre-execute to parse exposure model
        calc = RiskCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)
        self.job.is_running = True
        self.job.save()
        calc.pre_execute()

        self.builder = hazard_getters.GetterBuilder(
            self.taxonomy, self.job.risk_calculation)

        self.assets = models.ExposureData.objects.filter(
            exposure_model=self.job.risk_calculation.exposure_model).order_by(
            'asset_ref').filter(taxonomy=self.taxonomy)

        ho = self.job.risk_calculation.hazard_output
        self.nbytes = self.builder.calc_nbytes([ho])
        [self.getter] = self.builder.make_getters(
            self.getter_class, [ho], self.assets)

    def test_nbytes(self):
        self.assertEqual(self.nbytes, 0)

    def test_is_pickleable(self):
        pickle.dumps(self.getter)  # raises an error if not

    def test_call(self):
        # the exposure model in this example has three assets of taxonomy VF
        # called a1, a2 and a3; only a2 and a3 are within the maximum distance
        [a1, a2, a3] = self.assets
        self.assertEqual(self.getter.assets, [a2, a3])

        values = self.getter.get_data(self.imt)
        numpy.testing.assert_allclose(
            [[(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
             [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)]], values)


class GroundMotionValuesGetterTestCase(HazardCurveGetterTestCase):

    hazard_demo = get_data_path('event_based_hazard/job.ini')
    risk_demo = get_data_path('event_based_risk/job.ini')
    hazard_output_type = 'gmf'
    getter_class = hazard_getters.GroundMotionValuesGetter
    taxonomy = 'RM'

    def test_nbytes(self):
        # 1 asset * 3 ruptures
        self.assertEqual(self.builder.epsilons_shape.values(), [(1, 3)])
        self.assertEqual(self.nbytes, 24)

    def test_call(self):
        # the exposure model in this example has two assets of taxonomy RM
        # (a1 and a3); the asset a3 has no hazard data within the
        # maximum distance; there is one realization and three ruptures
        a1, a3 = self.assets
        self.assertEqual(self.getter.assets, [a1])
        rupture_ids = self.getter.rupture_ids
        self.assertEqual(len(rupture_ids), 3)
        [gmvs] = self.getter.get_data(self.imt)
        numpy.testing.assert_allclose([0.1, 0.2, 0.3], gmvs)
        numpy.testing.assert_allclose(
            numpy.array([[0.49671415, -0.1382643, 0.64768854]]),
            self.getter.get_epsilons())  # shape (1, 3)


class ScenarioTestCase(GroundMotionValuesGetterTestCase):

    hazard_demo = get_data_path('scenario_hazard/job.ini')
    risk_demo = get_data_path('scenario_risk/job.ini')
    hazard_output_type = 'gmf_scenario'
    taxonomy = 'RM'

    def test_nbytes(self):
        # 10 realizations * 1 asset
        self.assertEqual(len(self.getter.rupture_ids), 10)
        self.assertEqual(self.nbytes, 80)

    def test_call(self):
        # the exposure model in this example has two assets of taxonomy RM
        # (a1 and a3) but the asset a3 has no hazard data within the
        # maximum distance; there are 10 realizations
        a1, a3 = self.assets
        self.assertEqual(self.getter.assets, [a1])

        [gmvs] = self.getter.get_data(self.imt)
        expected = [0.1, 0.2, 0.3] + [0] * 7
        numpy.testing.assert_allclose(expected, gmvs)
