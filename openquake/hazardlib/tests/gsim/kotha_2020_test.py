# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.kotha_2020 import (KothaEtAl2020SERA,
                                                 KothaEtAl2020Site,
                                                 KothaEtAl2020Slope,
                                                 KothaEtAl2020SERASlopeGeology)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

MAX_DISCREP = 0.01

# Build the c3 input tables
tau_c3 = CoeffsTable(sa_damping=5, table="""
imt                  c3           tau_c3
pgv     -0.303453527552   0.179928856360
pga     -0.608840589420   0.254501921365
0.010   -0.607836921386   0.254473840849
0.025   -0.572198448811   0.253266193047
0.040   -0.534112656153   0.245054022905
0.050   -0.554344743057   0.260199667680
0.070   -0.640526595472   0.286956317682
0.100   -0.743396259134   0.322309553915
0.150   -0.815043098860   0.322007237429
0.200   -0.772880020737   0.301572220795
0.250   -0.721417443819   0.274901019805
0.300   -0.659797998230   0.261180806047
0.350   -0.617942668472   0.254737453226
0.400   -0.590763475754   0.244367107710
0.450   -0.554433746532   0.246565073080
0.500   -0.518700657967   0.239580664585
0.600   -0.453602302389   0.217919431330
0.700   -0.397369836147   0.216884654674
0.750   -0.376202497137   0.211017683167
0.800   -0.362739820962   0.193658451006
0.900   -0.333308869969   0.179232974308
1.000   -0.316824095141   0.174173178526
1.200   -0.274783316235   0.163249277591
1.400   -0.234349930531   0.153501938280
1.600   -0.197546621568   0.150851270249
1.800   -0.166778722563   0.157733949899
2.000   -0.140417710429   0.156493287404
2.500   -0.120374488710   0.178207969780
3.000   -0.148534265023   0.175955415496
3.500   -0.142560085634   0.192759182459
4.000   -0.141789103905   0.192905670114
4.500   -0.155260019763   0.154450733985
5.000   -0.125368353163   0.139412564761
6.000   -0.112670397633   0.144727555167
7.000   -0.069644614376   0.148649539627
8.000   -0.050512729714   0.152958209816
""")

cfact = 1.732051
c3_slow = {}
c3_fast = {}

for imt in tau_c3.non_sa_coeffs:
    imts = str(imt)
    c3_slow[imts] = tau_c3[imt]["c3"] + cfact * tau_c3[imt]["tau_c3"]
    c3_fast[imts] = tau_c3[imt]["c3"] - cfact * tau_c3[imt]["tau_c3"]
for imt in tau_c3.sa_coeffs:
    imts = str(imt)
    c3_slow[imts] = tau_c3[imt]["c3"] + cfact * tau_c3[imt]["tau_c3"]
    c3_fast[imts] = tau_c3[imt]["c3"] - cfact * tau_c3[imt]["tau_c3"]


class KothaEtAl2020SERATestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERA

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_CENTRAL_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha20/KOTHA_2020_STDDEV_INTER_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020SERANonErgodicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERA

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_STDDEV_NONERGODIC_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_STDDEV_NONERGODIC_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)


class KothaEtAl2020SERASlowAttenTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERA

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_LOW_ATTEN_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   c3=c3_slow)


class KothaEtAl2020SERAFastAttenTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERA

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_FAST_ATTEN_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   c3=c3_fast)


class KothaEtAl2020SERAHighSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERA

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_HIGH_SIGMA_MU_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_mu_epsilon=1.0)


class KothaEtAl2020SERALowSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERA

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_LOW_SIGMA_MU_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_mu_epsilon=-1.0)


class KothaEtAl2020SiteTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020Site

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_VS30_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_VS30_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha20/KOTHA_2020_VS30_STDDEV_INTER_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_VS30_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020SiteNonErgodicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020Site

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_VS30_NONERGODIC_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_VS30_NONERGODIC_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)


class KothaEtAl2020SlopeTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020Slope

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_SLOPE_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_SLOPE_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha20/KOTHA_2020_SLOPE_STDDEV_INTER_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_SLOPE_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020SlopeNonErgodicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020Slope

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_SLOPE_NONERGODIC_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_SLOPE_NONERGODIC_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)


class KothaEtAl2020SlopeGeologyTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERASlopeGeology

    def test_mean(self):
        self.check("kotha20/KOTHA_2020_SLOPE_GEOLOGY_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_SLOPE_GEOLOGY_INTRA_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha20/KOTHA_2020_SLOPE_GEOLOGY_INTER_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_SLOPE_GEOLOGY_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2020SlopeGeologyNonergodicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2020SERASlopeGeology

    def test_std_intra(self):
        self.check("kotha20/KOTHA_2020_SLOPE_GEOLOGY_NONERGODIC_INTRA_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)

    def test_std_total(self):
        self.check("kotha20/KOTHA_2020_SLOPE_GEOLOGY_NONERGODIC_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   ergodic=False)
