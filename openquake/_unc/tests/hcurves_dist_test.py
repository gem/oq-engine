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

from openquake._unc.hcurves_dist import to_matrix
aae = np.testing.assert_almost_equal


class HazardCurvesDistributionTestCase(unittest.TestCase):

    def test(self):
        his = [np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 19]),
               np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])]
        minp = np.array([0, 1])
        nump = np.array([2, 2])

        computed, _ = to_matrix(his, minp, nump)
        expected = np.empty((15, 2)) * np.nan
        expected[0:10, 0] = his[0]
        expected[5:15, 1] = his[1]
        aae(expected, computed)
        for hi, col in zip(his, computed.T):
            aae(hi, col[np.isfinite(col)])
