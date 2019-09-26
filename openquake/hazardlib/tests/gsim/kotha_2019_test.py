# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.kotha_2019 import (KothaEtAl2019SERA,
                                                 KothaEtAl2019Site,
                                                 KothaEtAl2019Slope,
                                                 KothaEtAl2019SERASlopeGeology)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

MAX_DISCREP = 0.01

# Build the c3 input tables
tau_c3 = CoeffsTable(sa_damping=5, table="""
imt                      c3              tau_c3
pgv      -0.358475654018642   0.158122937530244
pga      -0.678379247430291   0.263916141885138
0.0100   -0.677333232895566   0.263885400397128
0.0250   -0.638666791582353   0.262164920363914
0.0400   -0.597052092823935   0.251662690566386
0.0500   -0.621868044857147   0.265892288510560
0.0700   -0.724343238043036   0.291387067989580
0.1000   -0.829503523244518   0.332348696555227
0.1500   -0.889955230608062   0.338152565231841
0.2000   -0.834473063837879   0.308867853425155
0.2500   -0.776587060423500   0.277393830052251
0.3000   -0.718787095472858   0.275157669080336
0.3500   -0.673786484345681   0.259619616389265
0.4000   -0.642239681195656   0.246279727018558
0.4500   -0.603205730169031   0.247585522515150
0.5000   -0.563257403363693   0.239584431802383
0.6000   -0.497303864164013   0.219211803845992
0.7000   -0.440618892293181   0.214461662068525
0.7500   -0.419724044373000   0.207438203391352
0.8000   -0.403124991422463   0.189995354821562
0.9000   -0.374788234612032   0.167063633965528
1.0000   -0.353209184896043   0.152524622009451
1.2000   -0.307609138051120   0.136322298762975
1.4000   -0.263665247407548   0.126451619959459
1.6000   -0.218847134352892   0.131025001289405
1.8000   -0.185702153948541   0.137842414980722
2.0000   -0.159248285466522   0.140849131837099
2.5000   -0.136859516271201   0.166320529763324
3.0000   -0.169153068756301   0.162858122205747
3.5000   -0.166147766003538   0.172286178709976
4.0000   -0.162312356740869   0.174567193920684
4.5000   -0.172605613836776   0.145926141801792
5.0000   -0.140697393026636   0.136942909437525
6.0000   -0.133212839440133   0.141314902795929
7.0000   -0.088623284188977   0.145375015287528
8.0000   -0.064115203294262   0.151582553207261
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


class KothaEtAl2019SERATestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019SERA

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_CENTRAL_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha19/KOTHA_2019_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha19/KOTHA_2019_STDDEV_INTER_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha19/KOTHA_2019_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2019SERASlowAttenTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019SERA

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_LOW_ATTEN_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   c3=c3_slow)


class KothaEtAl2019SERAFastAttenTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019SERA

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_FAST_ATTEN_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   c3=c3_fast)


class KothaEtAl2019SERAHighSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019SERA

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_HIGH_SIGMA_MU_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_mu_epsilon=1.0)


class KothaEtAl2019SERALowSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019SERA

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_LOW_SIGMA_MU_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_mu_epsilon=-1.0)


class KothaEtAl2019SiteTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019Site

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_VS30_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha19/KOTHA_2019_VS30_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha19/KOTHA_2019_VS30_STDDEV_INTER_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha19/KOTHA_2019_VS30_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2019SlopeTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019Slope

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_SLOPE_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha19/KOTHA_2019_SLOPE_STDDEV_INTRA_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha19/KOTHA_2019_SLOPE_STDDEV_INTER_EVENT.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha19/KOTHA_2019_SLOPE_STDDEV_TOTAL.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2019SlopeGeologyTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KothaEtAl2019SERASlopeGeology

    def test_mean(self):
        self.check("kotha19/KOTHA_2019_SLOPE_GEOLOGY_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha19/KOTHA_2019_SLOPE_GEOLOGY_INTRA_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("kotha19/KOTHA_2019_SLOPE_GEOLOGY_INTER_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha19/KOTHA_2019_SLOPE_GEOLOGY_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)
