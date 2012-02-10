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

import os
import unittest

from openquake import shapes
from openquake.parser import hazard
from tests.utils import helpers

EXAMPLE_DIR = os.path.join(helpers.SCHEMA_DIR, "examples")
TEST_FILE = os.path.join(EXAMPLE_DIR, "hazard-map.xml")


class HazardMapParserTestCase(unittest.TestCase):

    def setUp(self):
        self.reader = hazard.HazardMapReader(TEST_FILE)
        self.data = self._parse()

    def test_reads_all_the_nodes_defined(self):
        # we have just two nodes in the example file
        self.assertEqual(2, len(self.data))

    def test_reads_the_site_for_each_node(self):
        self.assertEqual(shapes.Site(-116.0, 41.0), self.data[0][0])
        self.assertEqual(shapes.Site(-118.0, 41.0), self.data[1][0])

    def test_reads_the_intensity_measure_level_for_each_node(self):
        self.assertEqual(0.2, self.data[0][1]["IML"])
        self.assertEqual(0.3, self.data[1][1]["IML"])

    def test_reads_the_prob_of_exceedance(self):
        self.assertEqual(0.1, self.data[0][1]["poE"])
        self.assertEqual(0.1, self.data[1][1]["poE"])

    def test_reads_the_intensity_measure_type(self):
        self.assertEqual("PGA", self.data[0][1]["IMT"])
        self.assertEqual("PGA", self.data[1][1]["IMT"])

    def _parse(self):
        results = []

        for node in self.reader:
            results.append(node)

        return results
