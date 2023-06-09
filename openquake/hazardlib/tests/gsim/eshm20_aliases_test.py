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
"""
Test cases for the ESHM20 alias GMPEs
"""
import unittest
import numpy as np
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib import valid
from openquake.hazardlib.gsim.base import gsim_aliases
from openquake.hazardlib.gsim.kotha_2020 import\
    KothaEtAl2020ESHM20, eshm20_crust_lines, ICELAND_dL2L
from openquake.hazardlib.gsim.eshm20_craton import ESHM20Craton
from openquake.hazardlib.gsim.bchydro_2016_epistemic import\
    BCHydroESHM20SInter, BCHydroESHM20SSlab

MILLER_RICE_GAUSS_3PNT = [-1.732051, 0.0, 1.732051]
MILLER_RICE_GAUSS_5PNT = [-2.856970, -1.355630, 0.0, 1.355630, 2.856970]
STRESS_BRANCHES = ["VLow", "Low", "Mid", "High", "VHigh"]
SITE_BRANCHES = ["Low", "Mid", "High"]
ATTEN_BRANCHES = ["Fast", "Mid", "Slow"]
THETA_6_ADJUSTMENTS = [-0.0015, 0.0000, 0.0015]


def compare_gmms(alias_gmm, gmm, ctx, imts):
    """
    Ensure that the alias provides the same outputs as the original GMM
    with the corresponding adjustments
    """
    shape = [len(imts), ctx.size()]
    # Get the median ground motions for the alias GMM
    median_alias = np.zeros(shape)
    alias_gmm.compute(
        ctx, imts, median_alias,
        np.zeros(shape), np.zeros(shape), np.zeros(shape)
        )
    # Get the median ground motions for the original adjusted GMM
    median_gmm = np.zeros(shape)
    gmm.compute(
        ctx, imts, median_gmm,
        np.zeros(shape), np.zeros(shape), np.zeros(shape)
        )
    np.testing.assert_array_almost_equal(median_alias, median_gmm)


class ESHM20ShallowAliasesTestCase(unittest.TestCase):
    """Suite of tests to ensure that the ESHM20 shallow crustal GMPE aliases
    agree with the expected adjusted GMPEs
    """
    def setUp(self):
        # Build the context object
        self.ctx = RuptureContext()
        self.ctx.mag = np.array(([4.5] * 4) + ([5.5] * 4) + ([6.5] * 4))
        self.ctx.rjb = np.tile(
            np.array([20.0, 50.0, 100.0, 200.0]),
            [1, 3]).flatten()
        self.ctx.hypo_depth = 10.0 * np.ones(self.ctx.rjb.shape)
        self.ctx.vs30 = 800.0 * np.ones(self.ctx.rjb.shape)
        self.ctx.vs30measured = np.ones(self.ctx.rjb.shape, dtype=bool)
        self.ctx.region = np.zeros(self.ctx.rjb.shape, dtype=int)
        self.ctx.sids = np.arange(0, len(self.ctx.rjb), 1)
        self.imts = [PGA(), SA(0.2), SA(1.0)]

    def test_eshm20_shallow_gmpe_aliases(self):
        # Shallow crustal GMPE adjustments
        for line in eshm20_crust_lines:
            alias, sigma_mu_eps, c3_eps = line.split()
            adjustments = {"sigma_mu_epsilon": float(sigma_mu_eps),
                           "c3_epsilon": float(c3_eps)}
            alias_gmm = valid.gsim(alias)
            gmm = KothaEtAl2020ESHM20(**adjustments)
            compare_gmms(alias_gmm, gmm, self.ctx, self.imts)

    def test_eshm20_iceland_gmpe_aliases(self):
        # Icelandic GMPE adjustments
        for stress in STRESS_BRANCHES:
            dl2l = dict(list(zip(ICELAND_dL2L["IMTs"], ICELAND_dL2L[stress])))
            for atten, atten_adj in zip(ATTEN_BRANCHES,
                                        MILLER_RICE_GAUSS_3PNT):
                alias = "ESHM20Iceland{:s}Stress{:s}Atten".format(stress,
                                                                  atten)
                alias = gsim_aliases[alias]
                alias_gmm = valid.gsim(alias)
                gmm = KothaEtAl2020ESHM20(dl2l=dl2l, c3_epsilon=atten_adj)
                compare_gmms(alias_gmm, gmm, self.ctx, self.imts)


