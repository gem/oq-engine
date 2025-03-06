# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
import pickle
import toml

import numpy
import pandas
import matplotlib.pyplot as plt
from openquake.risklib import riskmodels, scientific

PLOTTING = False
aac = numpy.testing.assert_allclose
eids = numpy.arange(3)


def call(vf, gmvs, eids):
    rng = scientific.MultiEventRNG(42, eids)
    gmf_df = pandas.DataFrame(
        dict(eid=eids, PGA=gmvs, sid=numpy.zeros(len(eids))))
    return [vf(None, gmf_df, 'PGA', rng).loss.to_numpy()]


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
        self.test_func.init()

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
        expected_lrs = numpy.array([[0.006926, 0.033077, 0.181509]])
        test_input = [0.005, 0.006, 0.0269]
        numpy.testing.assert_allclose(
            expected_lrs, call(self.test_func, test_input, eids), atol=1E-6)

    def test_loss_ratio_interp_many_values_clipped(self):
        # Given a list of IML values (abscissae), test for proper interpolation
        # of loss ratios (ordinates).
        # This test also ensures that input IML values are 'clipped' to the IML
        # range defined for the vulnerability function.
        expected_lrs = numpy.array([[0.033077, 0.181509]])
        test_input = [0.00049, 0.006, 2.7]
        numpy.testing.assert_allclose(
            expected_lrs, call(self.test_func, test_input, eids), atol=1E-6)

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
            vf = scientific.VulnerabilityFunction(
                self.ID, self.IMT, self.IMLS_GOOD,
                [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
                [0.001, 0.002, 0.003, 0.004, 0.005, 0.006])
            vf.init()
        expected_error = (
            'It is not valid to define a mean loss ratio = 0 with a '
            'corresponding coefficient of variation > 0')
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
            'LN')
        curve.init()
        loss_ratios = tuple(curve.mean_loss_ratios_with_steps(5))
        lrem = curve.loss_ratio_exceedance_matrix(loss_ratios)
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
        aac(lrem, expected_lrem, atol=1E-3)


