# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

"""
Implements the set of tests for the NSHMP adjustments to the NGA West 2
Ground Motion Prediction Equations

Each of the test tables is generated from the original GMPE tables, which are
subsequently modified using the adjustment factors presented in the module
openquake.hazardlib.gsim.nshmp_2014
"""
import unittest
import numpy as np
from openquake.hazardlib.gsim.nshmp_2014 import (
    NSHMP2014, nga_west2_epistemic_adjustment)
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import \
    CampbellBozorgnia2014
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.idriss_2014 import Idriss2014
from openquake.hazardlib.geo import Point, Line, SimpleFaultSurface
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class AdjustmentFactorTestCase(unittest.TestCase):
    """
    Tests that the basic adjustment factors are being applied correctly
    """
    def setUp(self):
        """
        Instantiate with three distances
        """
        self.distance = np.array([5.0, 15.0, 50.0])

    def test_good_case(self):
        """
        Basic tests to ensure correct adjustment factors
        """
        # Magnitude < 6.0
        np.testing.assert_array_almost_equal(
            nga_west2_epistemic_adjustment(5.5, self.distance),
            np.array([0.37, 0.22, 0.22]))
        # 6.0 < Magnitude < 7.0
        np.testing.assert_array_almost_equal(
            nga_west2_epistemic_adjustment(6.5, self.distance),
            np.array([0.25, 0.23, 0.23]))
        # Magnitude > 7.0
        np.testing.assert_array_almost_equal(
            nga_west2_epistemic_adjustment(7.5, self.distance),
            np.array([0.40, 0.36, 0.33]))


