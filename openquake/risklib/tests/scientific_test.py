# -*- coding: utf-8 -*-

# Copyright (c) 2013, GEM Foundation.
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
import mock
import pickle
import numpy
from openquake.risklib import DegenerateDistribution, utils, scientific


class DegenerateDistributionTest(unittest.TestCase):
    def setUp(self):
        self.distribution = DegenerateDistribution()

    def test_survival_zero_mean(self):
        self.assertEqual(
            0, self.distribution.survival(numpy.random.random(), 0, None))

    def test_survival_nonzeromean(self):
        loss_ratio = numpy.random.random()
        mean = loss_ratio - numpy.random.random()

        self.assertEqual(
            0, self.distribution.survival(loss_ratio, mean, None))

        mean = loss_ratio + numpy.random.random()
        self.assertEqual(
            1, self.distribution.survival(loss_ratio, mean, None))


class BetaDistributionTestCase(unittest.TestCase):
    def test_sample_one(self):
        numpy.random.seed(0)
        numpy.testing.assert_allclose(
            [0.057241368], scientific.BetaDistribution().sample(
                numpy.array([0.1]), None, numpy.array([0.1])))


class TestMemoize(unittest.TestCase):
    def test_cache(self):
        m = mock.Mock(return_value=3)
        func = utils.memoized(m)
        self.assertEqual(3, func())
        self.assertEqual(3, func())

        self.assertEqual(1, m.call_count)


