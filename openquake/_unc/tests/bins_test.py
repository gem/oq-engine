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
from openquake._unc.bins import get_bins_data, get_bins_from_params


class CreatePMFTest(unittest.TestCase):
    """
    Tests the calculation of the PMF with np.histogram
    """
    def test_pmf(self):
        res = 10
        vals = np.array([0.011, 0.051, 0.052, 0.83])
        wei = np.ones_like(vals) / len(vals)

        # Compute bins data and bins
        min_power, num_powers = get_bins_data(vals)
        assert (min_power, num_powers) == (-2, 2)
        bins = get_bins_from_params(min_power, res, num_powers)
        assert len(bins) == 10*2 + 1

        # Compute the histogram of size num_powers * res
        his, _ = np.histogram(vals, bins=bins, weights=wei)
        assert len(his) == 20
        expected = np.array([0.25, 0., 0., 0., 0., 0.,
                             0., 0.5, 0., 0., 0.,
                             0., 0., 0., 0., 0.,
                             0., 0., 0., 0.25])
        np.testing.assert_array_equal(expected, his)


class BinsDataTest(unittest.TestCase):
    """
    Tests the calculation of bins data
    """
    def test_get_data(self):
        # bins for small values and negative zeros
        vals = np.array([
            -0.000000e+00, -0.000000e+00, +1.870947e-11, -0.000000e+00,
            -0.000000e+00, -0.000000e+00, +7.486355e-11, -0.000000e+00,
            -0.000000e+00, -0.000000e+00, +2.965895e-10, -0.000000e+00])
        min_power, num_powers = get_bins_data(vals)
        np.testing.assert_equal(min_power, -20)
        np.testing.assert_equal(num_powers, 11)


class GetBinsTest(unittest.TestCase):
    """
    Tests the calculation of bins i.e. edges of the intervals considered
    starting from bins data
    """
    def test_pmf_01(self):
        # simple bins calculation
        min_power = -2
        num_powers = 2
        nsampl_per_power = 5
        bins = get_bins_from_params(min_power, nsampl_per_power, num_powers)
        expected = np.array([0.01, 0.01584893, 0.02511886, 0.03981072,
                             0.06309573, 0.1, 0.15848932, 0.25118864,
                             0.39810717, 0.63095734, 1.])
        np.testing.assert_almost_equal(bins, expected, decimal=6)

    def test_pmf_02(self):
        # bins calculation - 3 powers
        min_power = -2
        num_powers = 3
        nsampl_per_power = 5
        bins = get_bins_from_params(min_power, nsampl_per_power, num_powers)
        np.testing.assert_equal(len(bins), num_powers * nsampl_per_power + 1)
