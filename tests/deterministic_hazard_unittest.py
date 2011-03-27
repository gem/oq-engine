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

import numpy
import unittest

from utils import test

from openquake import java
from openquake import kvs
from openquake import shapes
from openquake import job
from openquake import flags

from openquake.hazard import deterministic

DETERMINISTIC_SMOKE_TEST = test.smoketest_file("deterministic/config.gem")


class DeterministicEventBasedTestCase(unittest.TestCase):

    def setUp(self):
        flags.FLAGS.include_defaults = False

        self.engine = job.Job.from_file(DETERMINISTIC_SMOKE_TEST)
        self.engine.job_id = 1234
        
        self.engine.params["REGION_VERTEX"] = \
            "33.88, -118.30, 33.88, -118.06, 33.76, -118.06, 33.76, -118.30"

        self.engine.params["REGION_GRID_SPACING"] = 0.1
        self.engine.params["NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"] = 1

        kvs.flush()

    def test_triggered_with_deterministic_calculation_mode(self):
        """The deterministic calculator is triggered.

        When HAZARD_CALCULATION_MODE and RISK_CALCULATION_MODE
        are set to "Deterministic" the deterministic event
        based calculator is triggered.
        """

        # True, True means that both mixins (hazard and risk) are triggered
        self.assertEqual([True, True], self.engine.launch())

    def test_the_hazard_subsystem_stores_gmfs_for_all_the_sites(self):
        self.engine.launch()

        for site in self.engine.sites_for_region():
            key = kvs.tokens.ground_motion_value_key(
                self.engine.id, site.hash(), 1)

            self.assertTrue(kvs.get(key))
            gmv = kvs.get_value_json_decoded(key)
            
            self.assertTrue(numpy.allclose(site.latitude, gmv["site_lat"]))
            self.assertTrue(numpy.allclose(site.longitude, gmv["site_lon"]))

    def test_multiple_computations_are_triggered(self):
        self.engine.params["NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"] = 3
        self.engine.launch()

        for i in xrange(3):
# TODO (ac): Refactor!
            for site in self.engine.sites_for_region():
                key = kvs.tokens.ground_motion_value_key(
                    self.engine.id, site.hash(), i + 1)

                self.assertTrue(kvs.get(key))
                gmv = kvs.get_value_json_decoded(key)

# TODO (ac): Document this!
                self.assertTrue(numpy.allclose(site.latitude, gmv["site_lat"]))
                self.assertTrue(numpy.allclose(site.longitude, gmv["site_lon"]))

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

        gmf_as_dict = deterministic.gmf_to_dict(hashmap)
        self.assertEqual(3, len(gmf_as_dict))

        for gmv in gmf_as_dict:
            self.assertTrue(gmv["mag"] in (0.1, 0.2, 0.3))
            self.assertTrue(gmv["site_lon"] in (2.0, 2.1, 2.2))
            self.assertTrue(gmv["site_lat"] in (1.0, 1.1, 1.2))