class ESHM20CratonAliasesTestCase(unittest.TestCase):
    """Suite of tests to ensure that the ESHM20 craton GMPE aliases agree with
    the expected adjusted GMPEs
    """
    def setUp(self):
        # Build the context object
        self.ctx = RuptureContext()
        self.ctx.mag = np.array(([4.5] * 4) + ([5.5] * 4) + ([6.5] * 4))
        self.ctx.rrup = np.tile(
            np.array([20.0, 50.0, 100.0, 200.0]),
            [1, 3]).flatten()
        self.ctx.rjb = np.copy(self.ctx.rrup)
        self.ctx.vs30 = 800.0 * np.ones(self.ctx.rjb.shape)
        self.ctx.hypo_depth = 10.0 * np.ones(self.ctx.rjb.shape)
        self.ctx.vs30measured = np.ones(self.ctx.rjb.shape, dtype=bool)
        self.ctx.sids = np.arange(0, len(self.ctx.rjb), 1)
        self.ctx.region = np.zeros(len(self.ctx.rjb), dtype=int)
        self.imts = [PGA(), SA(0.2), SA(1.0)]

    def test_eshm20_craton_gmpe_aliases(self):
        # Craton GMPE adjustments
        for stress, stress_adj in zip(STRESS_BRANCHES, MILLER_RICE_GAUSS_5PNT):
            for site, site_adj in zip(SITE_BRANCHES, MILLER_RICE_GAUSS_3PNT):
                alias = "ESHM20Craton{:s}Stress{:s}Site".format(stress, site)
                alias_gmm = valid.gsim(alias)
                gmm = ESHM20Craton(epsilon=stress_adj,
                                   site_epsilon=site_adj)
                compare_gmms(alias_gmm, gmm, self.ctx, self.imts)

    def test_eshm20_craton_shallow_aliases(self):
        # Shallow GMPE adjustments for the Craton region
        compare_gmms(
            valid.gsim("ESHM20CratonShallowHighStressMidAtten"),
            KothaEtAl2020ESHM20(sigma_mu_epsilon=1.732051),
            self.ctx,
            self.imts
        )

        compare_gmms(
            valid.gsim("ESHM20CratonShallowHighStressSlowAtten"),
            KothaEtAl2020ESHM20(sigma_mu_epsilon=1.732051,
                                c3_epsilon=1.732051),
            self.ctx,
            self.imts
        )

        compare_gmms(
            valid.gsim("ESHM20CratonShallowMidStressMidAtten"),
            KothaEtAl2020ESHM20(),
            self.ctx,
            self.imts
        )

        compare_gmms(
            valid.gsim("ESHM20CratonShallowMidStressSlowAtten"),
            KothaEtAl2020ESHM20(c3_epsilon=1.732051),
            self.ctx,
            self.imts
        )


class ESHM20SubductionAliasesTestCase(unittest.TestCase):
    """Suite of tests to ensure that the ESHM20 subduction GMPE aliases agree
    with the expected adjusted GMPEs
    """
    def setUp(self):
        # Build the context object for the subduction GMPEs
        self.ctx = RuptureContext()
        self.ctx.mag = np.array(([5.0] * 4) + ([6.5] * 4) + ([8.0] * 4))
        self.ctx.rrup = np.tile(
            np.array([20.0, 50.0, 100.0, 200.0]),
            [1, 3]).flatten()
        self.ctx.rhypo = np.tile(
            np.array([60.0, 100.0, 150.0, 250.0]),
            [1, 3]).flatten()
        self.ctx.xvf = np.tile(np.array([100.0, 80.0, 0.0, -100.0]),
                               [1, 3]).flatten()
        self.ctx.vs30 = 800.0 * np.ones(self.ctx.rrup.shape)
        self.ctx.hypo_depth = 60.0 * np.ones(self.ctx.rrup.shape)
        self.ctx.sids = np.arange(0, len(self.ctx.rrup), 1)
        self.imts = [PGA(), SA(0.2), SA(1.0)]

    def test_eshm20_sinter_aliases(self):
        # Tests the adjustments for the Interface GMPEs
        for stress, stress_adj in zip(STRESS_BRANCHES, MILLER_RICE_GAUSS_5PNT):
            for atten, theta6 in zip(ATTEN_BRANCHES, THETA_6_ADJUSTMENTS):
                alias = "ESHM20SInter{:s}Stress{:s}Atten".format(stress, atten)
                alias_gmm = valid.gsim(alias)
                gmm = BCHydroESHM20SInter(sigma_mu_epsilon=stress_adj,
                                          theta6_adjustment=theta6,
                                          faba_taper_model="SFunc",
                                          a=-100.0, b=100.0)
                compare_gmms(alias_gmm, gmm, self.ctx, self.imts)

    def test_eshm20_sslab_aliases(self):
        # Tests the adjustments for the Inslab GMPEs
        for stress, stress_adj in zip(STRESS_BRANCHES, MILLER_RICE_GAUSS_5PNT):
            for atten, theta6 in zip(ATTEN_BRANCHES, THETA_6_ADJUSTMENTS):
                alias = "ESHM20SSlab{:s}Stress{:s}Atten".format(stress, atten)
                alias_gmm = valid.gsim(alias)
                gmm = BCHydroESHM20SSlab(sigma_mu_epsilon=stress_adj,
                                         theta6_adjustment=theta6,
                                         faba_taper_model="SFunc",
                                         a=-100.0, b=100.0)
                compare_gmms(alias_gmm, gmm, self.ctx, self.imts)
