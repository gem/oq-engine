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
As the GMPE is constructed directly from an OpenQuake implementation according
to the author's coefficient set and verified against the expected values from
the author's equivalent R implementation
"""
import unittest
import pandas as pd
import numpy as np
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.kotha_2020 import (
    KothaEtAl2020, KothaEtAl2020ESHM20, KothaEtAl2020Site,
    KothaEtAl2020Slope, KothaEtAl2020ESHM20SlopeGeology, KothaEtAl2020regional)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.kotha_2020 import get_distance_coefficients_3, get_dl2l

MAX_DISCREP = 0.01

# Build the c3 and dl2l input tables
c3 = CoeffsTable(sa_damping=5, table="""\
imt                      c3              tau_c3
pgv      -0.304426142175370   0.178233997535235
pga      -0.609876182476899   0.253818777234181
0.010    -0.608869451197394   0.253797652143759
0.025    -0.573207556417252   0.252734624432000
0.040    -0.535139204130152   0.244894143623498
0.050    -0.555191107011420   0.260330694464557
0.070    -0.641089475725666   0.286976037026550
0.100    -0.744270750619733   0.321927482439715
0.150    -0.815688997995934   0.322145126407981
0.200    -0.773372802995208   0.301795870071949
0.250    -0.722012122448262   0.274998157533509
0.300    -0.660466290850886   0.260774631679394
0.350    -0.618593385936676   0.254261888951322
0.400    -0.591574546068960   0.243643375298288
0.450    -0.555234498707119   0.245883260391068
0.500    -0.519413341065942   0.238559829231160
0.600    -0.454043559543982   0.216855298090451
0.700    -0.397781532595396   0.215716276719833
0.750    -0.376630503031279   0.209593410875067
0.800    -0.363246464853852   0.192106714053294
0.900    -0.333908265367165   0.177456610405390
1.000    -0.317465939881623   0.171997778367260
1.200    -0.275616235541070   0.160445653296358
1.400    -0.234977212668109   0.150949141990859
1.600    -0.198050139347725   0.148738498099927
1.800    -0.167123738873435   0.156141593013035
2.000    -0.140731664063789   0.155054491423268
2.500    -0.120745041347963   0.176744551716694
3.000    -0.149050671035371   0.174876785480317
3.500    -0.142873831246493   0.193619214137258
4.000    -0.142053716741244   0.193571789393738
4.500    -0.156076448842833   0.152553585766189
5.000    -0.126052481240424   0.137919529808920
6.000    -0.113766839623945   0.141669390606605
7.000    -0.070585399916418   0.146488759166368
8.000    -0.051296439369391   0.150981191615944
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


class KothaEtAl2020InstantiationTestCase(unittest.TestCase):
    # Testing instantiation of the GMPE

    def test_instantiation_dl2l(self):
        dl2l = {"PGA": 1.0, "SA(0.2)": 0.5, "SA(1.0)": -1.0}
        gsim = KothaEtAl2020(dl2l=dl2l)
        self.assertIsInstance(gsim.dl2l, CoeffsTable)
        for imt, val in zip([PGA(), SA(0.2), SA(1.0)], [1.0, 0.5, -1.0]):
            self.assertAlmostEqual(gsim.dl2l[imt]["dl2l"], val)

    def test_instantiation_c3(self):
        c3 = {"PGA": 0.1, "SA(0.2)": 0.2, "SA(1.0)": 0.3}
        gsim = KothaEtAl2020(c3=c3)
        self.assertIsInstance(gsim.c3, CoeffsTable)
        for imt, val in zip([PGA(), SA(0.2), SA(1.0)], [0.1, 0.2, 0.3]):
            self.assertAlmostEqual(gsim.c3[imt]["c3"], val)

    def test_instantiation_dl2l_non_dict(self):
        with self.assertRaises(IOError) as ioe:
            KothaEtAl2020(dl2l=1.0)
        self.assertEqual(
            str(ioe.exception),
            "For Kotha et al. (2020) GMM, source-region scaling parameter "
            "(dl2l) must be input in the form of a dictionary, if specified")

    def test_instantiation_c3_non_dict(self):
        with self.assertRaises(IOError) as ioe:
            KothaEtAl2020(c3=1.0)
        self.assertEqual(
            str(ioe.exception),
            "For Kotha et al. (2020) GMM, residual attenuation scaling (c3) "
            "must be input in the form of a dictionary, if specified")

