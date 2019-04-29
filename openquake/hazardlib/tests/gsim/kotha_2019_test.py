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
from openquake.hazardlib.gsim.kotha_2019 import KothaEtAl2019SERA
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

MAX_DISCREP = 0.01

# Build the c3 input tables
tau_c3 = CoeffsTable(sa_damping=5, table="""
  imt                    c3             tau_c3
  pgv    -0.003717368903319  0.001989175108629
  pga    -0.006384808664692  0.003322073844615
0.010    -0.006458744312803  0.003249099924187
0.025    -0.005879118382059  0.003276969789544
0.040    -0.005120561634558  0.003112094247622
0.050    -0.005264500214593  0.003353817406823
0.070    -0.005657375107420  0.003756011346075
0.100    -0.006883472019433  0.004231945903474
0.150    -0.008379507529490  0.004285093038848
0.200    -0.008258443814965  0.004065520686124
0.250    -0.008168225448742  0.003694223510441
0.300    -0.007633705781879  0.003523170130238
0.350    -0.006957073673618  0.003380818237915
0.400    -0.006621400220309  0.003224354754275
0.450    -0.006096405733691  0.003154801713776
0.500    -0.005479207002881  0.003026941234605
0.600    -0.004644786062988  0.002686696245752
0.700    -0.004025744863412  0.002564264366739
0.750    -0.004061356198934  0.002396351691290
0.800    -0.003879315832285  0.002262050918392
0.900    -0.003666723557583  0.002162505133793
1.000    -0.003428313609870  0.001961940063713
1.200    -0.002911204978252  0.001827548291076
1.400    -0.002529697033308  0.001567754308089
1.600    -0.002047277539427  0.001586628710920
1.800    -0.001554451068759  0.001390149466717
2.000    -0.001580015449440  0.001354445228794
2.500    -0.001631228333605  0.001201195688135
3.000    -0.001922721370983  0.001266687383427
3.500    -0.002126518816230  0.001270039982803
4.000    -0.002160985939694  0.001160548266474
4.500    -0.001860522670072  0.000000000000000
5.000    -0.001550196672696  0.000000000000000
6.000    -0.001439766119884  0.000000000000000
7.000    -0.000867891160389  0.000000000000000
8.000    -0.000600200472803  0.000892670164182
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
