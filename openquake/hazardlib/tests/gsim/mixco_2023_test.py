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
Test the Mixco et al. (2023) GMPE. This GMPE is a recalibration of the Kotha
et al. (2020) GMPE. Similarly to the Kotha et al. 2020 gsim, this gsim 
considers a baseline class, an automatic regionalisation class and two classes
with a site term considered (vs30 and slope-based site terms).
"""
import unittest
import pandas as pd
import numpy as np
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.mixco_2023 import (
    MixcoEtAl2023, MixcoEtAl2023Site, MixcoEtAl2023Slope, MixcoEtAl2023regional)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.mixco_2023 import get_distance_coefficients_2, get_dl2l


MAX_DISCREP = 1


# Build the c3 and dl2l input tables
c3 = CoeffsTable(sa_damping=5, table="""\
imt	              c3	tau_c3
pgv	    -0.066180908	0.143248159
pga	    -0.354727717	0.184023656
0.010	-0.350694830	0.184487029
0.025	-0.318827822	0.242576529
0.040	-0.394518934	0.244924967
0.050	-0.470347311	0.228729188
0.070	-0.511385083	0.233356965
0.100	-0.527152599	0.223976733
0.150	-0.562804873	0.325620872
0.200	-0.530656607	0.306029436
0.250	-0.540404267	0.327027893
0.300	-0.471301479	0.306656289
0.350	-0.451479445	0.286486735
0.400	-0.401443197	0.306236310
0.450	-0.385126425	0.292081260
0.500	-0.363230061	0.265560344
0.600	-0.292144971	0.249033607
0.700	-0.196069821	0.278934274
0.750	-0.173169830	0.251151933
0.800	-0.136594833	0.212955586
0.900	-0.114652231	0.195829720
1.000	-0.084545091	0.210348575
1.200	-0.102869498	0.125258534
1.400	-0.083389916	0.132870922
1.600	-0.094786090	0.123220786
1.800	-0.102752396	0.000000000
2.000	-0.103422742	0.000000000
2.500	-0.068244045	0.000000000
3.000	-0.057480215	0.085136059
3.500	-0.070146879	0.129473332
4.000	-0.091093435	0.134808200
4.500	-0.102064769	0.158631712
5.000	-0.097178697	0.167041461
6.000	-0.072362480	0.162922973
7.000	-0.047777252	0.165452428
8.000	 0.000607773	0.166338780
""")

cfact = 1.732051
c3_slow = {}
c3_fast = {}

for imt in c3.non_sa_coeffs:
    imts = str(imt)
    c3_fast[imts] = c3[imt]["c3"] - cfact * c3[imt]["tau_c3"]
for imt in c3.sa_coeffs:
    imts = str(imt)
    c3_fast[imts] = c3[imt]["c3"] - cfact * c3[imt]["tau_c3"]

dl2l_high = {}
for imt in c3.non_sa_coeffs:
    imts = str(imt)
    dl2l_high[imts] = 1.0
for imt in c3.sa_coeffs:
    imts = str(imt)
    dl2l_high[imts] = 1.0


class MixcoEtAl2023InstantiationTestCase(unittest.TestCase):
    """
    Check the specification of dl2l and c3 as period-dependent vectors (inputted
    as dicts) is correctly read in at instantiation level.
    """

    def test_instantiation_dl2l(self):
        dl2l = {"PGA": 1.10, "SA(0.2)": 0.75, "SA(1.0)": -1.25}
        gsim = MixcoEtAl2023(dl2l=dl2l)
        self.assertIsInstance(gsim.dl2l, CoeffsTable)
        for imt, val in zip([PGA(), SA(0.2), SA(1.0)], [1.10, 0.75, -1.25]):
            self.assertAlmostEqual(gsim.dl2l[imt]["dl2l"], val)

    def test_instantiation_c3(self):
        c3 = {"PGA": 0.15, "SA(0.2)": 0.25, "SA(1.0)": 0.35}
        gsim = MixcoEtAl2023(c3=c3)
        self.assertIsInstance(gsim.c3, CoeffsTable)
        for imt, val in zip([PGA(), SA(0.2), SA(1.0)], [0.15, 0.25, 0.35]):
            self.assertAlmostEqual(gsim.c3[imt]["c3"], val)

    def test_instantiation_dl2l_non_dict(self):
        with self.assertRaises(IOError) as ioe:
            MixcoEtAl2023(dl2l=1.0)
        self.assertEqual(
            str(ioe.exception),
            "For Mixco et al. (2023) GMM, source-region scaling parameter "
            "(dl2l) must be input in the form of a dictionary, if specified")

    def test_instantiation_c3_non_dict(self):
        with self.assertRaises(IOError) as ioe:
            MixcoEtAl2023(c3=1.0)
        self.assertEqual(
            str(ioe.exception),
            "For Mixco et al. (2023) GMM, residual attenuation scaling (c3) "
            "must be input in the form of a dictionary, if specified")

# TODO add csvs and modify accordingly when automatic regionalisation version is added
"""
class MixcoEtAl2023regionalcoefficientsTestCase(unittest.TestCase):
    # test to check the selection of region and site specific coefficients
    # the test sites and their corresponding delta_l2l and delta_c3 values
    # were selected manually. 
    def test_get_distance_coefficients3(self):
        delta_c3_epsilon = 0
        imt = 'PGA'
        f = MixcoEtAl2023regional()
        self.att = f.att
        C = MixcoEtAl2023regional.COEFFS[PGA()]
        ## manually selected sites
        data = [[-4.13, 38.55], [7.74, 46.23], [10.579, 62.477], 
                [12.34, 45.03], [15.02, 39.80]] 
        sctx = pd.DataFrame(data, columns=['lon', 'lat'])
        ## values retireved manually from the author provided csv files
        expected_val = np.array([-0.609876182476899, -0.589902644476899, 
            -0.609876182476899, -0.530099285476899, -1.065428170476899])
        target = get_distance_coefficients_2(self.att, delta_c3_epsilon, C, imt, sctx)
        np.testing.assert_array_equal(target, expected_val)

    def test_get_dl2l_coefficients(self):
        delta_l2l_epsilon = 0
        imt = 'PGA'
        f = MixcoEtAl2023regional()
        self.tec = f.tec
        ## manually selected sites
        hypo = [[-4.13, 38.55], [7.74, 46.23], [10.579, 62.477], 
                [12.34, 45.03], [15.02, 39.80]]
        ctx = pd.DataFrame(hypo, columns=['hypo_lon', 'hypo_lat'])
        ## values retireved manually from the author provided csv files
        expected_val = np.array([0., -0.1490727,  0., -0.28239376, -0.2107627 ])
        dl2l = get_dl2l(self.tec, ctx, imt, delta_l2l_epsilon)            
        np.testing.assert_array_equal(dl2l, expected_val)
    

