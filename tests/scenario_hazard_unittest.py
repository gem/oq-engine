# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
This module tests the hazard side of the scenario
event based job.
"""

import math
import unittest

from tests.utils import helpers
from tests.utils.helpers import patch

from openquake import engine
from openquake import java
from openquake import kvs
from openquake import shapes
from openquake.engine import JobContext
from openquake.calculators.hazard.scenario import core as scenario

SCENARIO_SMOKE_TEST = helpers.testdata_path("scenario/config.gem")
NUMBER_OF_CALC_KEY = "NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"


def compute_ground_motion_field(self, _random_generator):
    """Stubbed version of the method that computes the ground motion
    field calling java stuff."""

    hashmap = java.jclass("HashMap")()

    for site in self.job_ctxt.sites_to_compute():
        location = java.jclass("Location")(site.latitude, site.longitude)
        site = java.jclass("Site")(location)
        hashmap.put(site, 0.5)

    return hashmap


class ScenarioHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the Scenario Hazard engine.
    """

    @classmethod
    def setUpClass(cls):
        cls.kvs_client = kvs.get_client()

    def setUp(self):
        kvs.get_client().flushall()

        base_path = helpers.testdata_path("scenario")
        job = engine.prepare_job()
        self.job_profile, self.params, self.sections = (
            engine.import_job_profile(SCENARIO_SMOKE_TEST, job))
        self.job_ctxt = JobContext(
            self.params, job.id, sections=self.sections,
            base_path=base_path, oq_job_profile=self.job_profile,
            oq_job=job)

        self.job_ctxt.params[NUMBER_OF_CALC_KEY] = "1"

        self.job_ctxt.params['SERIALIZE_RESULTS_TO'] = 'xml'

        # saving the default java implementation
        self.default = (
            scenario.ScenarioHazardCalculator.compute_ground_motion_field)

        self.grid = self.job_ctxt.region.grid

        self.job_ctxt.to_kvs()

    def tearDown(self):
        # restoring the default java implementation
        scenario.ScenarioHazardCalculator.compute_ground_motion_field = \
            self.default

    def test_multiple_computations_are_triggered(self):
        """The hazard subsystem is able to trigger multiple computations.

        Depending on the value specified by the user in the
        NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS key, the system
        calls the computation of the values for the entire region
        multiple times.
        """

        self.job_ctxt.params[NUMBER_OF_CALC_KEY] = "3"
        self.job_profile.gmf_calculation_number = 3
        self.job_profile.save()

        calculator = scenario.ScenarioHazardCalculator(self.job_ctxt)

        with patch('openquake.calculators.hazard.scenario.core'
                   '.ScenarioHazardCalculator'
                   '.compute_ground_motion_field') as compute_gmf_mock:
            # the return value needs to be a Java HashMap
            compute_gmf_mock.return_value = java.jclass('HashMap')()
            calculator.execute()

        self.assertEquals(3, compute_gmf_mock.call_count)

    def test_transforms_a_java_gmf_to_dict(self):
        location1 = java.jclass("Location")(1.0, 2.0)
        location2 = java.jclass("Location")(1.1, 2.1)
        location3 = java.jclass("Location")(1.2, 2.2)

        site1 = java.jclass("Site")(location1)
        site2 = java.jclass("Site")(location2)
        site3 = java.jclass("Site")(location3)

        hashmap = java.jclass("HashMap")()

        hashmap.put(site1, 0.1)
        hashmap.put(site2, 0.2)
        hashmap.put(site3, 0.3)

        gmf_as_dict = scenario.gmf_to_dict(hashmap, "MMI")

        for gmv in gmf_as_dict:
            self.assertTrue(gmv["mag"] in (0.1, 0.2, 0.3))
            self.assertTrue(gmv["site_lon"] in (2.0, 2.1, 2.2))
            self.assertTrue(gmv["site_lat"] in (1.0, 1.1, 1.2))

    def test_when_measure_type_is_not_mmi_exp_is_stored(self):
        location = java.jclass("Location")(1.0, 2.0)
        site = java.jclass("Site")(location)

        hashmap = java.jclass("HashMap")()
        hashmap.put(site, 0.1)

        for gmv in scenario.gmf_to_dict(hashmap, "PGA"):
            self.assertEqual(math.exp(0.1), gmv["mag"])

    def test_when_measure_type_is_mmi_we_store_as_is(self):
        location = java.jclass("Location")(1.0, 2.0)
        site = java.jclass("Site")(location)

        hashmap = java.jclass("HashMap")()
        hashmap.put(site, 0.1)

        for gmv in scenario.gmf_to_dict(hashmap, "MMI"):
            self.assertEqual(0.1, gmv["mag"])

    def test_loads_the_rupture_model(self):
        calculator = scenario.ScenarioHazardCalculator(self.job_ctxt)

        self.assertEqual("org.opensha.sha.earthquake.EqkRupture",
                         calculator.rupture_model.__class__.__name__)

    def test_the_same_calculator_is_used_between_multiple_invocations(self):
        calculator = scenario.ScenarioHazardCalculator(self.job_ctxt)

        gmf_calculator1 = calculator.gmf_calculator([shapes.Site(1.0, 1.0)])
        gmf_calculator2 = calculator.gmf_calculator([shapes.Site(1.0, 1.0)])

        self.assertTrue(gmf_calculator1 == gmf_calculator2)
