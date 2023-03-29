# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
import unittest
import numpy as np
from openquake.hazardlib.imt import SA, PGA
from openquake.hazardlib import const
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.gsim.tromans_2019 import (
    TromansEtAl2019, TromansEtAl2019SigmaMu, HOMOSKEDASTIC_PHI,
    HOMOSKEDASTIC_TAU, HETEROSKEDASTIC_PHI, HETEROSKEDASTIC_TAU,
    get_alatik_youngs_sigma_mu)


class SigmaFunctionsTestCase(unittest.TestCase):
    """
    Tests the general sigma functions
    """
    def setUp(self):
        self.expected_hetero_pga = np.array([[4.0, 0.4700, 0.49],
                                             [4.5, 0.4700, 0.49],
                                             [5.0, 0.4700, 0.49],
                                             [5.5, 0.4425, 0.46],
                                             [6.0, 0.4150, 0.46],
                                             [6.5, 0.3875, 0.46],
                                             [7.0, 0.3600, 0.46],
                                             [7.5, 0.3600, 0.46]])
        self.expected_hetero_sa1 = np.array([[4.0, 0.4700, 0.46],
                                             [4.5, 0.4700, 0.46],
                                             [5.0, 0.4700, 0.46],
                                             [5.5, 0.4425, 0.45],
                                             [6.0, 0.4150, 0.45],
                                             [6.5, 0.3875, 0.45],
                                             [7.0, 0.3600, 0.45],
                                             [7.5, 0.3600, 0.45]])

    def test_heteroskedastic_phi(self):
        mags = self.expected_hetero_pga[:, 0]
        imt = PGA()
        # Central Branch
        phi = HETEROSKEDASTIC_PHI["central"](imt, mags)
        np.testing.assert_array_almost_equal(
            phi, self.expected_hetero_pga[:, 2], 7)

        imt = SA(1.0)
        # Central Branch
        phi = HETEROSKEDASTIC_PHI["central"](imt, mags)
        np.testing.assert_array_almost_equal(
            phi, self.expected_hetero_sa1[:, 2], 7)

    def test_heteroskedastic_tau(self):
        mags = self.expected_hetero_pga[:, 0]
        imt = PGA()
        # Central Branch
        tau = HETEROSKEDASTIC_TAU["central"](imt, mags)
        np.testing.assert_array_almost_equal(
            tau, self.expected_hetero_pga[:, 1], 7)

        imt = SA(1.0)
        # Central Branch
        tau = HETEROSKEDASTIC_TAU["central"](imt, mags)
        np.testing.assert_array_almost_equal(
            tau, self.expected_hetero_sa1[:, 1], 7)

    def test_homoskedastic_phi(self):
        self.assertEqual(HOMOSKEDASTIC_PHI["central"](PGA()), 0.46)
        self.assertEqual(HOMOSKEDASTIC_PHI["central"](SA(1.0)), 0.45)

    def test_homoskedastic_tau(self):
        self.assertEqual(HOMOSKEDASTIC_TAU["central"](PGA()), 0.415)
        self.assertEqual(HOMOSKEDASTIC_TAU["central"](SA(1.0)), 0.415)

    def test_homoskedastic_phi_branches(self):
        mags = self.expected_hetero_pga[:, 0]
        central = HOMOSKEDASTIC_PHI["central"](PGA())
        lower = HOMOSKEDASTIC_PHI["lower"](PGA())
        upper = HOMOSKEDASTIC_PHI["upper"](PGA())
        np.testing.assert_array_almost_equal(
            lower / central, 0.84 * np.ones(len(mags)))
        np.testing.assert_array_almost_equal(
            upper / central, 1.16 * np.ones(len(mags)))

    def test_homoskedastic_tau_branches(self):
        central = HOMOSKEDASTIC_TAU["central"](PGA())
        lower = HOMOSKEDASTIC_TAU["lower"](PGA())
        upper = HOMOSKEDASTIC_TAU["upper"](PGA())
        np.testing.assert_array_almost_equal(lower, central - 0.075)
        np.testing.assert_array_almost_equal(upper, central + 0.075)


