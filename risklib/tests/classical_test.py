# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import unittest
import numpy

from risklib.curve import Curve
from risklib import scientific


class ClassicalTestCase(unittest.TestCase):

    def setUp(self):
        self.covs = [0.500, 0.400, 0.300, 0.200, 0.100]
        self.imls = [0.100, 0.200, 0.300, 0.450, 0.600]
        self.stddevs = [0.025, 0.040, 0.060, 0.080, 0.080]
        self.mean_loss_ratios = [0.050, 0.100, 0.200, 0.400, 0.800]

    def test_loss_is_zero_if_probability_is_too_high(self):
        loss_curve = Curve([
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])

        self.assertAlmostEqual(
            0.0, scientific.conditional_loss(loss_curve, 0.200))

    def test_loss_is_max_if_probability_is_too_low(self):
        loss_curve = Curve([
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])

        self.assertAlmostEqual(0.30,
                               scientific.conditional_loss(loss_curve, 0.050))

    def test_conditional_loss_duplicates(self):
        # we feed compute_conditional_loss with some duplicated data to see if
        # it's handled correctly

        loss1 = scientific.conditional_loss(Curve([
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ]), 0.100)

        # duplicated y values, different x values, (0.19, 0.131), (0.20, 0.131)
        # should be skipped
        loss2 = scientific.conditional_loss(Curve([
            (0.19, 0.131), (0.20, 0.131), (0.21, 0.131),
            (0.24, 0.108), (0.27, 0.089), (0.30, 0.066),
        ]), 0.100)

        numpy.testing.assert_allclose(loss1, loss2)

    def test_conditional_loss_computation(self):
        loss_curve = Curve([
            (0.21, 0.131), (0.24, 0.108),
            (0.27, 0.089), (0.30, 0.066),
        ])

        self.assertAlmostEqual(0.2526, scientific.conditional_loss(
            loss_curve, 0.100), 4)

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
            self.imls, self.mean_loss_ratios, self.covs, "BT")

        lrem = vf.loss_ratio_exceedance_matrix(5)
        numpy.testing.assert_allclose(
            expected_lrem, lrem, rtol=0.0, atol=0.0005)

    def test_lrem_po_computation(self):
        hazard_curve = [
            (0.01, 0.99), (0.08, 0.96),
            (0.17, 0.89), (0.26, 0.82),
            (0.36, 0.70), (0.55, 0.40),
            (0.70, 0.01),
        ]

        imls = [0.1, 0.2, 0.4, 0.6]
        covs = [0.5, 0.3, 0.2, 0.1]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        vuln_function = scientific.VulnerabilityFunction(
            imls, loss_ratios, covs, "LN")

        # pre computed values just use one intermediate
        # values between the imls, so steps=2
        lrem = vuln_function.loss_ratio_exceedance_matrix(2)
        lrem_po = scientific._loss_ratio_exceedance_matrix_per_poos(
            vuln_function, lrem, hazard_curve)

        numpy.testing.assert_allclose(0.07, lrem_po[0][0], atol=0.005)
        numpy.testing.assert_allclose(0.06, lrem_po[1][0], atol=0.005)
        numpy.testing.assert_allclose(0.13, lrem_po[0][1], atol=0.005)
        numpy.testing.assert_allclose(0.47, lrem_po[5][3], atol=0.005)
        numpy.testing.assert_allclose(0.23, lrem_po[8][3], atol=0.005)
        numpy.testing.assert_allclose(0.00, lrem_po[10][0], atol=0.005)

    def test_bin_width_from_imls(self):
        imls = [0.1, 0.2, 0.4, 0.6]
        covs = [0.5, 0.5, 0.5, 0.5]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]

        vulnerability_function = scientific.VulnerabilityFunction(
            imls, loss_ratios, covs, "LN")

        expected_steps = [0.05, 0.15, 0.3, 0.5, 0.7]

        numpy.testing.assert_allclose(
            expected_steps, vulnerability_function.mean_imls())

    def test_split_with_real_values_from_turkey(self):
        loss_ratios = [
            0.0, 1.96E-15, 2.53E-12, 8.00E-10, 8.31E-08, 3.52E-06,
            7.16E-05, 7.96E-04, 5.37E-03, 2.39E-02, 7.51E-02, 1.77E-01]

        result = [0.0, 3.9199999999999996e-16,
                  7.8399999999999992e-16, 1.1759999999999998e-15,
                  1.5679999999999998e-15, 1.9599999999999999e-15,
                  5.0756799999999998e-13, 1.0131759999999998e-12,
                  1.5187839999999998e-12, 2.024392e-12, 2.5299999999999999e-12,
                  1.6202400000000001e-10, 3.2151800000000003e-10,
                  4.8101199999999999e-10, 6.4050600000000006e-10,
                  8.0000000000000003e-10, 1.726e-08, 3.372e-08,
                  5.0179999999999997e-08, 6.6639999999999993e-08,
                  8.3099999999999996e-08, 7.7048000000000005e-07,
                  1.4578600000000002e-06, 2.1452400000000005e-06,
                  2.8326200000000003e-06, 3.5200000000000002e-06,
                  1.7136000000000003e-05, 3.0752000000000006e-05,
                  4.4368000000000013e-05, 5.7984000000000013e-05,
                  7.1600000000000006e-05, 0.00021648000000000001,
                  0.00036136000000000002, 0.00050624000000000003,
                  0.00065112000000000004, 0.00079600000000000005,
                  0.0017108000000000002, 0.0026256000000000001,
                  0.0035404, 0.0044552000000000003, 0.0053699999999999998,
                  0.0090760000000000007, 0.012782, 0.016487999999999999,
                  0.020194, 0.023900000000000001, 0.034140000000000004,
                  0.044380000000000003, 0.054620000000000002,
                  0.064860000000000001, 0.0751, 0.095479999999999995,
                  0.11585999999999999, 0.13624,
                  0.15661999999999998, 0.17699999999999999]

        numpy.testing.assert_allclose(
            result, scientific._evenly_spaced_loss_ratios(loss_ratios, 5))

    def test_split_with_real_values_from_taiwan(self):
        loss_ratios = [0.0, 1.877E-20, 8.485E-17, 8.427E-14,
                       2.495E-11, 2.769E-09, 1.372E-07, 3.481E-06,
                       5.042E-05, 4.550E-04, 2.749E-03, 1.181E-02]
        self.assertEqual(56, len(
            scientific._evenly_spaced_loss_ratios(loss_ratios, 5)))

    def test_compute_loss_ratio_curve(self):
        hazard_curve = [
            (0.01, 0.99), (0.08, 0.96),
            (0.17, 0.89), (0.26, 0.82),
            (0.36, 0.70), (0.55, 0.40),
            (0.70, 0.01)]

        imls = [0.1, 0.2, 0.4, 0.6]
        covs = [0.5, 0.3, 0.2, 0.1]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]

        vulnerability_function = scientific.VulnerabilityFunction(
            imls, loss_ratios, covs, "LN")

        # pre computed values just use one intermediate
        # values between the imls, so steps=2
        lrem = [[1., 1., 1., 1.],
                [8.90868149e-01, 9.99932030e-01, 1., 1.],
                [4.06642478e-01, 9.27063668e-01, 1., 1.],
                [2.14297309e-01, 7.12442306e-01, 9.99999988e-01, 1.],
                [1.09131851e-01, 4.41652761e-01, 9.99997019e-01, 1.],
                [7.84971008e-03, 2.00321301e-02, 9.55620783e-01, 1.],
                [7.59869969e-04, 5.41393717e-04, 4.60560758e-01, 1.],
                [2.79797605e-05, 1.66547090e-06, 1.59210054e-02,
                 9.97702369e-01],
                [1.75697664e-06, 9.04938835e-09, 1.59710253e-04,
                 4.80110732e-01],
                [2.89163471e-09, 2.43138842e-14, 6.60395072e-11,
                 7.56938368e-09],
                [2.38464803e-11, 0., 1.11022302e-16, 0.]]

        loss_ratio_curve = scientific.classical(
            vulnerability_function, lrem, hazard_curve, 2)

        expected_curve = Curve([
            (0.0, 0.96), (0.025, 0.96),
            (0.05, 0.91), (0.065, 0.87),
            (0.08, 0.83), (0.14, 0.75),
            (0.2, 0.60), (0.3, 0.47),
            (0.4, 0.23), (0.7, 0.00),
            (1.0, 0.00)])

        for x_value in expected_curve.abscissae:
            numpy.testing.assert_allclose(
                expected_curve.ordinate_for(x_value),
                loss_ratio_curve.ordinate_for(x_value), atol=0.005)

    def test_split_single_interval_with_no_steps_between(self):
        numpy.testing.assert_allclose(
            [1.0, 2.0],
            scientific._evenly_spaced_loss_ratios([1.0, 2.0], 1))

    def test_evenly_spaced_single_interval_with_a_step_between(self):
        numpy.testing.assert_allclose(
            [1.0, 1.5, 2.0],
            scientific._evenly_spaced_loss_ratios([1.0, 2.0], 2))

    def test_evenly_spaced_single_interval_with_steps_between(self):
        numpy.testing.assert_allclose(
            [1.0, 1.25, 1.50, 1.75, 2.0],
            scientific._evenly_spaced_loss_ratios([1.0, 2.0], 4))

    def test_evenly_spaced_multiple_intervals_with_a_step_between(self):
        numpy.testing.assert_allclose(
            [1.0, 1.5, 2.0, 2.5, 3.0],
            scientific._evenly_spaced_loss_ratios([1.0, 2.0, 3.0], 2))

    def test_evenly_spaced_multiple_intervals_with_steps_between(self):
        numpy.testing.assert_allclose(
            [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0],
            scientific._evenly_spaced_loss_ratios([1.0, 2.0, 3.0], 4))