class KothaEtAl2020regionalcoefficientsTestCase(unittest.TestCase):
    # test to check the selection of region and site specific coefficients
    # the test sites and their corresponding delta_l2l and delta_c3 values
    # were selected manually. 
    def test_get_distance_coefficients3(self):
        delta_c3_epsilon = 0
        imt = 'PGA'
        f = KothaEtAl2020regional()
        self.att = f.att
        C = KothaEtAl2020regional.COEFFS[PGA()]
        ## manually selected sites
        data = [[-4.13, 38.55], [7.74, 46.23], [10.579, 62.477], 
                [12.34, 45.03], [15.02, 39.80]] 
        sctx = pd.DataFrame(data, columns=['lon', 'lat'])
        ## values retireved manually from the author provided csv files
        expected_val = np.array([-0.609876182476899, -0.589902644476899, 
            -0.609876182476899, -0.530099285476899, -1.065428170476899])
        target = get_distance_coefficients_3(self.att, delta_c3_epsilon, C, imt, sctx)
        np.testing.assert_array_equal(target, expected_val)

    def test_get_dl2l_coefficients(self):
        delta_l2l_epsilon = 0
        imt = 'PGA'
        f = KothaEtAl2020regional()
        self.tec = f.tec
        ## manually selected sites
        hypo = [[-4.13, 38.55], [7.74, 46.23], [10.579, 62.477], 
                [12.34, 45.03], [15.02, 39.80]]
        ctx = pd.DataFrame(hypo, columns=['hypo_lon', 'hypo_lat'])
        ## values retireved manually from the author provided csv files
        expected_val = np.array([0., -0.1490727,  0., -0.28239376, -0.2107627 ])
        dl2l = get_dl2l(self.tec, ctx, imt, delta_l2l_epsilon)            
        np.testing.assert_array_equal(dl2l, expected_val)
    

class KothaEtAl2020regionalTestCase(BaseGSIMTestCase):
    ##Testing the regional version of the GMPE
    GSIM_CLASS = KothaEtAl2020regional
    ## for a list of pre defined scenarios, the GMPE predictions
    ## were calculated in a notebook using the 
    ## `KothaEtAl2020regional.get_mean_and_stddevs(ctxs, ctxs, ctxs, i, [StdDev.TOTAL])`
    def test_all(self):
        self.check("kotha20/KOTHA_2020_REGIONAL_MEAN.csv",
                max_discrep_percentage=MAX_DISCREP)
        self.check("kotha20/KOTHA_2020_REGIONAL_STDDEV_INTRA_EVENT.csv",
                "kotha20/KOTHA_2020_REGIONAL_STDDEV_INTER_EVENT.csv",
                "kotha20/KOTHA_2020_REGIONAL_STDDEV_TOTAL.csv",
                max_discrep_percentage=MAX_DISCREP)

