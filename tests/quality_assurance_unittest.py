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

import os
import unittest

from openquake import shapes
from tests.utils import helpers

TEST_NAME = "PeerTestSet1Case2"


class ClassicalPSHACalculatorAssuranceTestCase(unittest.TestCase):

    def test_peerTestSet1Case2(self):
        expected_results = self._load_results()
        self._run_job(helpers.smoketest_file(TEST_NAME + "/config.gem"))
        # - query database
        # - check results
        # - clean database

    def _run_job(self, config_file):
        job = helpers.job_from_file(config_file)
        job.launch()

    def _load_results(self):
        # simply split the x string and get
        # the value at index y casted to float
        get = lambda x, y: float(x.split(",")[y])

        results_dir = helpers.smoketest_file(TEST_NAME + "/expected_results")
        results_files = os.listdir(results_dir)

        results = {}

        for file in results_files:
            path = os.path.join(results_dir, file)

            with open(path, "rb") as hazard_curve:
                lines = hazard_curve.readlines()[0].split()

                coords = lines.pop(0)
                site = shapes.Site(get(coords, 0), get(coords, 1))

                results[site] = []

                while len(lines):
                    pair = lines.pop(0)
                    results[site].append((get(pair, 0), get(pair, 1)))

        return results
