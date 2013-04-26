# Copyright (c) 2010-2013, GEM Foundation.
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
from tests.utils import helpers
import unittest
import cPickle as pickle

from openquake.engine.db import models
from openquake.engine.calculators.risk import hazard_getters
from openquake.engine.calculators.risk.base import RiskCalculator

from tests.utils.helpers import demo_file


class HazardCurveGetterPerAssetTestCase(unittest.TestCase):

    hazard_demo = demo_file('simple_fault_demo_hazard/job.ini')
    risk_demo = demo_file('classical_psha_based_risk/job.ini')
    hazard_output_type = 'curve'
    getter_class = hazard_getters.HazardCurveGetterPerAsset
    taxonomy = 'VF'

    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            self.risk_demo, self.hazard_demo, self.hazard_output_type)

        # need to run pre-execute to parse exposure model
        calc = RiskCalculator(self.job)
        calc.pre_execute()

        self._assets = models.ExposureData.objects.filter(
            exposure_model=self.job.risk_calculation.exposure_model).order_by(
                'asset_ref')

        self.getter = self.getter_class(
            self.ho().id, self.assets(), 500)

    def test_is_pickleable(self):
        pickle.dumps(self.getter)  # raises an error if not

    def ho(self):
        return self.job.risk_calculation.hazard_output.hazardcurve

    def test_call(self):
        assets, values, missing = self.getter("PGA")

        self.assertEqual([a.id for a in self.assets()], [a.id for a in assets])
        self.assertEqual(set(), missing)
        self.assertEqual([[(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
                          [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
                          [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)]], values)

    def assets(self):
        return self._assets.filter(taxonomy=self.taxonomy)

    def test_filter(self):
        self.getter.max_distance = 0.00001  # 1 cm
        assets, values, missing = self.getter("PGA")
        self.assertEqual([], assets)
        self.assertEqual(set([a.id for a in self.assets()]), missing)
        self.assertEqual([], values)


class GroundMotionValuesGetterTestCase(HazardCurveGetterPerAssetTestCase):

    hazard_demo = demo_file('event_based_hazard/job.ini')
    risk_demo = demo_file('event_based_risk/job.ini')
    hazard_output_type = 'gmf'
    getter_class = hazard_getters.GroundMotionValuesGetter
    taxonomy = 'RM'

    def ho(self):
        return self.job.risk_calculation.hazard_output.gmfcollection

    def test_call(self):
        assets, values, missing = self.getter("PGA")

        gmvs = numpy.array(values)[:, 0]

        self.assertEqual([a.id for a in self.assets()], [a.id for a in assets])
        self.assertEqual(set(), missing)
        self.assertEqual([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]], gmvs.tolist())


class GroundMotionScenarioGetterTestCase(HazardCurveGetterPerAssetTestCase):

    hazard_demo = demo_file('scenario_hazard/job.ini')
    risk_demo = demo_file('scenario_risk/job.ini')
    hazard_output_type = 'gmf_scenario'
    getter_class = hazard_getters.GroundMotionScenarioGetter
    taxonomy = 'RM'

    def ho(self):
        return self.job.risk_calculation.hazard_output

    def test_call(self):
        assets, values, missing = self.getter("PGA")

        self.assertEqual([a.id for a in self.assets()], [a.id for a in assets])
        self.assertEqual(set(), missing)
        self.assertEqual([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]], values)