class VulnerabilityFunctionTestCase(unittest.TestCase):
    """
    Test for
    :py:class:`openquake.risklib.vulnerability_function.VulnerabilityFunction`.
    """
    IMLS_GOOD = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]
    IMLS_BAD = [-0.1, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]
    IMLS_DUPE = [0.005, 0.005, 0.0098, 0.0137, 0.0192, 0.0269]
    IMLS_BAD_ORDER = [0.005, 0.0098, 0.007, 0.0137, 0.0192, 0.0269]

    LOSS_RATIOS_GOOD = [0.01, 0.1, 0.3, 0.5, 0.6, 1.0]
    LOSS_RATIOS_BAD = [0.1, 0.3, 0.0, 1.1, -0.1, 0.6]
    LOSS_RATIOS_TOO_SHORT = [0.1, 0.3, 0.0, 0.5, 1.0]
    LOSS_RATIOS_TOO_LONG = [0.1, 0.3, 0.0, 0.5, 1.0, 0.6, 0.5]

    COVS_GOOD = [0.3, 0.1, 0.3, 0.0, 0.3, 10]
    COVS_BAD = [-0.1, 0.1, 0.3, 0.0, 0.3, 10]
    COVS_TOO_SHORT = [0.3, 0.1, 0.3, 0.0, 0.3]
    COVS_TOO_LONG = [0.3, 0.1, 0.3, 0.0, 0.3, 10, 11]

    def setUp(self):
        self.test_func = scientific.VulnerabilityFunction(
            self.IMLS_GOOD, self.LOSS_RATIOS_GOOD, self.COVS_GOOD, "LN")

        self.test_func.init_distribution(1, 1, seed=3)

    def test_vuln_func_constructor_raises_on_bad_imls(self):
        # This test attempts to invoke AssertionErrors by passing 3 different
        # sets of bad IMLs to the constructor:
        #     - IML list containing out-of-range value(s)
        #     - IML list containing duplicates
        #     - IML list ordered improperly
        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_BAD, self.LOSS_RATIOS_GOOD, self.COVS_GOOD, "LN")

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_DUPE, self.LOSS_RATIOS_GOOD, self.COVS_GOOD, "LN")

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_BAD_ORDER, self.LOSS_RATIOS_GOOD,
            self.COVS_GOOD, "LN")

    def test_vuln_func_constructor_raises_on_bad_cov(self):
        # This test attempts to invoke AssertionErrors by passing 3 different
        # sets of bad CoV values to the constructor:
        #     - CoV list containing out-range-values
        #     - CoV list which is shorter than the IML list
        #     - CoV list which is longer than the IML list
        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_GOOD, self.COVS_BAD, "LN")

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_TOO_SHORT, "LN")

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_TOO_LONG, "LN")

    def test_vuln_func_constructor_raises_on_bad_loss_ratios(self):
        # This test attempts to invoke AssertionErrors by passing 3 different
        # sets of bad loss ratio values to the constructor:
        #     - loss ratio list containing out-range-values
        #     - loss ratio list which is shorter than the IML list
        #     - loss ratio list which is longer than the IML list
        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_BAD, self.COVS_GOOD, "LN")

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_TOO_SHORT,
            self.COVS_GOOD, "LN")

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_TOO_LONG, self.COVS_GOOD,
            "LN")

    def test_loss_ratio_interp_many_values(self):
        expected_lrs = numpy.array([0.0161928, 0.07685701,
                                    4.64095499])
        test_input = [0.005, 0.006, 0.0269]

        numpy.testing.assert_allclose(expected_lrs, self.test_func(test_input))

    def test_loss_ratio_interp_many_values_clipped(self):
        # Given a list of IML values (abscissae), test for proper interpolation
        # of loss ratios (ordinates).
        # This test also ensures that input IML values are 'clipped' to the IML
        # range defined for the vulnerability function.
        expected_lrs = numpy.array([0.0, 0.07685701, 4.64095499])
        test_input = [0.00049, 0.006, 2.7]

        numpy.testing.assert_allclose(expected_lrs, self.test_func(test_input))

    def test_cov_interp_many_values(self):
        expected_covs = numpy.array([0.3, 0.2, 10])
        test_input = [0.005, 0.006, 0.0269]

        numpy.testing.assert_allclose(
            expected_covs, self.test_func._cov_for(test_input))

    def test_cov_interp_many_values_clipped(self):
        # Given a list of IML values (abscissae), test for proper interpolation
        # of CoVs.
        # This test also ensures that input IML values are 'clipped' to the IML
        # range defined for the vulnerability function.
        expected_covs = numpy.array([0.3, 0.2, 10])
        test_input = [0.0049, 0.006, 0.027]

        numpy.testing.assert_allclose(
            expected_covs, self.test_func._cov_for(test_input))

    def test_vuln_func_constructor_raises_on_invalid_lr_cov(self):
        # If a loss ratio is 0.0 and the corresponding CoV is > 0.0, we expect
        # a ValueError.
        with self.assertRaises(ValueError) as ar:
            scientific.VulnerabilityFunction(
                self.IMLS_GOOD,
                [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
                [0.001, 0.002, 0.003, 0.004, 0.005, 0.006],
                "LN"
            )
        expected_error = (
            'It is not valid to define a loss ratio = 0.0 with a corresponding'
            ' coeff. of varation > 0.0'
        )
        self.assertEqual(expected_error, ar.exception.message)

    def test_lrem_lr_cov_special_cases(self):
        # Test LREM computation for points in a vuln curve where the loss ratio
        # > 0 and the CoV = 0, or loss ratio = 0 and CoV = 0.
        # If LR > 0 and CoV = 0, the PoE for values <= this LR are 1, and >
        # this LR are 0.
        # If LR = 0 and CoV = 0, the PoE will be 0.
        curve = scientific.VulnerabilityFunction(
            [0.1, 0.2, 0.3, 0.45, 0.6],  # IMLs
            [0.0, 0.1, 0.2, 0.4, 1.2],   # loss ratios
            [0.0, 0.0, 0.3, 0.2, 0.1],   # CoVs
            'LN'
        )
        loss_ratios, lrem = curve.loss_ratio_exceedance_matrix(5)
        expected_lrem = numpy.array([
            [0.000, 1.000, 1.000, 1.000, 1.000],
            [0.000, 1.000, 1.000, 1.000, 1.000],
            [0.000, 1.000, 1.000, 1.000, 1.000],
            [0.000, 1.000, 1.000, 1.000, 1.000],
            [0.000, 1.000, 0.999, 1.000, 1.000],
            [0.000, 1.000, 0.987, 1.000, 1.000],
            [0.000, 0.000, 0.944, 1.000, 1.000],
            [0.000, 0.000, 0.857, 1.000, 1.000],
            [0.000, 0.000, 0.730, 1.000, 1.000],
            [0.000, 0.000, 0.584, 1.000, 1.000],
            [0.000, 0.000, 0.442, 1.000, 1.000],
            [0.000, 0.000, 0.221, 0.993, 1.000],
            [0.000, 0.000, 0.098, 0.956, 1.000],
            [0.000, 0.000, 0.040, 0.848, 1.000],
            [0.000, 0.000, 0.016, 0.667, 1.000],
            [0.000, 0.000, 0.006, 0.461, 1.000],
            [0.000, 0.000, 0.000, 0.036, 1.000],
            [0.000, 0.000, 0.000, 0.001, 1.000],
            [0.000, 0.000, 0.000, 0.000, 0.999],
            [0.000, 0.000, 0.000, 0.000, 0.917],
            [0.000, 0.000, 0.000, 0.000, 0.480],
        ])
        numpy.testing.assert_array_almost_equal(lrem, expected_lrem, decimal=3)


class LogNormalDistributionTestCase(unittest.TestCase):

    def setUp(self):
        self.dist = scientific.LogNormalDistribution()

    def test_init(self):
        assets_num = 100
        samples_num = 1000
        correlation = 0.37
        self.dist.init(assets_num, samples_num, correlation=correlation,
                       seed=17)

        tol = 0.1
        for a1, a2 in utils.pairwise(range(assets_num)):
            coeffs = numpy.corrcoef(
                self.dist.epsilons[a1, :], self.dist.epsilons[a2, :])

            numpy.testing.assert_allclose([1, 1], [coeffs[0, 0], coeffs[1, 1]])
            numpy.testing.assert_allclose(
                correlation, coeffs[0, 1], rtol=0, atol=tol)
            numpy.testing.assert_allclose(
                correlation, coeffs[1, 0], rtol=0, atol=tol)

    def test_sample_mixed(self):
        # test that sampling works also when we have both covs = 0 and
        # covs != 0

        self.dist.init(1, 1, seed=17)
        samples = self.dist.sample(numpy.array([0., 0., .1, .1]),
                                   numpy.array([0., .1, 0., .1]),
                                   None)
        numpy.testing.assert_allclose([0., 0., 0.1, 0.10228396], samples)


class VulnerabilityLossRatioStepsTestCase(unittest.TestCase):
    def setUp(self):
        self.v1 = scientific.VulnerabilityFunction(
            [0, 1], [0.5, 0.7], [0, 0], "LN")
        self.v2 = scientific.VulnerabilityFunction(
            [0, 1, 2], [0.25, 0.5, 0.75], [0, 0, 0], "LN")

    def test_split_single_interval_with_no_steps_between(self):
        numpy.testing.assert_allclose(
            [0.0, 0.5, 0.7, 1.0],
            self.v1.mean_loss_ratios_with_steps(1))

    def test_evenly_spaced_single_interval_with_a_step_between(self):
        numpy.testing.assert_allclose(
            [0., 0.25, 0.5, 0.6, 0.7, 0.85, 1.],
            self.v1.mean_loss_ratios_with_steps(2))

    def test_evenly_spaced_single_interval_with_steps_between(self):
        numpy.testing.assert_allclose(
            [0., 0.125, 0.25, 0.375, 0.5, 0.55, 0.6, 0.65,
             0.7, 0.775, 0.85, 0.925, 1.],
            self.v1.mean_loss_ratios_with_steps(4))

    def test_evenly_spaced_multiple_intervals_with_a_step_between(self):
        numpy.testing.assert_allclose(
            [0., 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.],
            self.v2.mean_loss_ratios_with_steps(2))

    def test_evenly_spaced_multiple_intervals_with_steps_between(self):
        numpy.testing.assert_allclose(
            [0., 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375,
             0.4375, 0.5, 0.5625, 0.625, 0.6875, 0.75, 0.8125,
             0.875, 0.9375, 1.],
            self.v2.mean_loss_ratios_with_steps(4))

    def test__evenly_spaced_loss_ratios(self):
        vf = scientific.VulnerabilityFunction(
            [0, 1, 2, 3, 4], [0.0, 0.1, 0.2, 0.4, 1.2], [0, 0, 0, 0, 0], "LN")

        es_lrs = vf.mean_loss_ratios_with_steps(5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_prepend_0(self):
        # We expect a 0.0 to be prepended to the LRs before spacing them

        vf = scientific.VulnerabilityFunction(
            [1, 2, 3, 4], [0.1, 0.2, 0.4, 1.2], [0, 0, 0, 0], "LN")
        es_lrs = vf.mean_loss_ratios_with_steps(5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_append_1(self):
        vf = scientific.VulnerabilityFunction(
            [0, 1], [0.0, 0.5], [0, 0], "LN")
        es_lrs = vf.mean_loss_ratios_with_steps(2)
        expected = [0.0, 0.25, 0.5, 0.75, 1.0]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test_strictly_increasing(self):
        vf = scientific.VulnerabilityFunction(
            [0, 1, 2, 3], [0.0, 0.5, 0.5, 1], [0, 0, 3, 4], "LN")
        vfs = vf.strictly_increasing()

        numpy.testing.assert_allclose([0, 1, 3], vfs.imls)
        numpy.testing.assert_allclose([0, 0.5, 1], vfs.mean_loss_ratios)
        numpy.testing.assert_allclose([0, 0, 4], vfs.covs)
        self.assertEqual(vf.distribution_name, vfs.distribution_name)

    def test_pickle(self):
        vf = scientific.VulnerabilityFunction(
            [0, 1, 2, 3], [0.0, 0.5, 0.5, 1], [0, 0, 3, 4], "LN")
        pickle.loads(pickle.dumps(vf))


class FragilityFunctionTestCase(unittest.TestCase):
    def test_dda_iml_above_range(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is higher than the highest
        # intensity measure level defined in the model (in this
        # particular case 0.7). Given this condition, to compute
        # the fractions of buildings we use the highest intensity
        # measure level defined in the model (0.7 in this case)

        ffns = [scientific.FragilityFunctionDiscrete(
            [0.1, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00])] * 2

        self._close_to(scientific.scenario_damage(ffns, [0.7]),
                       scientific.scenario_damage(ffns, [0.8]))

    def test_dda_iml_below_range_damage_limit_defined(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1) and lower than the no_damage_limit
        # attribute defined in the model. Given this condition, the
        # fractions of buildings is 100% no_damage and 0% for the
        # remaining limit states defined in the model.

        ffns = [scientific.FragilityFunctionDiscrete(
            [0.05, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00], 0.5)] * 2
        self._close_to([[1.0, 0.0, 0.0]],
                       scientific.scenario_damage(ffns, [0.02]))

    def test_gmv_between_no_damage_limit_and_first_iml(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1) but bigger than the no_damage_limit
        # attribute defined in the model. Given this condition, the
        # fractions of buildings is 97.5% no_damage and 2.5% for the
        # remaining limit states defined in the model.

        ffs = [
            scientific.FragilityFunctionDiscrete(
                [0.05, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00], 0.05),
            scientific.FragilityFunctionDiscrete(
                [0.05, 0.1, 0.3, 0.5, 0.7], [0, 0.00, 0.05, 0.20, 0.50], 0.05)]

        self._close_to([[0.975, 0.025, 0.]],
                       scientific.scenario_damage(ffs, [0.075]))

    def _close_to(self, expected, actual):
        numpy.testing.assert_allclose(actual, expected, atol=0.0, rtol=0.05)

    def test_can_pickle(self):
        ffd = scientific.FragilityFunctionDiscrete(
            [0, .1, .2, .3], [0.05, 0.20, 0.50, 1.00])
        self.assertEqual(pickle.loads(pickle.dumps(ffd)), ffd)

    def test_continuous_pickle(self):
        ffs = scientific.FragilityFunctionContinuous(0, 1)

        pickle.loads(pickle.dumps(ffs))

    def test_call(self):
        ffs = scientific.FragilityFunctionContinuous(0.5, 1)
        self._close_to(0.26293, ffs(0.1))

    def test_discrete_ne(self):
        ffd1 = scientific.FragilityFunctionDiscrete([], [])
        ffd2 = scientific.FragilityFunctionDiscrete([0.1], [0.1])

        self.assertTrue(ffd1 != ffd2)


class InsuredLossesTestCase(unittest.TestCase):
    def test_below_deductible(self):
        numpy.testing.assert_allclose(
            [0],
            scientific.insured_losses(numpy.array([0.05]), 0.1, 1))
        numpy.testing.assert_allclose(
            [0, 0],
            scientific.insured_losses(numpy.array([0.05, 0.1]), 0.1, 1))

    def test_above_limit(self):
        numpy.testing.assert_allclose(
            [0.4],
            scientific.insured_losses(numpy.array([0.6]), 0.1, 0.5))
        numpy.testing.assert_allclose(
            [0.4, 0.4],
            scientific.insured_losses(numpy.array([0.6, 0.7]), 0.1, 0.5))

    def test_in_range(self):
        numpy.testing.assert_allclose(
            [0.2],
            scientific.insured_losses(numpy.array([0.3]), 0.1, 0.5))
        numpy.testing.assert_allclose(
            [0.2, 0.3],
            scientific.insured_losses(numpy.array([0.3, 0.4]), 0.1, 0.5))

    def test_mixed(self):
        numpy.testing.assert_allclose(
            [0, 0.1, 0.4],
            scientific.insured_losses(numpy.array([0.05, 0.2, 0.6]), 0.1, 0.5))


class InsuredLossCurveTestCase(unittest.TestCase):
    def test_curve(self):
        curve = numpy.array(
            [numpy.linspace(0, 1, 11), numpy.linspace(1, 0, 11)])

        numpy.testing.assert_allclose(
            numpy.array([[0., 0.1, 0.2, 0.3, 0.4, 0.5],
                         [0.8, 0.8, 0.8, 0.7, 0.6, 0.5]]),
            scientific.insured_loss_curve(curve, 0.2, 0.5))

    def test_trivial_curve(self):
        curve = numpy.array(
            [numpy.linspace(0, 1, 11), numpy.zeros(11)])

        numpy.testing.assert_allclose(
            [[0, 0.1, 0.2, 0.3, 0.4, 0.5],
             [0, 0, 0, 0, 0, 0]],
            scientific.insured_loss_curve(curve, 0.1, 0.5))
