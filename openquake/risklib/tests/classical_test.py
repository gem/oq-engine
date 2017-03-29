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
import numpy
from scipy.interpolate import interp1d

from openquake.risklib import scientific


class ClassicalTestCase(unittest.TestCase):

    def setUp(self):
        self.covs = [0.500, 0.400, 0.300, 0.200, 0.100]
        self.imls = [0.100, 0.200, 0.300, 0.450, 0.600]
        self.stddevs = [0.025, 0.040, 0.060, 0.080, 0.080]
        self.mean_loss_ratios = [0.050, 0.100, 0.200, 0.400, 0.800]

    def test_loss_is_zero_if_probability_is_too_high(self):
        self.assertAlmostEqual(
            0.00, scientific.conditional_loss_ratio(
                [0.21, 0.24, 0.27, 0.30],
                [0.131, 0.108, 0.089, 0.066],
                .200))

    def test_loss_is_max_if_probability_is_too_low(self):
        self.assertAlmostEqual(
            0.30, scientific.conditional_loss_ratio(
                [0.21, 0.24, 0.27, 0.30],
                [0.131, 0.108, 0.089, 0.066],
                .01))

    def test_conditional_loss_duplicates(self):
        # we feed compute_conditional_loss with some duplicated data to see if
        # it's handled correctly

        loss_ratios1, poes1 = zip(*[
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])

        # duplicated y values, different x values, (0.19, 0.131), (0.20, 0.131)
        # should be skipped
        loss_ratios2, poes2 = zip(*[
            (0.19, 0.131), (0.20, 0.131), (0.21, 0.131),
            (0.24, 0.108), (0.27, 0.089), (0.30, 0.066),
        ])

        numpy.testing.assert_allclose(
            scientific.conditional_loss_ratio(loss_ratios1, poes1, 0.1),
            scientific.conditional_loss_ratio(loss_ratios2, poes2, 0.1))

    def test_conditional_loss_second(self):
        loss_ratios1, poes1 = zip(*[
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])
        numpy.testing.assert_allclose(
            0.2113043478,
            scientific.conditional_loss_ratio(loss_ratios1, poes1, 0.13))

    def test_conditional_loss_first(self):
        loss_ratios1, poes1 = zip(*[
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])
        numpy.testing.assert_allclose(
            0.21,
            scientific.conditional_loss_ratio(loss_ratios1, poes1, 0.131))

    def test_conditional_loss_last(self):
        loss_ratios1, poes1 = zip(*[
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])
        numpy.testing.assert_allclose(
            0.29869565217391303,
            scientific.conditional_loss_ratio(loss_ratios1, poes1, 0.067))

    def test_conditional_loss_last_exact(self):
        loss_ratios1, poes1 = zip(*[
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])
        numpy.testing.assert_allclose(
            0.30,
            scientific.conditional_loss_ratio(loss_ratios1, poes1, 0.066))

    def test_conditional_loss_computation(self):
        loss_ratios, poes = zip(*[
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])

        self.assertAlmostEqual(
            0.25263157,
            scientific.conditional_loss_ratio(loss_ratios, poes, 0.1))

    def test_compute_lrem_using_beta_distribution(self):
        expected_lrem = [
            [1.0000000, 1.0000000, 1.0000000, 1.0000000, 1.0000000],
            [0.9895151, 0.9999409, 1.0000000, 1.0000000, 1.0000000],
            [0.9175720, 0.9981966, 0.9999997, 1.0000000, 1.0000000],
            [0.7764311, 0.9887521, 0.9999922, 1.0000000, 1.0000000],
            [0.6033381, 0.9633258, 0.9999305, 1.0000000, 1.0000000],
            [0.4364471, 0.9160514, 0.9996459, 1.0000000, 1.0000000],
            [0.2975979, 0.8460938, 0.9987356, 1.0000000, 1.0000000],
            [0.1931667, 0.7574557, 0.9964704, 1.0000000, 1.0000000],
            [0.1202530, 0.6571491, 0.9917729, 0.9999999, 1.0000000],
            [0.0722091, 0.5530379, 0.9832939, 0.9999997, 1.0000000],
            [0.0420056, 0.4521525, 0.9695756, 0.9999988, 1.0000000],
            [0.0130890, 0.2790107, 0.9213254, 0.9999887, 1.0000000],
            [0.0037081, 0.1564388, 0.8409617, 0.9999306, 1.0000000],
            [0.0009665, 0.0805799, 0.7311262, 0.9996882, 1.0000000],
            [0.0002335, 0.0384571, 0.6024948, 0.9988955, 1.0000000],
            [0.0000526, 0.0171150, 0.4696314, 0.9967629, 1.0000000],
            [0.0000022, 0.0027969, 0.2413923, 0.9820831, 1.0000000],
            [0.0000001, 0.0003598, 0.0998227, 0.9364072, 1.0000000],
            [0.0000000, 0.0000367, 0.0334502, 0.8381920, 0.9999995],
            [0.0000000, 0.0000030, 0.0091150, 0.6821293, 0.9999959],
            [0.0000000, 0.0000002, 0.0020162, 0.4909782, 0.9999755],
            [0.0000000, 0.0000000, 0.0000509, 0.1617086, 0.9995033],
            [0.0000000, 0.0000000, 0.0000005, 0.0256980, 0.9945488],
            [0.0000000, 0.0000000, 0.0000000, 0.0016231, 0.9633558],
            [0.0000000, 0.0000000, 0.0000000, 0.0000288, 0.8399534],
            [0.0000000, 0.0000000, 0.0000000, 0.0000001, 0.5409583],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.3413124],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.1589844],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0421052],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0027925],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000]]

        vf = scientific.VulnerabilityFunction(
            'VF', 'PGA', self.imls, self.mean_loss_ratios, self.covs, "BT")

        loss_ratios, lrem = vf.loss_ratio_exceedance_matrix(5)
        numpy.testing.assert_allclose(
            expected_lrem, lrem, rtol=0.0, atol=0.0005)

    def test_bin_width_from_imls(self):
        imls = [0.1, 0.2, 0.4, 0.6]
        covs = [0.5, 0.5, 0.5, 0.5]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]

        vulnerability_function = scientific.VulnerabilityFunction(
            'VF', 'PGA', imls, loss_ratios, covs, "LN")

        expected_steps = [0.05, 0.15, 0.3, 0.5, 0.7]

        numpy.testing.assert_allclose(
            expected_steps, vulnerability_function.mean_imls())

    def test_compute_loss_ratio_curve(self):
        hazard_imls = [0.01, 0.08, 0.17, 0.26, 0.36, 0.55, 0.7]
        hazard_curve = [0.99, 0.96, 0.89, 0.82, 0.7, 0.4, 0.01]
        imls = [0.1, 0.2, 0.4, 0.6]
        covs = [0.5, 0.3, 0.2, 0.1]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]

        vulnerability_function = scientific.VulnerabilityFunction(
            'VF', 'PGA', imls, loss_ratios, covs, "LN")

        loss_ratio_curve = scientific.classical(
            vulnerability_function, hazard_imls, hazard_curve, 2)

        expected_curve = [
            (0.0, 0.96), (0.025, 0.96),
            (0.05, 0.91), (0.065, 0.87),
            (0.08, 0.83), (0.14, 0.75),
            (0.2, 0.60), (0.3, 0.47),
            (0.4, 0.23), (0.7, 0.00),
            (1.0, 0.00)]

        actual_poes_interp = interp1d(loss_ratio_curve[0],
                                      loss_ratio_curve[1])

        for loss, poe in expected_curve:
            numpy.testing.assert_allclose(
                poe, actual_poes_interp(loss), atol=0.005)
