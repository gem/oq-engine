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

import numpy
import unittest

from openquake.risklib import scientific


EPSILONS = [0.5377, 1.8339, -2.2588, 0.8622, 0.3188, -1.3077,
            -0.4336, 0.3426, 3.5784, 2.7694]


GMF = (0.079888, 0.273488, 0.115856, 0.034912, 0.271488, 0.00224,
       0.04336, 0.099552, 0.071968, 0.003456, 0.030704, 0.011744,
       0.024176, 0.002224, 0.008912, 0.004224, 0.033584, 0.041088,
       0.012864, 0.001728, 0.06648, 0.000736, 0.01992, 0.011616,
       0.001104, 0.033264, 0.021552, 0.055088, 0.00176, 0.001088, 0.041872,
       0.005152, 0.007424, 0.002464, 0.008496, 0.019744, 0.025136, 0.005552,
       0.00168, 0.00704, 0.00272, 0.081328, 0.001408, 0.025568, 0.051376,
       0.003456, 0.01208, 0.002496, 0.001152, 0.007552, 0.004944, 0.024944,
       0.01168, 0.027408, 0.00504, 0.003136, 0.20608, 0.00344, 0.01448,
       0.03664, 0.124992, 0.005024, 0.007536, 0.015696, 0.00608,
       0.001248, 0.005744, 0.017328, 0.002272, 0.06384, 0.029104,
       0.001152, 0.016384, 0.002096, 0.00328, 0.004304, 0.020544,
       0.000768, 0.011456, 0.004528, 0.024688, 0.024304, 0.126928,
       0.002416, 0.0032, 0.024768, 0.00608, 0.02544, 0.003392,
       0.381296, 0.013808, 0.002256, 0.181776, 0.038912, 0.023888,
       0.002848, 0.014176, 0.001936, 0.089408, 0.001008, 0.02152,
       0.002464, 0.00464, 0.064384, 0.001712, 0.01584, 0.012544,
       0.028128, 0.005808, 0.004928, 0.025536, 0.008304, 0.112528,
       0.06472, 0.01824, 0.002624, 0.003456, 0.014832, 0.002592,
       0.041264, 0.004368, 0.016144, 0.008032, 0.007344, 0.004976,
       0.00072, 0.022192, 0.002496, 0.001456, 0.044976, 0.055424,
       0.009232, 0.010368, 0.000944, 0.002976, 0.00656, 0.003184,
       0.004288, 0.00632, 0.286512, 0.007568, 0.00104, 0.00144,
       0.004896, 0.053248, 0.046144, 0.0128, 0.033072, 0.02968,
       0.002096, 0.021008, 0.017536, 0.000656, 0.016032, 0.012768,
       0.002752, 0.007392, 0.007072, 0.044112, 0.023072, 0.013232,
       0.001824, 0.020064, 0.008912, 0.039504, 0.00144, 0.000816,
       0.008544, 0.077056, 0.113984, 0.001856, 0.053024, 0.023792,
       0.013056, 0.0084, 0.009392, 0.010928, 0.041904, 0.000496,
       0.041936, 0.035664, 0.03176, 0.003552, 0.00216, 0.0476, 0.028944,
       0.006832, 0.011136, 0.025712, 0.006368, 0.004672, 0.001312,
       0.008496, 0.069136, 0.011568, 0.01576, 0.01072, 0.002336,
       0.166192, 0.00376, 0.013216, 0.000592, 0.002832, 0.052928,
       0.007872, 0.001072, 0.021136, 0.029568, 0.012944, 0.004064,
       0.002336, 0.010832, 0.10104, 0.00096, 0.01296, 0.037104)

TSES = 900.
TIMESPAN = 50.


