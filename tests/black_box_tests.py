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
Implementation of the black box tests suite.
"""

import numpy
import unittest

from openquake import kvs
from openquake import shapes
from tests.utils import helpers

# the Probability of Exceedance used to build the mean hazard map
POE = 0.1


class HazardMapTestCase(unittest.TestCase):

    def setUp(self):
        self.expected_results = _load_expected_results()
        kvs.flush()

        self.engine = helpers.job_from_file(
            helpers.smoketest_file("HazardMapTest/config.gem"))

    def bb_we_compute_the_same_sites_in_the_region(self):
        """We compute results on the correct sites.

        This test verifies that we split the region and compute
        the results on the sites we expect.
        """

        computed_sites = set(self.engine.region.sites)
        expected_sites = set([result[0] for result in self.expected_results])

        self.assertEqual(len(computed_sites), len(expected_sites))
        self.assertTrue(expected_sites == computed_sites)

    def bb_hazard_map_values_are_correctly_stored_in_kvs(self):
        """Hazard map values are correct and stored in kvs.

        This test verifies that the hazard map values we are going
        to store in .tiff and .xml formats are correct.
        """

        self.engine.launch()

        pattern = "%s*%s*%s*" % (
            kvs.tokens.MEAN_HAZARD_MAP_KEY_TOKEN, self.engine.id, POE)

        map_values = kvs.get_pattern_decoded(pattern)

        self.assertEqual(len(self.expected_results), len(map_values))

        for expected_result in self.expected_results:
            key = kvs.tokens.mean_hazard_map_key(
                self.engine.id, expected_result[0], POE)

            computed_value = float(kvs.get_value_json_decoded(key)["IML"])

            self.assertTrue(numpy.allclose(computed_value,
                    expected_result[1], atol=0.001))


def _load_expected_results():
    """Return a list of tuples in the form (shapes.Site, value)."""

    results = []

    with open(helpers.smoketest_file(
        "HazardMapTest/expected_results/meanHazardMap0.1.dat")) as f:

        for result in f:
            lon, lat, value = result.split()
            site = shapes.Site(float(lon), float(lat))
            results.append((site, float(value)))

    return results
