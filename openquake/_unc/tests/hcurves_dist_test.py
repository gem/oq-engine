#
# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025 GEM Foundation
#
#                `.......      `....     `..`...     `..`... `......
#                `..    `..  `..    `..  `..`. `..   `..     `..
#                `..    `..`..        `..`..`.. `..  `..     `..
#                `.......  `..        `..`..`..  `.. `..     `..
#                `..       `..        `..`..`..   `. `..     `..
#                `..         `..     `.. `..`..    `. ..     `..
#                `..           `....     `..`..      `..     `..
#
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import unittest
import numpy as np

from openquake._unc.hcurves_dist import to_matrix, from_matrix
aae = np.testing.assert_almost_equal


class HazardCurvesDistributionTestCase(unittest.TestCase):

    def setUp(self):
        self.his0 = np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        self.his1 = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.minp = np.array([0, 1])
        self.nump = np.array([2, 2])

    def test_get_matrix(self):
        """ Get the matrix test case """
        his = []
        his.append(self.his0)
        his.append(self.his1)
        computed, _ = to_matrix(his, self.minp, self.nump)
        expected = np.empty((15, 2)) * np.nan
        expected[0:10, 0] = self.his0
        expected[5:15, 1] = self.his1
        aae(expected, computed)

    def test_from_matrix(self):
        """ From matrix test case """
        his = []
        his.append(self.his0)
        his.append(self.his1)
        mtx, _ = to_matrix(his, self.minp, self.nump)
        computed = from_matrix(mtx)
        aae(his, computed)
