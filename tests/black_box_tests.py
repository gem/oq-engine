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
from openquake import job
from openquake import shapes
from utils import helpers


class HazardMapTestCase(unittest.TestCase):
    
    def setUp(self):
        expected_results_file = open(helpers.smoketest_file(
            "HazardMapTest/expected_results/meanHazardMap0.1.dat"))

        self.expected_results = []
        
        for expected_result in expected_results_file:
            self.expected_results.append(expected_result.split())

        kvs.flush()

        self.engine = job.Job.from_file(
            helpers.smoketest_file("HazardMapTest/config.gem"))

    def test_hazard_map_values_are_correctly_stored_in_kvs(self):
        self.engine.launch()
        
        pattern = "%s*%s*%s*" % (kvs.tokens.MEAN_HAZARD_MAP_KEY_TOKEN, self.engine.id, 0.1)
        map_values = kvs.mget_decoded(pattern)
        
        self.assertEqual(len(self.expected_results), len(map_values))
        
        for expected_result in self.expected_results:
            lon, lat, value = expected_result
            site = shapes.Site(float(lon), float(lat))

            key = kvs.tokens.mean_hazard_map_key(self.engine.id, site, 0.1)
            computed_value = float(kvs.get_value_json_decoded(key)["IML"])

            self.assertTrue(numpy.allclose(computed_value, float(value), atol=0.15))