class TromansEtAl2019AdjustmentsTestCase(unittest.TestCase):
    """
    Test case for the various adjustments of the Tromans et al. (2019)
    GMPE using the Bindi et al. (2014) model for the base GMPE.
    """
    def setUp(self):
        """
        """
        self.gsim = TromansEtAl2019
        self.ctx = RuptureContext()
        self.ctx.mag = 6.5
        self.ctx.rake = 0.
        self.ctx.rjb = self.ctx.rrup = np.array([5., 10., 20., 50., 100.])
        self.ctx.vs30 = 500. * np.ones(5)
        self.ctx.sids = np.arange(5)

    def _compare_arrays(self, arr1, arr2, diffs):
        """
        Compares two means that differ by an adjustment factor
        """
        np.testing.assert_array_almost_equal(np.exp(arr1) / np.exp(arr2),
                                             diffs * np.ones(arr1.shape))

    def test_scaling_factors(self):
        gsim_1 = self.gsim("BindiEtAl2014Rjb", branch="central",
                           scaling_factor=1.2)

        gsim_2 = self.gsim("BindiEtAl2014Rjb", branch="central")

        mean_1 = gsim_1.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                             PGA(), [const.StdDev.TOTAL])[0]
        mean_2 = gsim_2.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                             PGA(), [const.StdDev.TOTAL])[0]
        self._compare_arrays(mean_1, mean_2, 1.2)

    def test_vskappa_scaling(self):
        vskappa_dict = {"PGA": 1.2, "SA(0.2)": 1.3, "SA(1.0)": 1.4}
        gsim_1 = self.gsim("BindiEtAl2014Rjb", branch="central",
                           vskappa=vskappa_dict)

        gsim_2 = self.gsim("BindiEtAl2014Rjb", branch="central")
        # PGA
        self._compare_arrays(
            gsim_1.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                        PGA(), [const.StdDev.TOTAL])[0],
            gsim_2.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                        PGA(), [const.StdDev.TOTAL])[0], 1.2)

        # SA(0.2)
        self._compare_arrays(
            gsim_1.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                        SA(0.2), [const.StdDev.TOTAL])[0],
            gsim_2.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                        SA(0.2), [const.StdDev.TOTAL])[0], 1.3)
        # SA(1.0)
        self._compare_arrays(
            gsim_1.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                        SA(1.0), [const.StdDev.TOTAL])[0],
            gsim_2.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                        SA(1.0), [const.StdDev.TOTAL])[0], 1.4)


class TromansEtAl2019SigmaMuTestCase(TromansEtAl2019AdjustmentsTestCase):
    """
    Tests the Tromans et al (2019) GMPE with the sigma mu adjustment
    """
    def setUp(self):
        self.gsim = TromansEtAl2019SigmaMu
        self.ctx = RuptureContext()
        self.ctx.mag = 6.5
        self.ctx.rake = 0.
        self.ctx.rjb = self.ctx.rrup = np.array([5., 10., 20., 50., 100.])
        self.ctx.vs30 = 500. * np.ones(5)
        self.ctx.sids = np.arange(5)

    def test_alatik_youngs_factors(self):
        self.assertAlmostEqual(
            get_alatik_youngs_sigma_mu(5.0, -90., PGA()),
            0.121)
        self.assertAlmostEqual(
            get_alatik_youngs_sigma_mu(5.0, -90., SA(0.5)),
            0.121)
        self.assertAlmostEqual(
            get_alatik_youngs_sigma_mu(7.5, -90., SA(0.5)),
            0.149)
        self.assertAlmostEqual(
            get_alatik_youngs_sigma_mu(5.0, -90., SA(np.exp(1))),
            0.1381)
        self.assertAlmostEqual(
            get_alatik_youngs_sigma_mu(5.0, 90., SA(0.2)),
            0.083)

    def test_sigma_mu_scaling(self):
        gsim_1 = self.gsim("BindiEtAl2014Rjb", branch="central",
                           sigma_mu_epsilon=1.0)

        gsim_2 = self.gsim("BindiEtAl2014Rjb", branch="central")

        mean_1 = gsim_1.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                             PGA(), [const.StdDev.TOTAL])[0]
        mean_2 = gsim_2.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                             PGA(), [const.StdDev.TOTAL])[0]
        self._compare_arrays(mean_1, mean_2, np.exp(0.083))


