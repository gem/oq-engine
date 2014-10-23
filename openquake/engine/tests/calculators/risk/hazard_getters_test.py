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
        models.JobParam.objects.create(
            job=self.job, name='intensity_measure_types',
            value=repr([self.imt]))

        # need to run pre-execute to parse exposure model
        calc = RiskCalculator(self.job)
        self.job.is_running = True
        self.job.save()
        calc.pre_execute()

        self.builder = hazard_getters.RiskInitializer(
            self.taxonomy, calc.rc)
        self.builder.init_assocs()

        assocs = models.AssetSite.objects.filter(job=self.job)
        self.assets = models.ExposureData.objects.get_asset_chunk(
            calc.rc, assocs)
        self.nbytes = self.builder.calc_nbytes()
        self.builder.init_epsilons()
        self.getter = self.getter_class(
            self.imt, self.taxonomy, calc.rc.hazard_outputs(), self.assets)

    def test_nbytes(self):
        self.assertEqual(self.nbytes, 0)

    def test_is_pickleable(self):
        pickle.dumps(self.getter)  # raises an error if not

    def test_call(self):
        # the exposure model in this example has three assets of taxonomy VF
        # called a1, a2 and a3; only a2 and a3 are within the maximum distance
        [a2, a3] = self.assets
        self.assertEqual(self.getter.assets, [a2, a3])
        data = self.getter.get_data()
        numpy.testing.assert_allclose(
            [[(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
             [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)]], data)


class GroundMotionGetterTestCase(HazardCurveGetterTestCase):

    hazard_demo = get_data_path('event_based_hazard/job.ini')
    risk_demo = get_data_path('event_based_risk/job.ini')
    hazard_output_type = 'gmf'
    getter_class = hazard_getters.GroundMotionGetter
    taxonomy = 'RM'

    def test_nbytes(self):
        # 1 asset * 3 ruptures
        self.assertEqual(self.builder.epsilons_shape.values(), [(1, 3)])
        self.assertEqual(self.nbytes, 24)

    def test_call(self):
        # the exposure model in this example has two assets of taxonomy RM
        # (a1 and a3); the asset a3 has no hazard data within the
        # maximum distance, so it is excluded;
        # there is one realization and three ruptures
        a1, = self.assets
        self.assertEqual(self.getter.assets, [a1])
        rupture_ids = self.getter.rupture_ids
        self.assertEqual(len(rupture_ids), 3)

        data = self.getter.get_data()
        numpy.testing.assert_allclose([[0.1, 0.2, 0.3]], data)
        numpy.testing.assert_allclose(
            numpy.array([[0.49671415, -0.1382643, 0.64768854]]),
            self.getter.epsilons)  # shape (1, 3)


class ScenarioTestCase(GroundMotionGetterTestCase):

    hazard_demo = get_data_path('scenario_hazard/job.ini')
    risk_demo = get_data_path('scenario_risk/job.ini')
    hazard_output_type = 'gmf_scenario'
    taxonomy = 'RM'

    def test_nbytes(self):
        # I am not populating the table ses_rupture
        self.assertEqual(len(self.getter.rupture_ids), 0)
        self.assertEqual(self.nbytes, 80)

    def test_call(self):
        # the exposure model in this example has two assets of taxonomy RM
        # (a1 and a3) but the asset a3 has no hazard data within the
        # maximum distance; there are 10 realizations
        a1, = self.assets
        self.assertEqual(self.getter.assets, [a1])
        [hazard] = self.getter.hazards.values()
        self.assertEqual(hazard.values()[0], {0: 0.1, 1: 0.2, 2: 0.3})

        # NB: since I am not populating the table ses_rupture,
        # self.getter.get_data() is empty