class VulnerabilityLossRatioStepsTestCase(unittest.TestCase):
    IMT = 'PGA'

    def setUp(self):
        self.v1 = scientific.VulnerabilityFunction(
            'V1', self.IMT, [0, 1], [0.5, 0.7], [0, 0], "LN")
        self.v1.seed = 41
        self.v2 = scientific.VulnerabilityFunction(
            'V2', self.IMT, [0, 1, 2], [0.25, 0.5, 0.75], [0, 0, 0], "LN")
        self.v2.seed = 41

    def test_split_single_interval_with_no_steps_between(self):
        aac([0.0, 0.5, 0.7, 1.0], self.v1.mean_loss_ratios_with_steps(1))

    def test_evenly_spaced_single_interval_with_a_step_between(self):
        aac([0., 0.25, 0.5, 0.6, 0.7, 0.85, 1.],
            self.v1.mean_loss_ratios_with_steps(2))

    def test_evenly_spaced_single_interval_with_steps_between(self):
        aac([0., 0.125, 0.25, 0.375, 0.5, 0.55, 0.6, 0.65,
             0.7, 0.775, 0.85, 0.925, 1.],
            self.v1.mean_loss_ratios_with_steps(4))

    def test_evenly_spaced_multiple_intervals_with_a_step_between(self):
        aac([0., 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.],
            self.v2.mean_loss_ratios_with_steps(2))

    def test_evenly_spaced_multiple_intervals_with_steps_between(self):
        aac([0., 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375,
             0.4375, 0.5, 0.5625, 0.625, 0.6875, 0.75, 0.8125,
             0.875, 0.9375, 1.],
            self.v2.mean_loss_ratios_with_steps(4))

    def test__evenly_spaced_loss_ratios(self):
        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [0, 1, 2, 3, 4], [0.0, 0.1, 0.2, 0.4, 1.2],
            [0, 0, 0, 0, 0])
        vf.seed = 42
        vf.init()

        es_lrs = vf.mean_loss_ratios_with_steps(5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        aac(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_prepend_0(self):
        # We expect a 0.0 to be prepended to the LRs before spacing them

        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [1, 2, 3, 4], [0.1, 0.2, 0.4, 1.2], [0, 0, 0, 0])
        vf.seed = 42
        vf.init()

        es_lrs = vf.mean_loss_ratios_with_steps(5)
        expected = [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18,
                    0.2, 0.24000000000000002, 0.28, 0.32, 0.36, 0.4, 0.56,
                    0.72, 0.8799999999999999, 1.04, 1.2]
        aac(es_lrs, expected)

    def test__evenly_spaced_loss_ratios_append_1(self):
        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [0, 1], [0.0, 0.5], [0, 0])
        vf.seed = 42
        vf.init()
        es_lrs = vf.mean_loss_ratios_with_steps(2)
        expected = [0.0, 0.25, 0.5, 0.75, 1.0]
        aac(es_lrs, expected)

    def test_strictly_increasing(self):
        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [0, 1, 2, 3], [0.0, 0.5, 0.5, 1], [0, 0, 3, 4])
        vf.seed = 42
        vf.init()
        vfs = vf.strictly_increasing()

        aac([0, 1, 3], vfs.imls)
        aac([0, 0.5, 1], vfs.mean_loss_ratios)
        aac([0, 0, 4], vfs.covs)
        self.assertEqual(vf.distribution_name, vfs.distribution_name)

    def test_pickle(self):
        vf = scientific.VulnerabilityFunction(
            'VF', self.IMT, [0, 1, 2, 3], [0.0, 0.5, 0.5, 1], [0, 0, 3, 4])
        vf.seed = 42
        vf.init()
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

        ffns = [
            scientific.FragilityFunctionDiscrete(
                'LS1', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.05, 0.20, 0.50, 1.00], 0.5),
            scientific.FragilityFunctionDiscrete(
                'LS2', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.05, 0.20, 0.50, 1.00], 0.5),
            ]
        self._close_to([[1.0], [0.0], [0.0]],
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
                'LS1', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.05, 0.20, 0.50, 1.00], 0.05),
            scientific.FragilityFunctionDiscrete(
                'LS2', [0.05, 0.1, 0.3, 0.5, 0.7],
                [0, 0.00, 0.05, 0.20, 0.50], 0.05)]
        self._close_to([0.975, 0.025, 0],
                       scientific.scenario_damage(ffs, 0.075))

    def _close_to(self, expected, actual):
        aac(actual, expected, atol=0.0, rtol=0.05)

    def test_can_pickle(self):
        ffd = scientific.FragilityFunctionDiscrete(
            'LS1', [0, .1, .2, .3], [0.05, 0.20, 0.50, 1.00])
        self.assertEqual(pickle.loads(pickle.dumps(ffd)), ffd)

    def test_continuous_pickle(self):
        ffs = scientific.FragilityFunctionContinuous('LS1', 0, 1, 0, 2.)

        pickle.loads(pickle.dumps(ffs))

    def test_call(self):
        ffs = scientific.FragilityFunctionContinuous('LS1', 0.5, 1, 0, 2.)
        self._close_to(0.26293, ffs(numpy.array([0.1])))

    def test_discrete_ne(self):
        ffd1 = scientific.FragilityFunctionDiscrete('LS1', [], [])
        ffd2 = scientific.FragilityFunctionDiscrete('LS1', [0.1], [0.1])

        self.assertTrue(ffd1 != ffd2)


class InsuredLossesTestCase(unittest.TestCase):
    def test_below_deductible(self):
        aac([0],scientific.insured_losses(numpy.array([0.05]), 0.1, 1))
        aac([0, 0],
            scientific.insured_losses(numpy.array([0.05, 0.1]), 0.1, 1))

    def test_above_limit(self):
        aac([0.4],
            scientific.insured_losses(numpy.array([0.6]), 0.1, 0.5))
        aac([0.4, 0.4],
            scientific.insured_losses(numpy.array([0.6, 0.7]), 0.1, 0.5))

    def test_in_range(self):
        aac([0.2],
            scientific.insured_losses(numpy.array([0.3]), 0.1, 0.5))
        aac([0.2, 0.3],
            scientific.insured_losses(numpy.array([0.3, 0.4]), 0.1, 0.5))

    def test_mixed(self):
        aac([0, 0.1, 0.4],
            scientific.insured_losses(numpy.array([0.05, 0.2, 0.6]), 0.1, 0.5))

    def test_mean(self):
        losses1 = numpy.array([0.05, 0.2, 0.6])
        losses2 = numpy.array([0.01, 0.1, 0.3, 0.55])
        l1 = len(losses1)
        l2 = len(losses2)
        m1 = scientific.insured_losses(losses1, 0.1, 0.5).mean()
        m2 = scientific.insured_losses(losses2, 0.1, 0.5).mean()
        m = scientific.insured_losses(numpy.concatenate([losses1, losses2]),
                                      0.1, 0.5).mean()
        aac((m1 * l1 + m2 * l2) / (l1 + l2), m)