class TromansEtAl2019TestCaseCentralHomo(BaseGSIMTestCase):
    """
    Tests the standard deviation model of the Tromans et al. (2019) GMPE
    for the central branch with homoskedastic sigma
    """
    GSIM_CLASS = TromansEtAl2019

    def test_std_total(self):
        self.check(
            "./tromans_2019/Tromans_2019_TOTAL_STDDEV_HOMO_CENTRAL.csv",
            max_discrep_percentage=0.01, gmpe_name="BindiEtAl2014Rjb",
            branch="central", homoskedastic_sigma=True)


class TromansEtAl2019TestCaseLowerHomo(BaseGSIMTestCase):
    """
    Tests the standard deviation model of the Tromans et al. (2019) GMPE
    for the lower branch with homoskedastic sigma
    """
    GSIM_CLASS = TromansEtAl2019

    def test_std_total(self):
        self.check(
            "./tromans_2019/Tromans_2019_TOTAL_STDDEV_HOMO_LOWER.csv",
            max_discrep_percentage=0.01, gmpe_name="BindiEtAl2014Rjb",
            branch="lower", homoskedastic_sigma=True)


class TromansEtAl2019TestCaseUpperHomo(BaseGSIMTestCase):
    """
    Tests the standard deviation model of the Tromans et al. (2019) GMPE
    for the lower branch with homoskedastic sigma
    """
    GSIM_CLASS = TromansEtAl2019

    def test_std_total(self):
        self.check(
            "./tromans_2019/Tromans_2019_TOTAL_STDDEV_HOMO_UPPER.csv",
            max_discrep_percentage=0.01, gmpe_name="BindiEtAl2014Rjb",
            branch="upper", homoskedastic_sigma=True)


class TromansEtAl2019TestCaseCentralHetero(BaseGSIMTestCase):
    """
    Tests the standard deviation model of the Tromans et al. (2019) GMPE
    for the central branch with heteroskedastic sigma
    """
    GSIM_CLASS = TromansEtAl2019

    def test_std_total(self):
        self.check(
            "./tromans_2019/Tromans_2019_TOTAL_STDDEV_HETERO_CENTRAL.csv",
            max_discrep_percentage=0.01, gmpe_name="BindiEtAl2014Rjb",
            branch="central", homoskedastic_sigma=False)


class TromansEtAl2019TestCaseLowerHetero(BaseGSIMTestCase):
    """
    Tests the standard deviation model of the Tromans et al. (2019) GMPE
    for the lower branch with heteroskedastic sigma
    """
    GSIM_CLASS = TromansEtAl2019

    def test_std_total(self):
        self.check(
            "./tromans_2019/Tromans_2019_TOTAL_STDDEV_HETERO_LOWER.csv",
            max_discrep_percentage=0.01, gmpe_name="BindiEtAl2014Rjb",
            branch="lower", homoskedastic_sigma=False)


class TromansEtAl2019TestCaseUpperHetero(BaseGSIMTestCase):
    """
    Tests the standard deviation model of the Tromans et al. (2019) GMPE
    for the lower branch with heteroskedastic sigma
    """
    GSIM_CLASS = TromansEtAl2019

    def test_std_total(self):
        self.check(
            "./tromans_2019/Tromans_2019_TOTAL_STDDEV_HETERO_UPPER.csv",
            max_discrep_percentage=0.01, gmpe_name="BindiEtAl2014Rjb",
            branch="upper", homoskedastic_sigma=False)
