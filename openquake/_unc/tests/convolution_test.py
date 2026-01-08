# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2026 GEM Foundation
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
from openquake._unc.convolution import conv, HistoGroup

aae = np.testing.assert_almost_equal


class ConvolutionTest(unittest.TestCase):

    def test_simple_convolution(self):
        # We start from PMFs
        min_power_a = -1
        num_powers_a = 1
        min_power_b = -1
        num_powers_b = 1
        hia = np.array([0.0, 0.3, 0.6, 0.1])
        hib = np.array([0.8, 0.2, 0.0, 0.0])

        # The bins for the output histogram are:
        # [ 0.1, 0.17782794, 0.31622777, 0.56234133, 1., 1.77827941,
        #   3.16227766, 5.62341325, 10.]
        #
        # While the mid points for the input are:
        #  [0.13891397, 0.24702785, 0.43928455, 0.78117066]
        #
        # Output:
        # - I + I = 0.13891397 * 2 = 0.27782794 -> II output bin
        # - I + II = 0.13891397 + 0.24702785 = 0.38594182 -> III output bin
        # - II + II = 0.24702785 * 2 = 0.4940557 -> III output bin
        # - III + I = 0.43928455 + 0.13891397 = 0.57819852 -> IV bin
        # - III + II = 0.43928455 + 0.24702785 = 0.6863124 -> IV output bin
        # - III + III = 0.43928455 * 2 = 0.8785691 -> IV output bin
        # - III + IV = 0.78117066 + 0.43928455 = 1.22045521 -> V bin
        # - IV + I = 0.78117066 + 0.13891397 = 0.92008463 -> IV bin
        #
        # Probabilities for some bins:
        # 2nd: 0.0 * 0.8 = 0.0
        # 3rd: 0.8 * 0.3 + 0.0 * 0.2 = 0.24
        #      0.2 * 0.3 = 0.06
        # 4th: 0.6 * 0.8 + 0.0 * 0.0 = 0.48
        #      0.6 * 0.2 + 0.3 * 0.0 = 0.12
        #      0.6 * 0.2 = 0.0
        #      0.1 * 0.8 + 0.0 * 0.0 = 0.08

        # Computing convolution
        pmfo = conv(hia, min_power_a, num_powers_a,
                    hib, min_power_b, num_powers_b).pmfs[0]
        np.testing.assert_allclose(pmfo, [0., 0., 0.3, 0.68, 0.02, 0., 0., 0.])


class TestCase(unittest.TestCase):

    def test_to_matrix(self):
        his = [np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 19]),
               np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])]
        minp = np.array([0, 1])
        nump = np.array([2, 2])

        computed, afes = HistoGroup(
            his, minp, nump, normalized=False).to_matrix()
        exp_afes = np.array([1.  ,    1.64,    2.68,    4.39,    7.2 ,
                             11.79,   19.31,  31.62,   51.79,   84.83,
                             138.95,  227.58,  372.76,  610.54,  1000.])
        aae(np.round(afes, 2), exp_afes)

        expected = np.empty((15, 2)) * np.nan
        expected[0:10, 0] = his[0]
        expected[5:15, 1] = his[1]
        aae(expected, computed)
        for hi, col in zip(his, computed.T):
            aae(hi, col[np.isfinite(col)])