class MixcoEtAl2023regionalTestCase(BaseGSIMTestCase):
    ##Testing the regional version of the GMPE
    GSIM_CLASS = MixcoEtAl2023regional
    ## for a list of pre defined scenarios, the GMPE predictions
    ## were calculated in a notebook using the 
    ## `MixcoEtAl2023regional.get_mean_and_stddevs(ctxs, ctxs, ctxs, i, [StdDev.TOTAL])`
    def test_all(self):
        self.check("mixco23/MIXCO_2023_REGIONAL_MEAN.csv",
                max_discrep_percentage=MAX_DISCREP)
        self.check("mixco23/MIXCO_2023_REGIONAL_STDDEV_INTRA_EVENT.csv",
                "mixco23/MIXCO_2023_REGIONAL_STDDEV_INTER_EVENT.csv",
                "mixco23/MIXCO_2023_REGIONAL_STDDEV_TOTAL.csv",
                max_discrep_percentage=MAX_DISCREP)
"""

class MixcoEtAl2023TestCase(BaseGSIMTestCase):
    # Testing the unadjusted version of the original GMPE
    GSIM_CLASS = MixcoEtAl2023

    def test_all(self):
        #self.check("mixco23/MIXCO_2023_CENTRAL_MEAN.csv",
         #          max_discrep_percentage=MAX_DISCREP)
        self.check("mixco23/MIXCO_2023_STDDEV_INTRA_EVENT.csv",
                   "mixco23/MIXCO_2023_STDDEV_INTER_EVENT.csv",
                   "mixco23/MIXCO_2023_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)
        
     
class MixcoEtAl2023SiteTestCase(BaseGSIMTestCase):
    # Testing the version of Mixco et al. (2023) with Vs30-based site
    # amplification
    GSIM_CLASS = MixcoEtAl2023Site

    def test_all(self):
        self.check("mixco23/MIXCO_2023_VS30_MEAN.csv",
                   "mixco23/MIXCO_2023_VS30_STDDEV_INTRA_EVENT.csv",
                   "mixco23/MIXCO_2023_VS30_STDDEV_INTER_EVENT.csv",
                   "mixco23/MIXCO_2023_VS30_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class MixcoEtAl2023SlopeTestCase(BaseGSIMTestCase):
    # Testing the version of Mixco et al. (2023) with slope-based site
    # amplification
    GSIM_CLASS = MixcoEtAl2023Slope

    def test_all(self):
        self.check("mixco23/MIXCO_2023_SLOPE_MEAN.csv",
                   "mixco23/MIXCO_2023_SLOPE_STDDEV_INTRA_EVENT.csv",
                   "mixco23/MIXCO_2023_SLOPE_STDDEV_INTER_EVENT.csv",
                   "mixco23/MIXCO_2023_SLOPE_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)