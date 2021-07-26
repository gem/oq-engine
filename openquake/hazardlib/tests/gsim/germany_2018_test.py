# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
import copy
import unittest
import numpy as np
from openquake.hazardlib.imt import SA, PGA
from openquake.hazardlib import const
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.gsim.cauzzi_2014 import CauzziEtAl2014RhypoGermany
from openquake.hazardlib.gsim.derras_2014 import DerrasEtAl2014RhypoGermany
from openquake.hazardlib.gsim.akkar_2014 import AkkarEtAlRhyp2014
from openquake.hazardlib.gsim.bindi_2014 import BindiEtAl2014Rhyp
from openquake.hazardlib.gsim.bindi_2017 import BindiEtAl2017Rhypo

# First Test the Cauzzi et al. (2014) and Derras et al., (2014) adjustments
# using test tables generated from the FRISK implementation


class CauzziEtAl2014RhypTestCase(BaseGSIMTestCase):
    """
    Implements the Cauzzi et al. (2014) Rhypo adjusted GMPE test

    Test tables for corrected GMPE verified against original FRISK version
    """
    GSIM_CLASS = CauzziEtAl2014RhypoGermany

    MEAN_FILE = "germany_2018/C14_RHYPO_ADJUSTMENT_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)


class CauzziEtAl2014RhypFiniteRuptureTestCase(BaseGSIMTestCase):
    """
    Implements the Cauzzi et al. (2014) Rhypo adjusted GMPE test for the case
    of a finite rupture (i.e. should use rrup rather than rhypo)

    Test tables for corrected GMPE verified against original FRISK version
    """
    GSIM_CLASS = CauzziEtAl2014RhypoGermany

    MEAN_FILE = "germany_2018/C14_RHYPO_FINITE_RUPTURE_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)


class DerrasEtAl2014RhypTestCase(CauzziEtAl2014RhypTestCase):
    """
    Implements the Derras et al. (2014) Rhypo adjusted GMPE test

    Test tables for corrected GMPE verified against original FRISK version
    """
    GSIM_CLASS = DerrasEtAl2014RhypoGermany
    MEAN_FILE = "germany_2018/D14_RHYPO_ADJUSTMENT_MEAN.csv"


class DerrasEtAl2014RhypFiniteRuptureTestCase(CauzziEtAl2014RhypTestCase):
    """
    Implements the Derras et al. (2014) Rhypo adjusted GMPE test for the case
    of a finite rupture (i.e. should use rjb rather than rhypo)

    Test tables for corrected GMPE verified against original FRISK version
    """
    GSIM_CLASS = DerrasEtAl2014RhypoGermany
    MEAN_FILE = "germany_2018/D14_RHYPO_FINITE_RUPTURE_MEAN.csv"


class GermanyStressParameterAdjustmentTestCase(unittest.TestCase):
    """
    Test suite to verify the stress parameter adjustments for GMPEs adopted
    within the German national seismic hazard model.
    """
    def setUp(self):
        """
        Setup with a set of distances and site paramwters
        """
        self.imts = [PGA(), SA(0.1), SA(0.2), SA(0.5), SA(1.0), SA(2.0)]
        self.mags = [4.5, 5.5, 6.5, 7.5]
        self.rakes = [-90., 0., 90.]
        self.ctx = RuptureContext()
        self.ctx.sids = np.arange(5)
        self.ctx.rhypo = np.array([5., 10., 20., 50., 100.])
        self.ctx.vs30 = 800.0 * np.ones(5)

    def check_gmpe_adjustments(self, adj_gmpe_set, original_gmpe):
        """
        Takes a set of three adjusted GMPEs representing the "low", "middle"
        and "high" stress drop adjustments for Germany and compares them
        against the original "target" GMPE for a variety of magnitudes
        and styles of fauling.
        """
        low_gsim, mid_gsim, high_gsim = adj_gmpe_set
        tot_std = [const.StdDev.TOTAL]
        for imt in self.imts:
            for mag in self.mags:
                for rake in self.rakes:
                    ctx = copy.copy(self.ctx)
                    ctx.mag = mag
                    ctx.rake = rake
                    ctx.hypo_depth = 10.
                    ctx.width = 0.0001
                    # Get "original" values
                    mean = original_gmpe.get_mean_and_stddevs(
                        ctx, ctx, ctx, imt, tot_std)[0]
                    mean = np.exp(mean)
                    # Get "low" adjustments (0.75 times the original)
                    low_mean = low_gsim.get_mean_and_stddevs(
                        ctx, ctx, ctx, imt, tot_std)[0]
                    np.testing.assert_array_almost_equal(
                        np.exp(low_mean) / mean, 0.75 * np.ones_like(low_mean))

                    # Get "middle" adjustments (1.25 times the original)
                    mid_mean = mid_gsim.get_mean_and_stddevs(
                        ctx, ctx, ctx, imt, tot_std)[0]
                    np.testing.assert_array_almost_equal(
                        np.exp(mid_mean) / mean, 1.25 * np.ones_like(mid_mean))

                    # Get "high" adjustments (1.5 times the original)
                    high_mean = high_gsim.get_mean_and_stddevs(
                        ctx, ctx, ctx, imt, tot_std)[0]
                    np.testing.assert_array_almost_equal(
                        np.exp(high_mean) / mean,
                        1.5 * np.ones_like(high_mean))

    def test_akkar_germany_adjustments(self):
        adj_gmpes = [AkkarEtAlRhyp2014(adjustment_factor=0.75),
                     AkkarEtAlRhyp2014(adjustment_factor=1.25),
                     AkkarEtAlRhyp2014(adjustment_factor=1.50)]
        self.check_gmpe_adjustments(adj_gmpes, AkkarEtAlRhyp2014())

    def test_bindi_2014_germany_adjustments(self):
        adj_gmpes = [BindiEtAl2014Rhyp(adjustment_factor=0.75),
                     BindiEtAl2014Rhyp(adjustment_factor=1.25),
                     BindiEtAl2014Rhyp(adjustment_factor=1.50)]
        self.check_gmpe_adjustments(adj_gmpes, BindiEtAl2014Rhyp())

    def test_cauzzi_germany_adjustments(self):
        adj_gmpes = [CauzziEtAl2014RhypoGermany(adjustment_factor=0.75),
                     CauzziEtAl2014RhypoGermany(adjustment_factor=1.25),
                     CauzziEtAl2014RhypoGermany(adjustment_factor=1.50)]
        self.check_gmpe_adjustments(adj_gmpes, CauzziEtAl2014RhypoGermany())

    def test_derras_germany_adjustments(self):
        adj_gmpes = [DerrasEtAl2014RhypoGermany(adjustment_factor=0.75),
                     DerrasEtAl2014RhypoGermany(adjustment_factor=1.25),
                     DerrasEtAl2014RhypoGermany(adjustment_factor=1.50)]
        self.check_gmpe_adjustments(adj_gmpes, DerrasEtAl2014RhypoGermany())

    def test_bindi_2017_germany_adjustments(self):
        adj_gmpes = [BindiEtAl2017Rhypo(adjustment_factor=0.75),
                     BindiEtAl2017Rhypo(adjustment_factor=1.25),
                     BindiEtAl2017Rhypo(adjustment_factor=1.50)]
        self.check_gmpe_adjustments(adj_gmpes, BindiEtAl2017Rhypo())
