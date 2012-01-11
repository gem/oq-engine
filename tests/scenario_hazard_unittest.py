# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
This module tests the hazard side of the scenario
event based calculation.
"""

import math
import unittest

from tests.utils import helpers
from tests.utils.helpers import patch

from openquake import engine
from openquake import java
from openquake import kvs
from openquake import shapes

from openquake.engine import CalculationProxy
from openquake.hazard import scenario

from openquake.db.models import OqCalculation

SCENARIO_SMOKE_TEST = helpers.testdata_path("scenario/config.gem")
NUMBER_OF_CALC_KEY = "NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"


def compute_ground_motion_field(self, _random_generator):
    """Stubbed version of the method that computes the ground motion
    field calling java stuff."""

    hashmap = java.jclass("HashMap")()

    for site in self.calc_proxy.sites_to_compute():
        location = java.jclass("Location")(site.latitude, site.longitude)
        site = java.jclass("Site")(location)
        hashmap.put(site, 0.5)

    return hashmap


class ScenarioEventBasedMixinTestCase(unittest.TestCase):
    """
    Tests for the Scenario Hazard engine.
    """

    @classmethod
    def setUpClass(cls):
        cls.kvs_client = kvs.get_client()

    def setUp(self):
        kvs.get_client().flushall()

        base_path = helpers.testdata_path("scenario")
        self.job_profile, self.params, self.sections = (
            engine.import_job_profile(SCENARIO_SMOKE_TEST))
        calculation = OqCalculation(owner=self.job_profile.owner,
                                    oq_job_profile=self.job_profile)
        calculation.save()
        self.calc_proxy = CalculationProxy(
            self.params, calculation.id, sections=self.sections,
            base_path=base_path, oq_job_profile=self.job_profile,
            oq_calculation=calculation)

        self.calc_proxy.params[NUMBER_OF_CALC_KEY] = "1"

        self.calc_proxy.params['SERIALIZE_RESULTS_TO'] = 'xml'

        # saving the default java implementation
        self.default = (
            scenario.ScenarioEventBasedMixin.compute_ground_motion_field)

        self.grid = self.calc_proxy.region.grid

        self.calc_proxy.to_kvs()

    def tearDown(self):
        # restoring the default java implementation
        scenario.ScenarioEventBasedMixin.compute_ground_motion_field = \
            self.default

    def test_multiple_computations_are_triggered(self):
        """The hazard subsystem is able to trigger multiple computations.

        Depending on the value specified by the user in the
        NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS key, the system
        calls the computation of the values for the entire region
        multiple times.
        """

        self.calc_proxy.params[NUMBER_OF_CALC_KEY] = "3"
        self.job_profile.gmf_calculation_number = 3
        self.job_profile.save()

        calculator = scenario.ScenarioEventBasedMixin(self.calc_proxy)

        with patch('openquake.hazard.scenario.ScenarioEventBasedMixin'
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
        calculator = scenario.ScenarioEventBasedMixin(self.calc_proxy)

        self.assertEqual("org.opensha.sha.earthquake.EqkRupture",
                         calculator.rupture_model.__class__.__name__)

    def test_the_same_calculator_is_used_between_multiple_invocations(self):
        calculator = scenario.ScenarioEventBasedMixin(self.calc_proxy)

        gmf_calculator1 = calculator.gmf_calculator([shapes.Site(1.0, 1.0)])
        gmf_calculator2 = calculator.gmf_calculator([shapes.Site(1.0, 1.0)])

        self.assertTrue(gmf_calculator1 == gmf_calculator2)
