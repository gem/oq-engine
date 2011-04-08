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
This module tests the hazard side of the deterministic
event based calculation.
"""

import math
import numpy
import unittest
import json

from utils import helpers

from openquake import java
from openquake import kvs
from openquake import job
from openquake import flags
from openquake import shapes

from openquake.hazard import deterministic as det

DETERMINISTIC_SMOKE_TEST = helpers.smoketest_file("deterministic/config.gem")
NUMBER_OF_CALC_KEY = "NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"


def compute_ground_motion_field(self, random_generator):
    """Stubbed version of the method that computes the ground motion
    field calling java stuff."""

    hashmap = java.jclass("HashMap")()

    for site in self.sites_for_region():
        location = java.jclass("Location")(site.latitude, site.longitude)
        site = java.jclass("Site")(location)
        hashmap.put(site, 0.5)

    return hashmap


class DeterministicEventBasedMixinTestCase(unittest.TestCase):

    def setUp(self):
        flags.FLAGS.include_defaults = False

        self.engine = job.Job.from_file(DETERMINISTIC_SMOKE_TEST)
        self.engine.job_id = 1234

        self.engine.params["REGION_VERTEX"] = \
            "33.88, -118.30, 33.88, -118.06, 33.76, -118.06, 33.76, -118.30"

        self.engine.params["RUPTURE_SURFACE_DISCRETIZATION"] = "0.1"
        self.engine.params[NUMBER_OF_CALC_KEY] = "1"

        # saving the default java implementation
        self.default = \
            det.DeterministicEventBasedMixin.compute_ground_motion_field

        kvs.flush()
        self.kvs_client = kvs.get_client(binary=False)

    def tearDown(self):
        # restoring the default java implementation
        det.DeterministicEventBasedMixin.compute_ground_motion_field = \
            self.default

        flags.FLAGS.include_defaults = True

    def test_triggered_with_deterministic_calculation_mode(self):
        """The deterministic calculator is triggered.

        When HAZARD_CALCULATION_MODE and RISK_CALCULATION_MODE
        are set to "Deterministic" the deterministic event
        based calculator is triggered.
        """

        det.DeterministicEventBasedMixin.compute_ground_motion_field = \
            compute_ground_motion_field

        # True, True means that both mixins (hazard and risk) are triggered
        self.assertEqual([True, True], self.engine.launch())

    def test_the_hazard_subsystem_stores_gmfs_for_all_the_sites(self):
        """The hazard subsystem stores the computed gmfs in kvs.

        For each site in the region, a ground motion value is store
        in the underlying kvs system.
        """

        det.DeterministicEventBasedMixin.compute_ground_motion_field = \
            compute_ground_motion_field

        self.engine.launch()
        decoder = json.JSONDecoder()

        for site in self.engine.sites_for_region():
            key = kvs.tokens.ground_motion_value_key(
                self.engine.id, site.hash())

            # just one calculation is triggered in this test case
            self.assertEqual(1, self.kvs_client.llen(key))
            gmv = decoder.decode(self.kvs_client.lpop(key))
            self.assertEqual(0, self.kvs_client.llen(key))

            self.assertTrue(
                numpy.allclose(site.latitude, gmv["site_lat"]))

            self.assertTrue(
                numpy.allclose(site.longitude, gmv["site_lon"]))

    def test_multiple_computations_are_triggered(self):
        """The hazard subsystem is able to trigger multiple computations.

        Depending on the value specified by the user in the
        NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS key, the system
        calls the computation of the values for the entire region
        multiple times.
        """

        det.DeterministicEventBasedMixin.compute_ground_motion_field = \
            compute_ground_motion_field

        self.engine.params["INTENSITY_MEASURE_TYPE"] = "MMI"
        self.engine.params[NUMBER_OF_CALC_KEY] = "3"

        self.engine.launch()
        decoder = json.JSONDecoder()

        for site in self.engine.sites_for_region():
            key = kvs.tokens.ground_motion_value_key(
                self.engine.id, site.hash())

            self.assertEqual(3, self.kvs_client.llen(key))
            gmv = decoder.decode(self.kvs_client.lpop(key))
            self.assertEqual(0.5, gmv["mag"])

            # since the org.opensha.commons.geo.Location object
            # stores lat/lon in radians, values are not
            # exactly the same
            self.assertTrue(
                numpy.allclose(site.latitude, gmv["site_lat"]))

            self.assertTrue(
                numpy.allclose(site.longitude, gmv["site_lon"]))

    def test_stores_the_list_of_keys_in_kvs(self):
        det.DeterministicEventBasedMixin.compute_ground_motion_field = \
            compute_ground_motion_field

        self.engine.params["INTENSITY_MEASURE_TYPE"] = "MMI"
        self.engine.params[NUMBER_OF_CALC_KEY] = "3"

        self.engine.launch()
        key_set_key = kvs.tokens.ground_motion_fields_keys(self.engine.id)
        key_set = self.kvs_client.smembers(key_set_key)

        # there are six sites in the test region, so
        # six keys are produced
        self.assertEqual(6, len(key_set))

        for site in self.engine.sites_for_region():
            key = kvs.tokens.ground_motion_value_key(
                self.engine.id, site.hash())

            self.assertTrue(key in key_set)

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

        gmf_as_dict = det.gmf_to_dict(hashmap, "MMI")

        for gmv in gmf_as_dict:
            self.assertTrue(gmv["mag"] in (0.1, 0.2, 0.3))
            self.assertTrue(gmv["site_lon"] in (2.0, 2.1, 2.2))
            self.assertTrue(gmv["site_lat"] in (1.0, 1.1, 1.2))

    def test_the_number_of_calculation_must_be_greater_than_zero(self):
        self.engine.params[NUMBER_OF_CALC_KEY] = "0"
        self.assertRaises(ValueError, self.engine.launch)

        self.engine.params[NUMBER_OF_CALC_KEY] = "-1"
        self.assertRaises(ValueError, self.engine.launch)

    def test_simple_computation_using_the_java_calculator(self):
        self.engine.launch()

        for site in self.engine.sites_for_region():
            key = kvs.tokens.ground_motion_value_key(
                self.engine.id, site.hash())

            self.assertTrue(kvs.get_keys(key))

    def test_when_measure_type_is_not_mmi_exp_is_stored(self):
        location = java.jclass("Location")(1.0, 2.0)
        site = java.jclass("Site")(location)

        hashmap = java.jclass("HashMap")()
        hashmap.put(site, 0.1)

        for gmv in det.gmf_to_dict(hashmap, "PGA"):
            self.assertEqual(math.exp(0.1), gmv["mag"])

    def test_when_measure_type_is_mmi_we_store_as_is(self):
        location = java.jclass("Location")(1.0, 2.0)
        site = java.jclass("Site")(location)

        hashmap = java.jclass("HashMap")()
        hashmap.put(site, 0.1)

        for gmv in det.gmf_to_dict(hashmap, "MMI"):
            self.assertEqual(0.1, gmv["mag"])

    def test_loads_the_rupture_model(self):
        calculator = det.DeterministicEventBasedMixin(None, None)
        calculator.params = self.engine.params

        self.assertEqual("org.opensha.sha.earthquake.EqkRupture",
                         calculator.rupture_model.__class__.__name__)

    def test_loads_the_gmpe(self):
        calculator = det.DeterministicEventBasedMixin(None, None)
        calculator.params = self.engine.params

        self.assertTrue("org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel",
                        calculator.gmpe.__class__.__name__)

    def test_the_same_calculator_is_used_between_multiple_invocations(self):
        calculator = det.DeterministicEventBasedMixin(None, None)
        calculator.params = self.engine.params

        gmf_calculator1 = calculator.gmf_calculator([shapes.Site(1.0, 1.0)])
        gmf_calculator2 = calculator.gmf_calculator([shapes.Site(1.0, 1.0)])

        self.assertTrue(gmf_calculator1 == gmf_calculator2)