class InsuredLossCurveTestCase(unittest.TestCase):
    def test_curve(self):
        curve = numpy.array(
            [numpy.linspace(0, 1, 11), numpy.linspace(1, 0, 11)])

        aac(numpy.array([[0., 0.1, 0.2, 0.3, 0.4, 0.5],
                         [0.8, 0.8, 0.8, 0.7, 0.6, 0.5]]),
            scientific.insurance_loss_curve(curve, 0.2, 0.5))

    def test_trivial_curve(self):
        curve = numpy.array(
            [numpy.linspace(0, 1, 11), numpy.zeros(11)])

        aac([[0, 0.1, 0.2, 0.3, 0.4, 0.5], [0, 0, 0, 0, 0, 0]],
            scientific.insurance_loss_curve(curve, 0.1, 0.5))


class ClassicalDamageTestCase(unittest.TestCase):
    def test_discrete(self):
        hazard_imls = [0.05, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4]
        fragility_functions = scientific.FragilityFunctionList(
            [], imls=hazard_imls, format='discrete')
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
        aac(poos, [1.0415184E-09, 1.4577245E-06, 1.9585762E-03, 6.9677521E-02,
                   9.2836244E-01], atol=1E-5)

    def test_continuous(self):
        hazard_imls = numpy.array(
            [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6,
             0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15, 1.2,
             1.25, 1.3, 1.35, 1.4])
        fragility_functions = scientific.FragilityFunctionList(
            [], imls=hazard_imls, format='continuous')
        fragility_functions.extend([
            scientific.FragilityFunctionContinuous(
                'slight', 0.160, 0.104, 0, 2.),
            scientific.FragilityFunctionContinuous(
                'moderate', 0.225, 0.158, 0, 2.),
            scientific.FragilityFunctionContinuous(
                'extreme', 0.400, 0.300, 0, 2.),
            scientific.FragilityFunctionContinuous(
                'complete', 0.600, 0.480, 0, 2.),
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
        aac(poos, [0.56652127, 0.12513401, 0.1709355, 0.06555033, 0.07185889])


class LossesByEventTestCase(unittest.TestCase):
    def test_convergency(self):
        # testing convergency of the mean curve
        periods = [10, 20, 50, 100, 150, 200, 250]
        eff_time = 500
        losses = 10**numpy.random.default_rng(42).random(2000)
        losses0 = losses[:1000]
        losses1 = losses[1000:]
        curve0 = scientific.losses_by_period(
            losses0, periods, len(losses0), eff_time)['curve']
        curve1 = scientific.losses_by_period(
            losses1, periods, len(losses1), eff_time)['curve']
        mean = (curve0 + curve1) / 2
        full = scientific.losses_by_period(
            losses, periods, len(losses), 2*eff_time)['curve']
        aac(mean, full, rtol=1E-2)  # converges only at 1%

    def test_maximum_probable_loss(self):
        # checking that MPL does not break summability
        rng = numpy.random.default_rng(42)
        claim = numpy.round(1000 + rng.random(10) * 1000)
        cession = numpy.round(rng.random(10) * 1000)
        period = 2000
        efftime = 10000
        retention = claim - cession
        idxs = numpy.argsort(claim)
        claim_mpl = scientific.maximum_probable_loss(
            claim[idxs], period, efftime, sorting=False)
        cession_mpl = scientific.maximum_probable_loss(
            cession[idxs], period, efftime, sorting=False)
        ret_mpl = scientific.maximum_probable_loss(
            retention[idxs], period, efftime, sorting=False)
        self.assertEqual(claim_mpl, cession_mpl + ret_mpl)
        # print('claim', claim[idxs], claim_mpl)
        # print('cession', cession[idxs], cession_mpl)
        # print('retention', retention[idxs], ret_mpl)
        # [1094. 1128. 1439. 1450. 1697. 1761. 1774. 1786. 1859. 1976.] 1761.
        # [443. 828. 927. 632. 823. 555. 371.  64. 644. 227.] 555.
        # [651. 300. 512. 818. 874. 1206. 1403. 1722. 1215. 1749.] 1206.

    def test_claim(self):
        # curves for claim=cession+retention        
        rng = numpy.random.default_rng(42)
        claim = numpy.round(1000 + rng.random(100) * 1000)
        cession = numpy.round(rng.random(100) * 1000)
        efftime = 100_000
        n = len(claim)
        periods = scientific.return_periods(efftime, n)
        retention = claim - cession
        idxs = numpy.argsort(claim)
        claim_curve = scientific.losses_by_period(
            claim[idxs], periods, n, efftime, sorting=False)['curve']
        cession_curve = scientific.losses_by_period(
            cession[idxs], periods, n, efftime, sorting=False)['curve']
        ret_curve = scientific.losses_by_period(
            retention[idxs], periods, n, efftime, sorting=False)['curve']
        aac(claim_curve, cession_curve + ret_curve)
        print('keeping event associations')
        print('claim', claim_curve)
        print('cession', cession_curve)
        print('retention', ret_curve)
        if PLOTTING:
            _fig, ax = plt.subplots()
            ax.plot(periods, claim_curve, label='claim')
            ax.plot(periods, cession_curve, label='cession')
            ax.plot(periods, ret_curve, label='retention')
            ax.legend()
            plt.show()

        claim_curve = scientific.losses_by_period(
            claim, periods, n, efftime)['curve']
        cession_curve = scientific.losses_by_period(
            cession, periods, n, efftime)['curve']
        ret_curve = scientific.losses_by_period(
            retention, periods, n, efftime)['curve']
        print('not keeping event associations')
        print('claim', claim_curve)
        print('cession', cession_curve)
        print('retention', ret_curve)


class PlaFactorTestCase(unittest.TestCase):
    def test_interp(self):
        rps = [1, 5, 10, 50, 100, 500, 1000]
        factors = [1, 1, 1.092, 1.1738, 1.209, 1.2908, 1.326]
        df = pandas.DataFrame(dict(return_period=rps, pla_factor=factors))
        pla_factor = scientific.pla_factor(df)

        # no interp
        numpy.testing.assert_allclose(pla_factor([1, 1000]), [1, 1.326])

        # interp
        self.assertEqual(pla_factor(1.1), 1.0)
        self.assertAlmostEqual(pla_factor(900), 1.31896)

        # extrap
        self.assertAlmostEqual(pla_factor(0.9), 1.0)
        self.assertAlmostEqual(pla_factor(1001), 1.326)


class ComposeDDSTestCase(unittest.TestCase):
    def test_associative(self):
        comp = scientific.compose_dds
        dd1 = [.8, .1, .1]
        dd2 = [.9, .05, .05]
        dd3 = [.7, .2, .1]
        exp = [0.504, 0.2655, 0.2305]
        dd = comp([comp([dd1, dd2]), dd3])
        aac(exp, dd)
        aac(exp, comp([dd1, dd2, dd3]))


class RiskComputerTestCase(unittest.TestCase):
    def test1(self):
        dic = {'calculation_mode': 'event_based_risk',
               'risk_functions': {
                   'groundshaking#structural#RC':
                   {"openquake.risklib.scientific.VulnerabilityFunction":
                    {"id": "RC",
                     "peril": 'groundshaking',
                     "loss_type": "structural",
                     "imt": "PGA",
                     "imls": [0.1, 0.2, 0.3, 0.5, 0.7],
                     "mean_loss_ratios": [0.0035, 0.07, 0.14, 0.28, 0.56],
                     "covs": [0.0, 0.0, 0.0, 0.0, 0.0],
                     "distribution_name": "LN"}}}}
        gmfs = {'eid': [0, 1],
                'sid': [0, 0],
                'PGA': [.23, .31]}
        rc = riskmodels.get_riskcomputer(dic)
        print(toml.dumps(dic))
        for k, v in rc.todict().items():
            self.assertEqual(dic[k], v)
        asset_df = pandas.DataFrame(
            {'area': [1.0],
             'id': [b'a2'],
             'lat': [38.17],
             'lon': [15.56],
             'site_id': [0],
             'taxonomy': [1],
             'value-number': [2000.0],
             'value-structural': [2000.0]})
        [out] = rc.output(asset_df, pandas.DataFrame(gmfs))
        print(out)

    def test2(self):
        dic = {'calculation_mode': 'event_based_risk',
               'risk_functions': {
                   'groundshaking#nonstructural#RM': {
                       'openquake.risklib.scientific.VulnerabilityFunction': {
                           'covs': [0.0001, 0.0001, 0.0001, 0.0001, 0.0001],
                           'distribution_name': 'LN',
                           'id': 'RM',
                           'imls': [0.1, 0.2, 0.4, 0.7, 1.0],
                           'imt': 'SA(1.0)',
                           'mean_loss_ratios': [0.1, 0.2, 0.35, 0.6, 0.9]}},
                   'groundshaking#structural#RM': {
                       'openquake.risklib.scientific.VulnerabilityFunction': {
                           'covs': [0.0001, 0.0001, 0.0001, 0.0001, 0.0001],
                           'distribution_name': 'LN',
                           'id': 'RM',
                           'imls': [0.02, 0.3, 0.5, 0.9, 1.2],
                           'imt': 'PGA',
                           'mean_loss_ratios': [0.05, 0.1, 0.2, 0.4, 0.8]}}},
               'wdic': {'RM#groundshaking': 1}}

        gmfs = {'eid': [0, 2],
                'sid': [0, 0],
                'PGA': [.23, .31],
                'SA(0.2)': [.23, .41],
                'SA(0.5)': [.23, .51],
                'SA(0.8)': [.23, .32],
                'SA(1.0)': [.23, .21]}
        rc = riskmodels.get_riskcomputer(dic)
        print(toml.dumps(dic))
        asset_df = pandas.DataFrame({
            'area': [10.0, 1.0],
            'id': [b'a0', b'a3'],
            'lat': [29.1098, 27.9015],
            'lon': [81.2985, 85.7477],
            'policy': [2, 1],
            'site_id': [0, 2],
            'taxonomy': [1, 1],
            'value-nonstructural': [1500.0, 2500.0],
            'value-number': [3.0, 10.0],
            'value-structural': [3000.0, 5000.0]})
        [out] = rc.output(asset_df, pandas.DataFrame(gmfs))
        print(out)

    def test3(self):
        # TODO: a case with nontrivial wdic, for instance
        # 'wdic': {'Wood/Com#contents': 1.0,
        #          'Wood1#structural': 0.6,
        #          'Wood2#structural': 0.4}
        # NB: for the same loss type the weights must sum up to 1
        pass

    def test4(self):
        # TODO: a case with secondary losses, for instance
        # seclosses = [partial(total_losses, kind=oq.total_losses)]
        # seclosses = [partial(insurance_losses, policy_df=self.policy_df)]
        pass

    def test_5(self):
        # multi-peril damage
        rcdic = {'calculation_mode': 'scenario_damage',
                 'risk_functions':
                 {'groundshaking#structural#Wood':
                  {'openquake.risklib.scientific.FragilityFunctionList': {
                      'array': [[0.0, 0.5, 0.861, 0.957, 0.985, 0.994, 0.997, 0.999],
                                [0.0, 0.204, 0.6, 0.813, 0.909, 0.954, 0.976, 0.986],
                                [0.0, 0.041, 0.255, 0.49, 0.664, 0.78, 0.855, 0.903],
                                [0.0, 0.007, 0.088, 0.236, 0.394, 0.532, 0.642, 0.728]],
                      'format': 'discrete',
                      'id': 'Wood',
                      'imls': [1e-10, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4],
                      'imt': 'PGA',
                      'kind': 'fragility',
                      'loss_type': 'structural',
                      'nodamage': 0.05,
                      'peril': 'groundshaking'}},
                  'landslide#structural#Wood':
                  {'openquake.risklib.scientific.FragilityFunctionList': {
                      'array': [[0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 1.0],
                                [0.0, 0.0, 0.0, 1.0]],
                      'format': 'discrete',
                      'id': 'Wood',
                      'imls': [1e-10, 0.3, 0.6, 1.0],
                      'imt': 'DispProb',
                      'kind': 'fragility',
                      'loss_type': 'structural',
                      'nodamage': 1e-10,
                      'peril': 'landslide'}}}}
        limit_states = 'slight moderate extreme complete'.split()
        rc = riskmodels.get_riskcomputer(rcdic, limit_states)
        asset_df = pandas.DataFrame({
            'id': ['a1'],
            'lon': [83.31],
            'lat': [29.46],
            'site_id': [0],
            'value-number': [100],
            'value-structural': [11340.],
            'taxonomy': [2]})
        gmf_df = pandas.DataFrame({
            'eid': [0, 1],
            'sid': [0, 0],
            'PGA': [.098234, .165975],
            'DispProb': [.335, .335]})
        dd5 = rc.get_dd5(asset_df, gmf_df)  # (P, A, E, L, D)
        dd0 = dd5[0, 0, 0, 0, 1:]
        dd1 = dd5[0, 0, 1, 0, 1:]
        aac(dd0, [14.538632, 8.006071, 1.669978, 0.343819], atol=1e-6)
        aac(dd1, [24.564302, 13.526962, 2.821575, 0.580912], atol=1e-6)

        rng = scientific.MultiEventRNG(master_seed=42, eids=gmf_df.eid)
        dd5 = rc.get_dd5(asset_df, gmf_df, rng)  # (A, E, L, D)
        dd0 = dd5[0, 0, 0, 0, 1:]
        dd1 = dd5[0, 0, 1, 0, 1:]
        aac(dd0, [10, 8, 4, 0])
        aac(dd1, [31, 14, 3, 0], atol=1e-8)