class ProbabilisticEventBasedTestCase(unittest.TestCase):

    def setUp(self):
        self.vulnerability_function1 = scientific.VulnerabilityFunction(
            'VF1', 'PGA',
            [0.01, 0.04, 0.07, 0.1, 0.12, 0.22, 0.37, 0.52],
            [0.001, 0.022, 0.051, 0.08, 0.1, 0.2, 0.405, 0.7],
            [0.0] * 8, "LN")

        self.exceeding_times = numpy.array([
            112, 46, 26, 18, 14, 12, 8, 7, 7, 6, 5, 4,
            4, 4, 4, 4, 2, 1, 1, 1, 1, 1, 1, 1,
        ])

        self.vulnerability_function2 = scientific.VulnerabilityFunction(
            'VF2', 'PGA',
            [0.0, 0.04, 0.08, 0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36,
             0.4, 0.44, 0.48, 0.53, 0.57, 0.61, 0.65, 0.69, 0.73, 0.77, 0.81,
             0.85, 0.89, 0.93, 0.97, 1.01, 1.05, 1.09, 1.13, 1.17, 1.21, 1.25,
             1.29, 1.33, 1.37, 1.41, 1.45, 1.49, 1.54, 1.58, 1.62, 1.66, 1.7,
             1.74, 1.78, 1.82, 1.86, 1.9, 1.94, 1.98, 2.02, 2.06, 2.1, 2.14,
             2.18, 2.22, 2.26, 2.3, 2.34, 2.38, 2.42, 2.46, 2.51, 2.55, 2.59,
             2.63, 2.67, 2.71, 2.75, 2.79, 2.83, 2.87, 2.91, 2.95, 2.99, 3.03,
             3.07, 3.11, 3.15, 3.19, 3.23, 3.27, 3.31, 3.35, 3.39, 3.43, 3.47,
             3.52, 3.56, 3.6, 3.64, 3.68, 3.72, 3.76, 3.8, 3.84, 3.88, 3.92,
             3.96, 4.0],
            [0.0, 0.0, 0.0, 0.01, 0.04, 0.07, 0.11, 0.15, 0.2,
             0.25, 0.3, 0.35, 0.39, 0.43, 0.47, 0.51, 0.55, 0.58, 0.61, 0.64,
             0.67, 0.69, 0.71, 0.73, 0.75, 0.77, 0.79, 0.8, 0.81, 0.83, 0.84,
             0.85, 0.86, 0.87, 0.88, 0.89, 0.89, 0.9, 0.91, 0.91, 0.92, 0.92,
             0.93, 0.93, 0.94, 0.94, 0.94, 0.95, 0.95, 0.95, 0.95, 0.96, 0.96,
             0.96, 0.96, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97, 0.98, 0.98, 0.98,
             0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.99, 0.99, 0.99, 0.99,
             0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99,
             0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 1.0, 1.0,
             1.0, 1.0, 1.0], [0.0] * 100, "LN")

        self.gmf1 = {"IMLs": (
            0.1439, 0.1821, 0.5343, 0.171, 0.2177,
            0.6039, 0.0618, 0.186, 0.5512, 1.2602, 0.2824, 0.2693,
            0.1705, 0.8453, 0.6355, 0.0721, 0.2475, 0.1601, 0.3544,
            0.1756), "TSES": 200, "TimeSpan": 50}

        self.gmf2 = {"IMLs": (
            0.1507, 0.2656, 0.5422, 0.3685, 0.3172,
            0.6604, 0.1182, 0.1545, 0.7613, 0.5246, 0.2428, 0.2882,
            0.2179, 1.2939, 0.6042, 0.1418, 0.3637, 0.222, 0.3613,
            0.113), "TSES": 200, "TimeSpan": 50}

        self.gmf3 = {"IMLs": (
            0.156, 0.3158, 0.3968, 0.2827, 0.1915, 0.5862,
            0.1438, 0.2114, 0.5101, 1.0097, 0.226, 0.3443, 0.1693,
            1.0754, 0.3533, 0.1461, 0.347, 0.2665, 0.2977,
            0.2925), "TSES": 200, "TimeSpan": 50}

        self.gmf4 = {"IMLs": (
            0.1311, 0.3566, 0.4895, 0.3647, 0.2313,
            0.9297, 0.2337, 0.2862, 0.5278, 0.6603, 0.3537, 0.2997,
            0.1097, 1.1875, 0.4752, 0.1575, 0.4009, 0.2519, 0.2653,
            0.1394), "TSES": 200, "TimeSpan": 50}

        self.gmfs_5 = {"IMLs": (
            0.0879, 0.2895, 0.465, 0.2463, 0.1862, 0.763,
            0.2189, 0.3324, 0.3215, 0.6406, 0.5014, 0.3877, 0.1318, 1.0545,
            0.3035, 0.1118, 0.2981, 0.3492, 0.2406,
            0.1043), "TSES": 200, "TimeSpan": 50}

        self.gmf6 = {"IMLs": (
            0.0872, 0.2288, 0.5655, 0.2118, 0.2, 0.6633,
            0.2095, 0.6537, 0.3838, 0.781, 0.3054, 0.5375, 0.1361, 0.8838,
            0.3726, 0.0845, 0.1942, 0.4629, 0.1354,
            0.1109), "TSES": 200, "TimeSpan": 50}

    def test_an_empty_gmf_produces_an_empty_set(self):
        self.assertEqual(0, self.vulnerability_function1([], []).size)

    def test_sampling_lr_gmf_inside_range_vulnimls(self):
        # Sampling loss ratios (covs greater than zero), Ground Motion Fields
        # IMLs inside range defined by Vulnerability function's imls
        vf = scientific.VulnerabilityFunction(
            'VF', 'PGA',
            [0.10, 0.30, 0.50, 1.00], [0.05, 0.10, 0.15, 0.30],
            [0.30, 0.30, 0.20, 0.20], "LN")

        gmf = (
            0.1576, 0.9706, 0.9572, 0.4854, 0.8003,
            0.1419, 0.4218, 0.9157, 0.7922, 0.9595,
        )

        expected_loss_ratios = numpy.array([
            0.0722, 0.4106, 0.1800, 0.1710, 0.2508,
            0.0395, 0.1145, 0.2883, 0.4734, 0.4885,
        ])

        ratios = vf(gmf, EPSILONS)
        numpy.testing.assert_allclose(expected_loss_ratios,
                                      ratios, atol=0.0, rtol=0.01)

    def test_sampling_lr_gmf_less_than_first_vulnimls(self):
        # Sampling loss ratios (covs greater than zero), Ground Motion Fields
        # IMLs outside range defined by Vulnerability function's imls, some
        # values are less than the lower bound.
        vuln_function = scientific.VulnerabilityFunction(
            'VF', 'PGA',
            [0.10, 0.30, 0.50, 1.00], [0.05, 0.10, 0.15, 0.30],
            [0.30, 0.30, 0.20, 0.20], "LN")

        gmfs = (0.08, 0.9706, 0.9572, 0.4854, 0.8003,
                0.1419, 0.4218, 0.9157, 0.05, 0.9595)

        numpy.testing.assert_allclose(
            numpy.array([0., 0.4105595, 0.18002423, 0.17102685, 0.25077079,
                         0.03945861, 0.11454372, 0.28828653, 0., 0.48847448]),
            vuln_function(gmfs, EPSILONS), atol=0.0, rtol=0.01)

    def test_sampling_lr_gmfs_greater_than_last_vulnimls(self):
        # Sampling loss ratios (covs greater than zero), Ground Motion Fields
        # IMLs outside range defined by Vulnerability function's imls, some
        # values are greater than the upper bound.
        imls = [0.10, 0.30, 0.50, 1.00]
        loss_ratios = [0.05, 0.10, 0.15, 0.30]
        covs = [0.30, 0.30, 0.20, 0.20]
        vuln_function = scientific.VulnerabilityFunction(
            'VF', 'PGA', imls, loss_ratios, covs, "LN")

        gmfs = (1.1, 0.9706, 0.9572, 0.4854, 0.8003,
                0.1419, 0.4218, 0.9157, 1.05, 0.9595)

        numpy.testing.assert_allclose(
            numpy.array([0.3272, 0.4105, 0.1800, 0.1710, 0.2508,
                         0.0394, 0.1145, 0.2883, 0.5975, 0.4885]),
            vuln_function(gmfs, EPSILONS), atol=0.0, rtol=0.01)

    def test_loss_ratios_boundaries(self):
        # Loss ratios generation given a GMFs and a vulnerability function

        # The vulnerability function used in this test has all covs equal
        # to zero, so the mean based algorithm is used. This test checks
        # the boundary conditions.

        # The resulting loss ratio is zero if the GMF is below the minimum IML
        # defined the vulnerability function.

        # The resulting loss ratio is equal to the maximum loss ratio
        # defined by the function if the GMF is greater than the maximum
        # IML defined.

        # min IML in this case is 0.01
        numpy.testing.assert_allclose(
            numpy.array([0.0, 0.0, 0.0]),
            self.vulnerability_function1(
                [0.0001, 0.0002, 0.0003], EPSILONS[:3]))

        # max IML in this case is 0.52
        numpy.testing.assert_allclose(
            numpy.array([0.700, 0.700]),
            self.vulnerability_function1([0.525, 0.530], EPSILONS[:2]))

    def test_loss_ratios_computation_using_gmfs(self):
        # Loss ratios generation given a GMFs and a vulnerability function
        # The vulnerability function used in this test has all covs equal
        # to zero, so the mean based algorithm is used. It basically
        # takes each IML defined in the GMFs and interpolates them using
        # the given vulnerability function.
        # manually computed values by Vitor Silva
        expected_loss_ratios = numpy.array([
            0.0605584000000000,
            0.273100266666667, 0.0958560000000000, 0.0184384000000000,
            0.270366933333333, 0.0,
            0.0252480000000000, 0.0795669333333333,
            0.0529024000000000, 0.0,
        ])

        # the length of the result is the length of the gmf
        numpy.testing.assert_allclose(
            expected_loss_ratios,
            self.vulnerability_function1(GMF[:10], EPSILONS))
