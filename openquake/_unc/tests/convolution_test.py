# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2025, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import numpy as np
from openquake._unc.convolution import get_pmf, conv


class CreatePMFTest(unittest.TestCase):

    def test_pmf_01(self):
        vals = np.array([0.011, 0.051, 0.052, 0.83])
        min_power, num_powers, pmf = get_pmf(vals)
        expected = np.array([0.25, 0., 0., 0., 0., 0.,
                             0., 0.5, 0., 0., 0.,
                             0., 0., 0., 0., 0.,
                             0., 0., 0., 0.25])
        np.testing.assert_array_equal(expected, pmf)


class ConvolutionTest(unittest.TestCase):

    def test_simple_convolution(self):
        # We start from PMFs
        res_a = 4
        res_b = 4
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
        _, _, _, pmfo = conv(
            hia, min_power_a, res_a, num_powers_a, hib, min_power_b, res_b,
            num_powers_b)
        np.testing.assert_allclose(pmfo, [0., 0., 0.3, 0.68, 0.02, 0., 0., 0.])
