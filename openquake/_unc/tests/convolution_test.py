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
from openquake._unc.convolution import conv

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
