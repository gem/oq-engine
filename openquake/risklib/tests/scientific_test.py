# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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
import mock
import pickle

import numpy
from openquake.risklib import utils, scientific

aaae = numpy.testing.assert_array_almost_equal


class DegenerateDistributionTest(unittest.TestCase):
    def setUp(self):
        self.distribution = scientific.DegenerateDistribution()

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


epsilons = scientific.make_epsilons(
    numpy.zeros((1, 3)), seed=3, correlation=0)[0]


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

    IMT = 'PGA'
    ID = 'vf1'

    def setUp(self):
        self.test_func = scientific.VulnerabilityFunction(
            self.ID, self.IMT, self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_GOOD)

    def test_vuln_func_constructor_raises_on_bad_imls(self):
        # This test attempts to invoke AssertionErrors by passing 3 different
        # sets of bad IMLs to the constructor:
        #     - IML list containing out-of-range value(s)
        #     - IML list containing duplicates
        #     - IML list ordered improperly
        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_BAD, self.LOSS_RATIOS_GOOD,
            self.COVS_GOOD)

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_DUPE, self.LOSS_RATIOS_GOOD,
            self.COVS_GOOD)

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_BAD_ORDER, self.LOSS_RATIOS_GOOD,
            self.COVS_GOOD)

    def test_vuln_func_constructor_raises_on_bad_cov(self):
        # This test attempts to invoke AssertionErrors by passing 3 different
        # sets of bad CoV values to the constructor:
        #     - CoV list containing out-range-values
        #     - CoV list which is shorter than the IML list
        #     - CoV list which is longer than the IML list
        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_BAD)

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_TOO_SHORT)

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_TOO_LONG)

    def test_vuln_func_constructor_raises_on_bad_loss_ratios(self):
        # This test attempts to invoke AssertionErrors by passing 3 different
        # sets of bad loss ratio values to the constructor:
        #     - loss ratio list containing out-range-values
        #     - loss ratio list which is shorter than the IML list
        #     - loss ratio list which is longer than the IML list
        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_GOOD, self.LOSS_RATIOS_BAD,
            self.COVS_GOOD)

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_GOOD, self.LOSS_RATIOS_TOO_SHORT,
            self.COVS_GOOD)

        self.assertRaises(
            AssertionError, scientific.VulnerabilityFunction,
            self.ID, self.IMT, self.IMLS_GOOD, self.LOSS_RATIOS_TOO_LONG,
            self.COVS_GOOD)

    def test_loss_ratio_interp_many_values(self):
        expected_lrs = numpy.array([0.0161928, 0.05880167, 0.12242504])
        test_input = [0.005, 0.006, 0.0269]
        numpy.testing.assert_allclose(
            expected_lrs, self.test_func(test_input, epsilons))

    def test_loss_ratio_interp_many_values_clipped(self):
        # Given a list of IML values (abscissae), test for proper interpolation
        # of loss ratios (ordinates).
        # This test also ensures that input IML values are 'clipped' to the IML
        # range defined for the vulnerability function.
        expected_lrs = numpy.array([0., 0.05880167, 0.12242504])
        test_input = [0.00049, 0.006, 2.7]
        numpy.testing.assert_allclose(
            expected_lrs, self.test_func(test_input, epsilons))

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
                self.ID, self.IMT, self.IMLS_GOOD,
                [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
                [0.001, 0.002, 0.003, 0.004, 0.005, 0.006],
            )
        expected_error = (
            'It is not valid to define a loss ratio = 0.0 with a corresponding'
            ' coeff. of variation > 0.0'
        )
        self.assertEqual(expected_error, str(ar.exception))

    def test_lrem_lr_cov_special_cases(self):
        # Test LREM computation for points in a vuln curve where the loss ratio
        # > 0 and the CoV = 0, or loss ratio = 0 and CoV = 0.
        # If LR > 0 and CoV = 0, the PoE for values <= this LR are 1, and >
        # this LR are 0.
        # If LR = 0 and CoV = 0, the PoE will be 0.
        curve = scientific.VulnerabilityFunction(
            self.ID, self.IMT,
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
        aaae(lrem, expected_lrem, decimal=3)


class VulnerabilityFunctionBlockSizeTestCase(unittest.TestCase):
    """
    Test the block size independency of the vulnerability function
    """
    @classmethod
    def setUpClass(cls):
        cls.vf = scientific.VulnerabilityFunction(
            'RM', 'PGA', [0.02, 0.3, 0.5, 0.9, 1.2],
            [0.05, 0.1, 0.2, 0.4, 0.8],
            [0.0001, 0.0001, 0.0001, 0.0001, 0.0001])

    def test(self):
        # values passed as a single block produce the same losses when
        # passed in several blocks

        gmvs = [0.3307648, 0.77900947, 0., 2.15393227, 0.,
                0., 0.42448847, 0., 0., 0., 0.15023323,
                0., 0., 0., 0., 0., 0., 0., 0.51451394, 0.]
        eps = [0.49671415, 0.64768854, -0.23415337, 1.57921282, -0.46947439,
               -0.46341769, 0.24196227, -1.72491783, -1.01283112, -0.90802408,
               1.46564877, 0.0675282, -0.54438272, -1.15099358, -0.60063869,
               -0.60170661, -0.01349722, 0.82254491, 0.2088636, -1.32818605]
        singleblock = list(self.vf(gmvs, eps).reshape(-1))

        # multiblock
        gmvs_, eps_ = [None] * 7, [None] * 7
        gmvs_[0] = [0.3307648, 0.77900947, 0.]
        eps_[0] = [0.49671415, 0.64768854, -0.23415337]
        gmvs_[1] = [2.15393227, 0., 0.]
        eps_[1] = [1.57921282, -0.46947439, -0.46341769]
        gmvs_[2] = [0.42448847, 0., 0.]
        eps_[2] = [0.24196227, -1.72491783, -1.01283112]
        gmvs_[3] = [0., 0.15023323, 0.]
        eps_[3] = [-0.90802408, 1.46564877, 0.0675282]
        gmvs_[4] = [0., 0., 0.]
        eps_[4] = [-0.54438272, -1.15099358, -0.60063869]
        gmvs_[5] = [0., 0., 0.]
        eps_[5] = [-0.60170661, -0.01349722, 0.82254491]
        gmvs_[6] = [0.51451394, 0.]
        eps_[6] = [0.2088636, -1.32818605]
        multiblock = []
        for gmvs, eps in zip(gmvs_, eps_):
            multiblock.extend(self.vf(gmvs, eps).reshape(-1))

        # this test has been broken forever, finally fixed in OpenQuake 1.5
        self.assertEqual(singleblock, multiblock)


class MeanLossTestCase(unittest.TestCase):
    def test_mean_loss(self):
        vf = scientific.VulnerabilityFunction(
            'VF1', 'PGA', imls=[0.1, 0.2, 0.3, 0.5, 0.7],
            mean_loss_ratios=[0.0035, 0.07, 0.14, 0.28, 0.56],
            covs=[0.1, 0.2, 0.3, 0.4, 0.5])

        epsilons = [0.98982371, 0.2776809, -0.44858935, 0.96196624,
                    -0.82757864, 0.53465707, 1.22838619]
        imls = [0.280357, 0.443609, 0.241845, 0.506982, 0.459758,
                0.456199, 0.38077]
        mean = vf(imls, epsilons).mean()
        aaae(mean, 0.2318058254)

        # if you don't reorder the epsilons, the mean loss depends on
        # the order of the imls!
        reordered_imls = [0.443609, 0.280357, 0.241845, 0.506982, 0.459758,
                          0.456199, 0.38077]
        mean2 = vf(reordered_imls, epsilons).mean()
        aaae(mean2, 0.238145174018)
        self.assertGreater(abs(mean2 - mean), 0.005)

        # by reordering the epsilons the problem is solved
        reordered_epsilons = [0.2776809, 0.98982371, -0.44858935, 0.96196624,
                              -0.82757864, 0.53465707, 1.22838619]
        mean3 = vf(reordered_imls, reordered_epsilons).mean()
        aaae(mean3, mean)


class LogNormalDistributionTestCase(unittest.TestCase):

    def test_init(self):
        assets_num = 100
        samples_num = 1000
        correlation = 0.37
        epsilons = scientific.make_epsilons(
            numpy.zeros((assets_num, samples_num)),
            seed=17, correlation=correlation)
        self.dist = scientific.LogNormalDistribution(epsilons)

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
        assets_num = 1
        samples_num = 1
        correlation = 0.37
        epsilons = scientific.make_epsilons(
            numpy.zeros((assets_num, samples_num)),
            seed=17, correlation=correlation)
        self.dist = scientific.LogNormalDistribution(epsilons)
        samples = self.dist.sample(numpy.array([0., 0., .1, .1]),
                                   numpy.array([0., .1, 0., .1]),
                                   None, slice(None)).reshape(-1)
        numpy.testing.assert_allclose([0., 0., 0.1, 0.10228396], samples)


class VulnerabilityLossRatioStepsTestCase(unittest.TestCase):
    IMT = 'PGA'

    def setUp(self):
        self.v1 = scientific.VulnerabilityFunction(
            'V1', self.IMT, [0, 1], [0.5, 0.7], [0, 0], "LN")
        self.v2 = scientific.VulnerabilityFunction(
            'V2', self.IMT, [0, 1, 2], [0.25, 0.5, 0.75], [0, 0, 0], "LN")

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
            'VF', self.IMT, [0, 1, 2, 3, 4], [0.0, 0.1, 0.2, 0.4, 1.2],
            [0, 0, 0, 0, 0])

        es_lrs = vf.mean_loss_ratios_with_steps(5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_prepend_0(self):
        # We expect a 0.0 to be prepended to the LRs before spacing them

        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [1, 2, 3, 4], [0.1, 0.2, 0.4, 1.2], [0, 0, 0, 0])
        es_lrs = vf.mean_loss_ratios_with_steps(5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_append_1(self):
        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [0, 1], [0.0, 0.5], [0, 0])
        es_lrs = vf.mean_loss_ratios_with_steps(2)
        expected = [0.0, 0.25, 0.5, 0.75, 1.0]
        numpy.testing.assert_allclose(es_lrs, expected)

    def test_strictly_increasing(self):
        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [0, 1, 2, 3], [0.0, 0.5, 0.5, 1], [0, 0, 3, 4])
        vfs = vf.strictly_increasing()

        numpy.testing.assert_allclose([0, 1, 3], vfs.imls)
        numpy.testing.assert_allclose([0, 0.5, 1], vfs.mean_loss_ratios)
        numpy.testing.assert_allclose([0, 0, 4], vfs.covs)
        self.assertEqual(vf.distribution_name, vfs.distribution_name)

    def test_pickle(self):
        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [0, 1, 2, 3], [0.0, 0.5, 0.5, 1], [0, 0, 3, 4])
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

        ffns = [
            scientific.FragilityFunctionDiscrete(
                'LS1', [0.1, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00]),
            scientific.FragilityFunctionDiscrete(
                'LS2', [0.1, 0.1, 0.3, 0.5, 0.7], [0, 0.05, 0.20, 0.50, 1.00])
            ]

        self._close_to(scientific.scenario_damage(ffns, 0.7),
                       scientific.scenario_damage(ffns, 0.8))

    def test_dda_iml_below_range_damage_limit_defined(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1) and lower than the no_damage_limit
        # attribute defined in the model. Given this condition, the
        # fractions of buildings is 100% no_damage and 0% for the
        # remaining limit states defined in the model.

        ffns = [
            scientific.FragilityFunctionDiscrete(
                'LS1', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.05, 0.20, 0.50, 1.00], 0.5),
            scientific.FragilityFunctionDiscrete(
                'LS2', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.05, 0.20, 0.50, 1.00], 0.5),
            ]
        self._close_to([1.0, 0.0, 0.0],
                       scientific.scenario_damage(ffns, 0.02))

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
                'LS1', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.05, 0.20, 0.50, 1.00], 0.05),
            scientific.FragilityFunctionDiscrete(
                'LS2', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.00, 0.05, 0.20, 0.50], 0.05)]

        self._close_to([0.975, 0.025, 0.],
                       scientific.scenario_damage(ffs, 0.075))

    def _close_to(self, expected, actual):
        numpy.testing.assert_allclose(actual, expected, atol=0.0, rtol=0.05)

    def test_can_pickle(self):
        ffd = scientific.FragilityFunctionDiscrete(
            'LS1', [0, .1, .2, .3], [0.05, 0.20, 0.50, 1.00])
        self.assertEqual(pickle.loads(pickle.dumps(ffd)), ffd)

    def test_continuous_pickle(self):
        ffs = scientific.FragilityFunctionContinuous('LS1', 0, 1)

        pickle.loads(pickle.dumps(ffs))

    def test_call(self):
        ffs = scientific.FragilityFunctionContinuous('LS1', 0.5, 1)
        self._close_to(0.26293, ffs(0.1))

    def test_discrete_ne(self):
        ffd1 = scientific.FragilityFunctionDiscrete('LS1', [], [])
        ffd2 = scientific.FragilityFunctionDiscrete('LS1', [0.1], [0.1])

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


