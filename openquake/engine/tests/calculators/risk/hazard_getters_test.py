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
        self.job.is_running = True
        self.job.save()
        calc.pre_execute()

        self.builder = hazard_getters.RiskInitializer(
            self.taxonomy, calc)
        self.builder.init_assocs()

        assocs = models.AssetSite.objects.filter(job=self.job)
        self.assets = models.ExposureData.objects.get_asset_chunk(
            calc.exposure_model, calc.time_event, assocs)
        self.getter = self.getter_class(
            self.imt, self.taxonomy, calc.get_hazard_outputs(), self.assets)

    def test_is_pickleable(self):
        pickle.dumps(self.getter)  # raises an error if not

    def test_call(self):
        # the exposure model in this example has three assets of taxonomy VF
        # called a1, a2 and a3; only a2 and a3 are within the maximum distance
        [a2, a3] = self.assets
        self.assertEqual(self.getter.assets, [a2, a3])
        data = self.getter.get_data()
        numpy.testing.assert_allclose([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]], data)
