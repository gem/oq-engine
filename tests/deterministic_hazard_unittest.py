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

import unittest

from utils import test

from openquake import kvs
from openquake import shapes
from openquake import job
from openquake import flags

DETERMINISTIC_SMOKE_TEST = test.smoketest_file("deterministic/config.gem")


class DeterministicEventBasedTestCase(unittest.TestCase):

    def setUp(self):
        flags.FLAGS.include_defaults = False

        self.engine = job.Job.from_file(DETERMINISTIC_SMOKE_TEST)
        self.engine.job_id = 1234

    def test_triggered_with_deterministic_calculation_mode(self):
        """The deterministic calculator is triggered.

        When HAZARD_CALCULATION_MODE and RISK_CALCULATION_MODE
        are set to "Deterministic" the deterministic event
        based calculator is triggered.
        """

        # True, True means that both mixins (hazard and risk) are triggered
        self.assertEqual([True, True], self.engine.launch())

    def test_the_hazard_subsystem_stores_gmfs_in_kvs(self):
        site = shapes.Site(1.0, 2.0)

        gmv = kvs.get_value_json_decoded(
            kvs.tokens.ground_motion_value_key(
            self.engine.id, site.hash(), 1))

        self.engine.launch()

        self.assertEqual(0.5, gmv["mag"])

        self.assertEqual(1.0, gmv["site_lon"])
        self.assertEqual(2.0, gmv["site_lat"])
