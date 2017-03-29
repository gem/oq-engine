# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import unittest

from openquake.risklib import scientific


class RiskCommonTestCase(unittest.TestCase):

    def test_compute_bcr(self):
        # numbers are proven to be correct
        eal_orig = 0.00838
        eal_retrofitted = 0.00587
        retrofitting_cost = 0.1
        interest = 0.05
        life_expectancy = 40
        expected_result = 0.43405

        result = scientific.bcr(
            eal_orig, eal_retrofitted, interest,
            life_expectancy, 1, retrofitting_cost)
        self.assertAlmostEqual(result, expected_result, delta=2e-5)