class ClassicalDamageTestCase(unittest.TestCase):
    def test_discrete(self):
        hazard_imls = [0.05, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4]
        fragility_functions = scientific.FragilityFunctionList(
            [], imls=hazard_imls, steps_per_interval=None, format='discrete')
        fragility_functions.extend([
            scientific.FragilityFunctionDiscrete(
                'slight', hazard_imls,
                [0.0, 0.771, 0.95, 0.989, 0.997, 0.999, 1., 1.]),
            scientific.FragilityFunctionDiscrete(
                'moderate', hazard_imls,
                [0, 0.5, 0.861, 0.957, 0.985, 0.994, 0.997, 0.999]),
            scientific.FragilityFunctionDiscrete(
                'extreme', hazard_imls,
                [0.0, 0.231, 0.636, 0.837, 0.924, 0.962, .981, .989]),
            scientific.FragilityFunctionDiscrete(
                'complete', hazard_imls,
                [0, 0.097, 0.414, 0.661, 0.806, 0.887, 0.933, 0.959]),
        ])
        hazard_poes = numpy.array([
            0.999999999997518,
            0.077404949,
            0.015530587,
            0.004201327,
            0.001284191,
            0.000389925,
            0.000127992,
            0.000030350,
        ])
        investigation_time = 50.
        risk_investigation_time = 100.
        poos = scientific.classical_damage(
            fragility_functions, hazard_imls, hazard_poes,
            investigation_time, risk_investigation_time)
        aaae(poos, [1.0415184E-09, 1.4577245E-06, 1.9585762E-03, 6.9677521E-02,
                    9.2836244E-01])

    def test_continuous(self):
        hazard_imls = numpy.array(
            [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6,
             0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15, 1.2,
             1.25, 1.3, 1.35, 1.4])
        fragility_functions = scientific.FragilityFunctionList(
            [], imls=hazard_imls, steps_per_interval=None, format='continuous')
        fragility_functions.extend([
            scientific.FragilityFunctionContinuous(
                'slight', 0.160, 0.104),
            scientific.FragilityFunctionContinuous(
                'moderate', 0.225, 0.158),
            scientific.FragilityFunctionContinuous(
                'extreme', 0.400, 0.300),
            scientific.FragilityFunctionContinuous(
                'complete', 0.600, 0.480),
        ])
        hazard_poes = numpy.array([
            0.5917765421,
            0.2482053921,
            0.1298604374,
            0.07718928965,
            0.04912904516,
            0.03262871528,
            0.02226628376,
            0.01553639696,
            0.01101802934,
            0.007905366815,
            0.005741833876,
            0.004199803178,
            0.003088785556,
            0.00229291494,
            0.001716474683,
            0.001284555773,
            0.0009583846496,
            0.0007102377096,
            0.0005201223961,
            0.0003899464723,
            0.0002997724582,
            0.0002287788496,
            0.0001726083994,
            0.0001279544769,
            0.00009229282594,
            0.00006368651249,
            0.00004249201524,
            0.00003033694903,
            ])
        investigation_time = 50.
        risk_investigation_time = 100.
        poos = scientific.classical_damage(
            fragility_functions, hazard_imls, hazard_poes,
            investigation_time, risk_investigation_time)
        aaae(poos, [0.56652127, 0.12513401, 0.1709355, 0.06555033, 0.07185889])