class NSHMP2014TestCase(BaseGSIMTestCase):
    """
    Implements the test case for the positive ('upper') epistemic adjustment
    of the Abrahamson et al. (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = NSHMP2014

    def test_AbrahamsonEtAl2014Upper(self):
        self.check('NSHMP2014/ASK14_NSHMP_UPPER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='AbrahamsonEtAl2014', sgn=1)

    def test_AbrahamsonEtAl2014Lower(self):
        self.check('NSHMP2014/ASK14_NSHMP_LOWER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='AbrahamsonEtAl2014', sgn=-1)

    def test_BooreEtAl2014Upper(self):
        self.check('NSHMP2014/BSSA14_NSHMP_UPPER_MEAN.csv',
                   max_discrep_percentage=2.0,
                   gmpe_name='BooreEtAl2014', sgn=1)

    def test_BooreEtAl2014Lower(self):
        self.check('NSHMP2014/BSSA14_NSHMP_LOWER_MEAN.csv',
                   max_discrep_percentage=2.0,
                   gmpe_name='BooreEtAl2014', sgn=-1)

    def test_CampbellBozorgnia2014Upper(self):
        self.check('NSHMP2014/CB14_NSHMP_UPPER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='CampbellBozorgnia2014', sgn=1)

    def test_CampbellBozorgnia2014Lower(self):
        self.check('NSHMP2014/CB14_NSHMP_LOWER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='CampbellBozorgnia2014', sgn=-1)

    def test_ChiouYoungs2014NSHMPUpper(self):
        self.check('NSHMP2014/CY14_NSHMP_UPPER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='ChiouYoungs2014', sgn=1)

    def test_ChiouYoungs2014NSHMPLower(self):
        self.check('NSHMP2014/CY14_NSHMP_LOWER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='ChiouYoungs2014', sgn=-1)

    def test_Idriss2014NSHMPUpper(self):
        self.check('NSHMP2014/IDRISS14_NSHMP_UPPER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='Idriss2014', sgn=1)

    def test_Idriss2014NSHMPLower(self):
        self.check('NSHMP2014/IDRISS14_NSHMP_LOWER_MEAN.csv',
                   max_discrep_percentage=MEAN_DISCREP,
                   gmpe_name='Idriss2014', sgn=-1)


class GeneralEquivalenceTestCase(unittest.TestCase):
    """
    The epistemic uncertainty model for the NGA West 2 models in the Western
    US is typically run to return the weighted average. For the mean curves
    we can either run each GMPE separately in the logic tree and take the
    weighted mean curve, or we can apply the weighting in-place inside the
    GMPE (thus running the GMPE only once). This tests verifies the near
    equivalence of the two methods
    """
    def setUp(self):
        """
        Builds a simple dipping/bending fault source with a characteristic
        source model. Compares the curves for four sites, two on the hanging
        wall and two on the footwall.
        The source model is taken from the PEER Tests
        """
        point_order_dipping_east = [Point(-64.78365, -0.45236),
                                    Point(-64.80164, -0.45236),
                                    Point(-64.90498, -0.36564),
                                    Point(-65.0000, -0.16188),
                                    Point(-65.0000, 0.0000)]
        trace_dip_east = Line(point_order_dipping_east)
        site_1 = Site(Point(-64.98651, -0.15738), 760.0, 48.0, 0.607,
                      vs30measured=True)
        site_2 = Site(Point(-64.77466, -0.45686), 760.0, 48.0, 0.607,
                      vs30measured=True)
        site_3 = Site(Point(-64.92747, -0.38363), 760.0, 48.0, 0.607,
                      vs30measured=True)
        site_4 = Site(Point(-65.05396, -0.17088), 760.0, 48.0, 0.607,
                      vs30measured=True)
        self.sites = SiteCollection([site_1, site_2, site_3, site_4])
        self.imtls = {"PGA": [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3,
                              0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9,
                              1.0]}
        fault_surface1 = SimpleFaultSurface.from_fault_data(
            trace_dip_east, 0.0, 12.0, 60., 0.5)
        mfd1 = EvenlyDiscretizedMFD(6.75, 0.01, [0.01])
        tom = PoissonTOM(1.0)
        self.sources = [
            CharacteristicFaultSource(
                "PEER_CHAR_FLT_EAST",
                "Peer Bending Fault Dipping East - Characteristic",
                "Active Shallow Crust",
                mfd1,
                tom,
                fault_surface1,
                90.0)]
        # We will check all the GMPEs
        self.gsim_set = {
            "ASK": [
                NSHMP2014(gmpe_name='AbrahamsonEtAl2014', sgn=0),
                (0.185, NSHMP2014(gmpe_name='AbrahamsonEtAl2014', sgn=-1)),
                (0.63, AbrahamsonEtAl2014()),
                (0.185, NSHMP2014(gmpe_name='AbrahamsonEtAl2014', sgn=1))],
            "BSSA": [
                NSHMP2014(gmpe_name='BooreEtAl2014', sgn=0),
                (0.185, NSHMP2014(gmpe_name='BooreEtAl2014', sgn=-1)),
                (0.63, BooreEtAl2014()),
                (0.185, NSHMP2014(gmpe_name='BooreEtAl2014', sgn=1))],
            "CB": [
                NSHMP2014(gmpe_name='CampbellBozorgnia2014', sgn=0),
                (0.185, NSHMP2014(gmpe_name='CampbellBozorgnia2014', sgn=-1)),
                (0.63, CampbellBozorgnia2014()),
                (0.185, NSHMP2014(gmpe_name='CampbellBozorgnia2014', sgn=1))],
            "CY": [
                NSHMP2014(gmpe_name='ChiouYoungs2014', sgn=0),
                (0.185, NSHMP2014(gmpe_name='ChiouYoungs2014', sgn=-1)),
                (0.63, ChiouYoungs2014()),
                (0.185, NSHMP2014(gmpe_name='ChiouYoungs2014', sgn=1))],
            "ID": [
                NSHMP2014(gmpe_name='Idriss2014', sgn=0),
                (0.185, NSHMP2014(gmpe_name='Idriss2014', sgn=-1)),
                (0.63, Idriss2014()),
                (0.185, NSHMP2014(gmpe_name='Idriss2014', sgn=1))]}

    def _verify_curves(self, gsim_name, truncation_level, ndp=3):
        """
        Implements the core verification. Initially the hazard calculation is
        run with the "Mean" GMPE (this has the mean weightings inside the
        GMPE). Then the "low", "average" and "high" cases are run separately
        and the resulting curves summed with their respective weights.

        A small degree of mismatch is found though this typically takes
        place at very low probabilities. Curves are compared in the logarithmic
        domain (ignoring 0 values)
        """
        gsim0 = {"Active Shallow Crust": self.gsim_set[gsim_name][0]}
        # Run new weighted mean curve
        wmean_curve = calc_hazard_curves(self.sources, self.sites, self.imtls,
                                         gsim0, truncation_level)
        # Now run low, mid and high curves
        curves = {"PGA": np.zeros_like(wmean_curve["PGA"])}
        for iloc in range(1, 4):
            gsim_i = {
                "Active Shallow Crust": self.gsim_set[gsim_name][iloc][1]}
            wgt = self.gsim_set[gsim_name][iloc][0]
            curves["PGA"] += (
                wgt * calc_hazard_curves(self.sources,
                                         self.sites,
                                         self.imtls,
                                         gsim_i,
                                         truncation_level)["PGA"])
        # Ignore cases where values are equal to zero
        idx = wmean_curve["PGA"] > 0.0
        np.testing.assert_array_almost_equal(
            np.log(wmean_curve["PGA"][idx]), np.log(curves["PGA"][idx]), ndp)

    def test_nshmp_wus_curves_normal_truncation(self):
        # Test the case with a conventional truncation value (3.)
        truncation = 3.0
        for gsim_name in ["ASK", "BSSA", "CB", "CY", "ID"]:
            self._verify_curves(gsim_name, truncation)

    def test_nshmp_wus_curves_zero_truncation(self):
        # Test the case with truncation set to zero
        truncation = 0
        for gsim_name in ["ASK", "BSSA", "CB", "CY", "ID"]:
            self._verify_curves(gsim_name, truncation, ndp=2)