class KothaEtAl2020TestCase(BaseGSIMTestCase):
    # Testing the unadjusted version of the original GMPE
    GSIM_CLASS = KothaEtAl2020

    def test_all(self):
        self.check("kotha20/KOTHA_2020_CENTRAL_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)
        self.check("kotha20/KOTHA_2020_STDDEV_INTRA_EVENT.csv",
                   "kotha20/KOTHA_2020_STDDEV_INTER_EVENT.csv",
                   "kotha20/KOTHA_2020_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020SiteTestCase(BaseGSIMTestCase):
    # Testing the version of Kotha et al. (2020) with Vs30-based site
    # amplification
    GSIM_CLASS = KothaEtAl2020Site

    def test_all(self):
        self.check("kotha20/KOTHA_2020_VS30_MEAN.csv",
                   "kotha20/KOTHA_2020_VS30_STDDEV_INTRA_EVENT.csv",
                   "kotha20/KOTHA_2020_VS30_STDDEV_INTER_EVENT.csv",
                   "kotha20/KOTHA_2020_VS30_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020SlopeTestCase(BaseGSIMTestCase):
    # Testing the version of Kotha et al. (2020) with slope-based site
    # amplification
    GSIM_CLASS = KothaEtAl2020Slope

    def test_all(self):
        self.check("kotha20/KOTHA_2020_SLOPE_MEAN.csv",
                   "kotha20/KOTHA_2020_SLOPE_STDDEV_INTRA_EVENT.csv",
                   "kotha20/KOTHA_2020_SLOPE_STDDEV_INTER_EVENT.csv",
                   "kotha20/KOTHA_2020_SLOPE_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020ESHM20TestCase(BaseGSIMTestCase):
    # Testing the unadjusted version of the ESHM20 calibrated GMPE (ergodic)
    GSIM_CLASS = KothaEtAl2020ESHM20

    def test_all(self):
        self.check("kotha20/KOTHA_2020_ESHM_CENTRAL_MEAN.csv",
                   "kotha20/KOTHA_2020_ESHM_STDDEV_INTRA_EVENT.csv",
                   "kotha20/KOTHA_2020_ESHM_STDDEV_INTER_EVENT.csv",
                   "kotha20/KOTHA_2020_ESHM_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020ESHM20NonErgodicTestCase(BaseGSIMTestCase):
    # Testing the non-ergodic case
    GSIM_CLASS = KothaEtAl2020ESHM20

    def test_stds(self):
        self.check(
            "kotha20/KOTHA_2020_ESHM_STDDEV_NONERGODIC_INTRA_EVENT.csv",
            "kotha20/KOTHA_2020_ESHM_STDDEV_NONERGODIC_TOTAL.csv",
            max_discrep_percentage=MAX_DISCREP,
            ergodic=False)


class KothaEtAl2020ESHM20FastAttenTestCase(BaseGSIMTestCase):
    # Testing the case of fast attenuation defined by c3_epsilon
    GSIM_CLASS = KothaEtAl2020ESHM20

    def test_all(self):
        self.check("kotha20/KOTHA_2020_ESHM_FAST_ATTEN_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP, c3_epsilon=-1.0)


class KothaEtAl2020ESHM20FastC3TestCase(BaseGSIMTestCase):
    # Testing the case of fast attenuation defined by manually input c3
    GSIM_CLASS = KothaEtAl2020ESHM20

    def test_all(self):
        self.check("kotha20/KOTHA_2020_ESHM_c3_FAST_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP, c3=c3_fast)


class KothaEtAl2020ESHM20HighSigmaMuTestCase(BaseGSIMTestCase):
    # Testing the case of high source region scaling, defined by positive
    # sigma mu
    GSIM_CLASS = KothaEtAl2020ESHM20

    def test_all(self):
        self.check("kotha20/KOTHA_2020_ESHM_HIGH_SIGMA_MU_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_mu_epsilon=1.0)


class KothaEtAl2020ESHM20HighDL2LTestCase(BaseGSIMTestCase):
    # Testing the case of high source region scaling, defined by set dL2L
    GSIM_CLASS = KothaEtAl2020ESHM20

    def test_all(self):
        self.check("kotha20/KOTHA_2020_ESHM_DL2L_HIGH_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP, dl2l=dl2l_high)


class KothaEtAl2020SlopeGeologyTestCase(BaseGSIMTestCase):
    # Testing the case in which site amplification is based on slope and
    # geology
    GSIM_CLASS = KothaEtAl2020ESHM20SlopeGeology

    def test_all(self):
        self.check(
            "kotha20/KOTHA_2020_SLOPE_GEOLOGY_MEAN.csv",
            "kotha20/KOTHA_2020_SLOPE_GEOLOGY_INTRA_EVENT_STDDEV.csv",
            "kotha20/KOTHA_2020_SLOPE_GEOLOGY_INTER_EVENT_STDDEV.csv",
            "kotha20/KOTHA_2020_SLOPE_GEOLOGY_TOTAL_STDDEV.csv",
            max_discrep_percentage=MAX_DISCREP)
