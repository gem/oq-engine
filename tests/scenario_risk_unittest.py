# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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
This module tests the risk side of the scenario event based calculation.
"""

import json
import unittest

from openquake import kvs
from openquake import shapes
from openquake.calculators.risk.scenario import core as scenario_core

TEST_JOB_ID = "1234"
TEST_REGION = shapes.Region.from_simple((0.1, 0.1), (0.2, 0.2))


class ScenarioRiskTestCase(unittest.TestCase):
    """
    Test case for module-level functions of the scenario risk job code.
    """

    def test_load_gmvs_for_point(self):
        """Exercises the function
        :func:`openquake.calculators.risk.scenario.core.load_gmvs_for_point`.
        """

        # clear the kvs before running the test
        kvs.get_client().flushall()

        # values to place in the kvs
        test_gmvs = [
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.117},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.167},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.542}]

        expected_gmvs = [0.117, 0.167, 0.542]

        test_point = TEST_REGION.grid.point_at(shapes.Site(0.1, 0.2))

        # we expect this point to be at row 1, column 0
        self.assertEqual(1, test_point.row)
        self.assertEqual(0, test_point.column)

        gmvs_key = kvs.tokens.ground_motion_values_key(TEST_JOB_ID, test_point)

        # place the test values in kvs
        for gmv in test_gmvs:
            json_gmv = json.JSONEncoder().encode(gmv)
            kvs.get_client().rpush(gmvs_key, json_gmv)

        actual_gmvs = scenario_core.load_gmvs_for_point(TEST_JOB_ID,
                                                        test_point)

        # clear the kvs again before the test concludes
        kvs.get_client().flushall()

        self.assertEqual(expected_gmvs, actual_gmvs)

    def test_load_assets_for_point(self):
        """
        Exercises the function
        :py:func:`openquake.risk.job.scenario.load_assets_for_point`.
        """

        kvs.get_client().flushall()

        # Fabricate some test data.
        test_assets = [
            {'assetValue': 2129.5,
             'assetID': '104',
             'listDescription': 'fake_description',
             'structureCategory': 'S4L_MC',
             'lon': 0.11,
             'taxonomy': 'HAZUS_S4L_MC',
             'listID': 'LA01',
             'assetValueUnit': 'EUR',
             'lat': 0.11},
            {'assetValue': 2229.5,
             'assetID': '105',
             'listDescription': 'fake_description',
             'structureCategory': 'S4L_MC',
             'lon': 0.11,
             'taxonomy': 'HAZUS_S4L_MC',
             'listID': 'LA02',
             'assetValueUnit': 'EUR',
             'lat': 0.12}]

        test_site = shapes.Site(0.1, 0.1)
        test_point = TEST_REGION.grid.point_at(test_site)

        encoder = json.JSONEncoder()

        assets_key = kvs.tokens.asset_key(
            TEST_JOB_ID, test_point.row, test_point.column)

        # Throw the test data into the KVS.
        for asset in test_assets:
            kvs.get_client().rpush(assets_key, encoder.encode(asset))

        # The data should now be in the KVS.
        # Now verify that the load_assets_for_point function returns
        # the appropriate data.
        actual_assets = (
            scenario_core.load_assets_for_point(TEST_JOB_ID, test_point))

        kvs.get_client().flushall()

        # They should come out exactly the way they went in.
        self.assertEqual(test_assets, actual_assets)
