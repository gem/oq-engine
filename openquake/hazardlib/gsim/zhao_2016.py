# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module exports :class:`ZhaoEtAl2016Asc`,
               :class:`ZhaoEtAl2016AscSiteSigma`,
               :class:`ZhaoEtAl2016UpperMantle`,
               :class:`ZhaoEtAl2016UpperMantleSiteSigma`,
               :class:`ZhaoEtAl2016SInter`,
               :class:`ZhaoEtAl2016SInterSiteSigma`,
               :class:`ZhaoEtAl2016SSlab`,
               :class:`ZhaoEtAl2016SSlabSiteSigma`,
               :class:`ZhaoEtAl2016SSlabPErg`
"""
import copy
import numpy as np
import pandas as pd

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.geo.packager import fiona
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo import Polygon
from openquake.hazardlib.gsim.zhao_2016_volc_perg import volc_perg


CONSTANTS = {"m_c": 7.1,
             "xcro": 2.0,
             "xinto": 10.0,  # Used in subduction Interface class
             "alpha": 2.0,
             "beta": 0.6,
             "Imin": 1.0,
             "Imax": 12.0,
             "m_sc": 6.3}  # Used in Subduction Slab class

# Impedence ratio factors for each site class
IMF = {1: (1. + 0.8 * 2.73) / 3.5,  # IMF 0.91
       2: 3.07 / 3.0,
       3: (1. + 0.9 * 1.76) / 2.5,
       4: (1. + 0.6 * 2.02) / 3.0}

get_magnitude_scaling_term = CallableDict()

# Coefficients table taken from spreadsheet supplied by the author
COEFFS_SLAB = CoeffsTable(sa_damping=5, table="""\
imt                alpha   beta      cSL     cSL2      dSL              bSLH       gSL      gLL      eSLV       eSL       eSLH       gamma         S2         S3         S4              lnSC1AM    sigma     tau  sigma_T  sc1_sigma_S  sc1_tau_S  sc1_sigma_ST  sc2_sigma_S  sc2_tau_S  sc2_sigma_ST  sc3_sigma_S  sc3_tau_S  sc3_sigma_ST  sc4_sigma_S  sc4_tau_S  sc4_sigma_ST
pga    -5.30118903954448  1.151  1.44758  0.37625  0.42646  0.01825668401347  -1.98471  1.12071  -0.01499  -0.00340  -0.000501   -9.879560   0.232000   0.143711   0.147037   0.3230000000000000   0.5870  0.4570   0.7440       0.3981     0.5107        0.6475       0.4174     0.4494        0.6133       0.4091     0.4306        0.5940       0.4152     0.4217        0.5918
0.005  -5.30118903954448  1.151  1.44758  0.37625  0.42646  0.01825668401347  -1.98471  1.12071  -0.01499  -0.00340  -0.000501   -9.879560   0.232000   0.143711   0.147037   0.3230000000000000   0.5870  0.4570   0.7440       0.3981     0.5107        0.6475       0.4174     0.4494        0.6133       0.4091     0.4306        0.5940       0.4152     0.4217        0.5918
0.010  -5.28843513142218  1.151  1.45400  0.38099  0.42075  0.01825668401347  -1.96360  1.03278  -0.01503  -0.00331  -0.000501   -9.512690   0.228860   0.139780   0.132840   0.2050000000000000   0.5870  0.4590   0.7460       0.3968     0.5166        0.6514       0.4173     0.4499        0.6136       0.4086     0.4314        0.5941       0.4149     0.4183        0.5892
0.020  -5.27568122329988  1.151  1.46625  0.39101  0.40055  0.01825668401347  -1.91839  0.94715  -0.01517  -0.00345  -0.000501   -9.266260   0.218250   0.126000   0.144310   0.0830000000000000   0.5870  0.4650   0.7490       0.3951     0.5180        0.6515       0.4172     0.4488        0.6128       0.4082     0.4313        0.5938       0.4158     0.4245        0.5942
0.030  -5.26822066531069  1.151  1.49246  0.41976  0.36433  0.01825668401347  -1.89271  0.93420  -0.01567  -0.00391  -0.000501   -9.331500   0.187370   0.061640   0.066000   0.0410000000000000   0.5880  0.4800   0.7590       0.3894     0.5369        0.6633       0.4179     0.4492        0.6135       0.4088     0.4300        0.5933       0.4166     0.4224        0.5933
0.040  -5.26292731517758  1.151  1.50129  0.45746  0.32072  0.01825668401347  -1.87260  0.97168  -0.01616  -0.00454  -0.000501   -9.507980   0.123320  -0.017050  -0.017140   0.0340000000000000   0.6000  0.5200   0.7940       0.3873     0.5716        0.6905       0.4201     0.4559        0.6200       0.4125     0.4281        0.5945       0.4201     0.4308        0.6017
0.050  -5.25882147383339  1.151  1.51051  0.48601  0.30000  0.01825668401347  -1.85351  1.01492  -0.01676  -0.00510  -0.000501   -9.728580   0.072070  -0.063310  -0.073120   0.0460000000000000   0.6070  0.5550   0.8230       0.3874     0.5857        0.7022       0.4219     0.4794        0.6386       0.4089     0.4286        0.5924       0.4217     0.4387        0.6085
0.060  -5.25546675718839  1.151  1.51380  0.50311  0.31147  0.01825668401347  -1.83395  1.06854  -0.01722  -0.00552  -0.000501   -9.966280   0.027010  -0.101030  -0.119550   0.0690000000000000   0.6230  0.5840   0.8540       0.3970     0.6131        0.7304       0.4160     0.5074        0.6561       0.4012     0.4485        0.6018       0.4227     0.4450        0.6138
0.070  -5.25263038467956  1.151  1.51111  0.50704  0.32673  0.01825668401347  -1.81345  1.13401  -0.01752  -0.00588  -0.000487  -10.225830  -0.006210  -0.146840  -0.160060   0.0980000000000000   0.6380  0.5980   0.8750       0.4027     0.6326        0.7499       0.4121     0.5317        0.6727       0.3942     0.4556        0.6025       0.4203     0.4732        0.6329
0.080  -5.25017340705527  1.151  1.50406  0.50004  0.34289  0.01825668401347  -1.79189  1.20364  -0.01768  -0.00615  -0.000479  -10.551110   0.015650  -0.144790  -0.124340   0.1320000000000000   0.6510  0.5980   0.8840       0.4130     0.6434        0.7646       0.4124     0.5554        0.6918       0.3887     0.4554        0.5987       0.4230     0.4905        0.6477
0.090  -5.24800619919920  1.151  1.49423  0.48071  0.35921  0.01825668401347  -1.76931  1.25808  -0.01772  -0.00635  -0.000476  -10.807210   0.050890  -0.126660  -0.072930   0.1690000000000000   0.6630  0.5850   0.8840       0.4221     0.6307        0.7589       0.4122     0.5677        0.7015       0.3905     0.4752        0.6151       0.4269     0.5177        0.6710
0.100  -5.24606756571109  1.151  1.48300  0.45759  0.37000  0.01825668401347  -1.74581  1.30112  -0.01768  -0.00652  -0.000478  -11.021900   0.095600  -0.093190  -0.014580   0.2080000000000000   0.6740  0.5670   0.8810       0.4286     0.6258        0.7585       0.4177     0.5662        0.7036       0.3936     0.5067        0.6416       0.4263     0.5593        0.7033
0.120  -5.24271284906608  1.151  1.45559  0.41355  0.40606  0.01825668401347  -1.73746  1.39137  -0.01742  -0.00660  -0.000489  -11.365300   0.200370  -0.008780   0.082520   0.2880000000000000   0.6900  0.5340   0.8720       0.4402     0.6135        0.7551       0.4285     0.5695        0.7127       0.4279     0.5479        0.6951       0.4445     0.5762        0.7277
0.140  -5.23987647655726  1.151  1.44277  0.37828  0.43450  0.01825668401347  -1.74463  1.47084  -0.01700  -0.00652  -0.000508  -11.730390   0.303720   0.089260   0.171510   0.3700000000000000   0.6920  0.5040   0.8560       0.4411     0.6126        0.7549       0.4347     0.5971        0.7386       0.4326     0.5072        0.6666       0.4424     0.5608        0.7143
0.150  -5.23860700772190  1.151  1.43314  0.36308  0.45000  0.01825668401347  -1.74972  1.50784  -0.01676  -0.00647  -0.000520  -11.880130   0.342840   0.136020   0.209320   0.4120000000000000   0.6960  0.4860   0.8500       0.4495     0.6023        0.7515       0.4399     0.5985        0.7428       0.4200     0.4896        0.6450       0.4401     0.5546        0.7080
0.160  -5.23741949893297  1.151  1.43253  0.34919  0.46055  0.01825668401347  -1.76259  1.54326  -0.01649  -0.00636  -0.000532  -12.056370   0.374000   0.177510   0.241170   0.4530000000000000   0.6970  0.4650   0.8380       0.4518     0.5987        0.7500       0.4443     0.5970        0.7442       0.4239     0.4939        0.6509       0.4369     0.5517        0.7037
0.180  -5.23525229107689  1.151  1.43710  0.32464  0.48439  0.01825668401347  -1.78989  1.60985  -0.01594  -0.00614  -0.000559  -12.420440   0.427000   0.253090   0.298960   0.5350000000000000   0.7040  0.4300   0.8250       0.4540     0.5990        0.7516       0.4474     0.6005        0.7489       0.4463     0.5003        0.6704       0.4361     0.5534        0.7046
0.200  -5.23331365758879  1.151  1.44781  0.30358  0.50900  0.01825668401347  -1.82110  1.67146  -0.01537  -0.00590  -0.000588  -12.785420   0.462970   0.320050   0.345910   0.6060000000000000   0.7130  0.4060   0.8210       0.4622     0.5897        0.7493       0.4499     0.5962        0.7469       0.4411     0.4907        0.6598       0.4322     0.5617        0.7088
0.250  -5.22920781624461  1.151  1.48260  0.26174  0.55500  0.01825668401347  -1.90412  1.80738  -0.01395  -0.00526  -0.000667  -13.635370   0.508560   0.453040   0.442310   0.6700000000000000   0.7110  0.3850   0.8080       0.4743     0.5545        0.7297       0.4702     0.6010        0.7631       0.4587     0.4500        0.6426       0.4319     0.5065        0.6657
0.300  -5.22585309959960  1.151  1.51881  0.23036  0.59300  0.01825668401347  -1.98439  1.92242  -0.01261  -0.00468  -0.000749  -14.380860   0.507760   0.548750   0.517820   0.7100000000000000   0.6830  0.3650   0.7750       0.4723     0.5320        0.7114       0.4749     0.5574        0.7322       0.4369     0.4989        0.6631       0.4323     0.4889        0.6526
0.350  -5.22301672709078  1.151  1.55291  0.20580  0.62500  0.01825668401347  -2.05756  2.02102  -0.01139  -0.00415  -0.000831  -15.035110   0.497100   0.617130   0.575960   0.7189367707551090   0.6650  0.3730   0.7620       0.4677     0.5050        0.6883       0.4780     0.5178        0.7047       0.4435     0.5315        0.6922       0.4318     0.4630        0.6331
0.400  -5.22055974946649  1.151  1.58443  0.18597  0.65200  0.01825668401347  -2.12282  2.10642  -0.01029  -0.00369  -0.000912  -15.615990   0.480650   0.666340   0.622390   0.7056101598849490   0.6570  0.3830   0.7610       0.4574     0.4792        0.6625       0.4836     0.4878        0.6868       0.4530     0.5458        0.7093       0.4155     0.4661        0.6244
0.450  -5.21839254161041  1.151  1.61360  0.16960  0.67500  0.01825668401347  -2.18047  2.18097  -0.00931  -0.00327  -0.000993  -16.138300   0.461590   0.701110   0.659760   0.6928932372909810   0.6470  0.3910   0.7560       0.4500     0.4608        0.6441       0.4772     0.4790        0.6761       0.4771     0.5294        0.7127       0.4079     0.4613        0.6158
0.500  -5.21645390812230  1.151  1.64075  0.15585  0.69500  0.01825668401347  -2.23118  2.24651  -0.00843  -0.00290  -0.001071  -16.613239   0.442240   0.725580   0.690660   0.6807534705053220   0.6400  0.4030   0.7560       0.4452     0.4506        0.6334       0.4696     0.4713        0.6653       0.4718     0.4947        0.6836       0.4087     0.4665        0.6202
0.600  -5.21309919147730  1.151  1.69020  0.13405  0.72900  0.01825668401347  -2.31475  2.35602  -0.00694  -0.00227  -0.001239  -17.452980   0.405370   0.752940   0.737960   0.6580415130288750   0.6330  0.4120   0.7550       0.4480     0.4355        0.6248       0.4597     0.4671        0.6553       0.4590     0.4701        0.6570       0.4065     0.4335        0.5943
0.700  -5.21026281896847  1.151  1.73450  0.11757  0.75600  0.01825668401347  -2.37885  2.44331  -0.00574  -0.00178  -0.001393  -18.180950   0.373420   0.762450   0.772260   0.6371531353146750   0.6330  0.4320   0.7660       0.4396     0.4299        0.6149       0.4595     0.4642        0.6532       0.4611     0.4727        0.6604       0.4031     0.4300        0.5894
0.800  -5.20780584134418  1.151  1.77474  0.10476  0.77800  0.01825668401347  -2.42769  2.51391  -0.00477  -0.00139  -0.001535  -18.824989   0.346230   0.761190   0.797360   0.6178103254041100   0.6360  0.4360   0.7710       0.4412     0.4269        0.6139       0.4596     0.4559        0.6474       0.4573     0.4565        0.6461       0.4067     0.4543        0.6097
0.900  -5.20563863348810  1.151  1.81162  0.09458  0.79600  0.01825668401347  -2.46450  2.57166  -0.00398  -0.00109  -0.001664  -19.403130   0.323640   0.753840   0.816160   0.5997867391697460   0.6360  0.4370   0.7720       0.4345     0.4314        0.6123       0.4559     0.4659        0.6519       0.4490     0.4391        0.6280       0.4082     0.4556        0.6117
1.000  -5.20370000000000  1.151  1.84561  0.08636  0.81200  0.01825668401347  -2.49170  2.61931  -0.00333  -0.00086  -0.001781  -19.927660   0.304790   0.742790   0.830090   0.5829000000000000   0.6370  0.4360   0.7720       0.4270     0.4400        0.6131       0.4479     0.4663        0.6466       0.4419     0.4415        0.6246       0.4080     0.4619        0.6163
1.250  -5.19959415865582  1.151  1.92015  0.07173  0.84100  0.01807627932941  -2.52758  2.70638  -0.00215  -0.00052  -0.001989  -21.058180   0.270260   0.708330   0.850360   0.5447531267038370   0.6350  0.4440   0.7750       0.4126     0.4401        0.6032       0.4422     0.4755        0.6493       0.4279     0.4321        0.6081       0.4123     0.4437        0.6057
1.500  -5.19623944201081  1.151  1.98274  0.06258  0.86100  0.01785908731221  -2.53359  2.76244  -0.00142  -0.00043  -0.002134  -21.996330   0.248310   0.672560   0.857320   0.5111822983011660   0.6450  0.4480   0.7850       0.4157     0.4485        0.6115       0.4477     0.4730        0.6513       0.4177     0.4605        0.6217       0.4178     0.4432        0.6090
2.000  -5.19094609187770  1.151  2.08214  0.05327  0.88400  0.01717728835933  -2.49565  2.82205  -0.00067  -0.00070  -0.002245  -23.488390   0.225290   0.610670   0.849910   0.4538170835899950   0.6330  0.4240   0.7620       0.4089     0.4409        0.6013       0.4371     0.4624        0.6362       0.4061     0.4720        0.6227       0.4133     0.4392        0.6031
2.500  -5.18684025053352  1.151  2.15841  0.05036  0.90000  0.01628389643418  -2.42623  2.84475  -0.00039  -0.00127  -0.002188  -24.647409   0.215400   0.564030   0.827570   0.4056165742693500   0.6080  0.4130   0.7350       0.3979     0.4247        0.5820       0.4293     0.4273        0.6057       0.3868     0.4841        0.6197       0.4139     0.4267        0.5945
3.000  -5.18348553388851  1.151  2.22046  0.04536  0.90000  0.01549254642056  -2.34726  2.84988  -0.00030  -0.00198  -0.002068  -25.597130   0.211540   0.526120   0.799110   0.3638313271186210   0.5820  0.4070   0.7110       0.3901     0.3963        0.5561       0.4227     0.4071        0.5869       0.3688     0.4470        0.5795       0.4117     0.4309        0.5959
3.500  -5.18064916137969  1.151  2.27406  0.04536  0.90000  0.01489171351523  -2.27002  2.84667  -0.00026  -0.00271  -0.001926  -26.409969   0.209756   0.497660   0.767820   0.3268167127622250   0.5620  0.3940   0.6870       0.3858     0.3856        0.5454       0.4104     0.4011        0.5738       0.3763     0.4339        0.5743       0.4016     0.4127        0.5758
4.000  -5.17819218375539  1.151  2.32307  0.04536  0.90000  0.01458020631717  -2.19947  2.83992  -0.00021  -0.00341  -0.001798  -27.131809   0.208748   0.476850   0.735940   0.2935047212753080   0.5400  0.3810   0.6600       0.3766     0.3728        0.5299       0.4104     0.3862        0.5636       0.3621     0.4064        0.5443       0.3943     0.3906        0.5550
4.500  -5.17602497589932  1.151  2.37009  0.04536  0.90000  0.01458710652043  -2.12528  2.82802  -0.00021  -0.00421  -0.001701  -27.792990   0.207737   0.462230   0.704070   0.2630000000000000   0.5250  0.3650   0.6400       0.3604     0.3635        0.5119       0.4116     0.3731        0.5555       0.3675     0.3831        0.5309       0.3853     0.3664        0.5317
5.000  -5.17408634241121  1.151  2.37009  0.04536  0.90000  0.01458710652043  -2.02646  2.82521  -0.00021  -0.00500  -0.001575  -28.313459   0.206721   0.452670   0.672200   0.2350000000000000   0.5220  0.3780   0.6450       0.3612     0.3588        0.5091       0.4469     0.3219        0.5508       0.3806     0.3163        0.4949       0.3799     0.3235        0.4990
    """)

# Coefficients specific to the site amplification
COEFFS_SITE_SLAB = CoeffsTable(sa_damping=5, table="""\
    imt    LnAmax1D1   LnAmax1D2   LnAmax1D3   LnAmax1D4     Src1D1     Src1D2     Src1D3     Src1D4     fsr1    fsr2    fsr3    fsr4
    pga     0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440   1.0000  1.0000  1.0000  1.0000
    0.005   0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440   1.0000  1.0000  1.0000  1.0000
    0.010   0.651810    0.706790    0.646240    0.404280   8.090000   1.882560   1.114440   0.836440   1.0000  1.0000  1.0000  1.0000
    0.020   0.653620    0.694650    0.638650    0.387890   6.992000   1.778610   1.124370   0.830000   1.0000  1.0000  1.0000  1.0500
    0.030   0.654670    0.687550    0.634210    0.378300   6.350000   1.717810   1.130170   0.826240   1.0000  1.0000  1.0000  0.5800
    0.040   0.652850    0.698920    0.606040    0.317370   4.883000   2.052340   1.150800   0.767580   1.0000  1.0060  1.0000  0.4820
    0.050   0.672640    0.701370    0.617160    0.309340   5.043000   2.387130   1.239710   0.786320   1.0000  0.8510  1.0000  0.4720
    0.060   0.699660    0.724450    0.637970    0.325300   6.271000   2.833990   1.348190   0.837750   1.0000  0.8030  1.0440  0.5060
    0.070   0.717130    0.743430    0.654370    0.354120   7.667000   3.294470   1.451810   0.926160   1.0000  0.9180  0.9750  0.5870
    0.080   0.716030    0.785980    0.680190    0.392820   9.034000   3.990910   1.583150   1.022280   1.0000  1.0620  0.9640  0.6830
    0.090   0.725610    0.797210    0.708890    0.421840  11.251000   4.465760   1.732920   1.118020   1.0000  1.1060  0.9800  0.7820
    0.100   0.742000    0.816680    0.718810    0.437360  14.817000   5.045610   1.841340   1.165780   1.0000  1.0710  0.9700  0.8230
    0.120   0.762360    0.845230    0.725810    0.472080  14.817000   5.899600   2.030290   1.285510   0.0000  0.9515  1.0220  1.0290
    0.140   0.752150    0.782960    0.745250    0.512780  14.817000   5.053530   2.281330   1.398080   0.0000  0.6720  0.8890  0.9910
    0.150   0.738190    0.794800    0.761030    0.534320  14.817000   5.204900   2.444130   1.443270   0.0000  0.6310  0.8610  0.9830
    0.160   0.719110    0.808610    0.768130    0.550220  14.817000   5.386940   2.580170   1.471770   0.0000  0.6000  0.8310  0.9730
    0.180   0.654080    0.843310    0.756900    0.572790  14.817000   5.871650   2.741610   1.546940   0.0000  0.5710  0.7480  0.9790
    0.200   0.583950    0.877700    0.717850    0.596740  14.817000   6.573910   2.825870   1.644010   0.0000  0.5650  0.6500  1.0060
    0.250   0.583950    0.937670    0.654700    0.611360  14.817000   8.500000   2.718930   1.790130   0.0000  0.6010  0.4790  1.0270
    0.300   0.583950    0.950000    0.696190    0.626380  14.817000  10.670300   2.417590   1.823450   0.0000  0.5790  0.4490  1.0210
    0.350   0.583950    1.000000    0.779070    0.630120  14.817000  10.670300   2.303750   1.790370   0.0000  0.6790  0.4820  1.0030
    0.400   0.583950    1.000000    0.827760    0.647730  14.817000  10.670300   2.236250   1.768440   0.0000  0.6550  0.4990  1.0100
    0.450   0.583950    1.000000    0.876450    0.641520  14.817000  10.670300   2.216780   1.675390   0.0000  0.6150  0.5150  0.9850
    0.500   0.583950    1.000000    0.925140    0.655820  14.817000  10.670300   2.243380   1.625390   0.0000  0.5500  0.5300  0.9900
    0.600   0.583950    1.000000    0.973830    0.686680  14.817000  10.670300   2.805350   1.524530   0.0000  0.0000  0.5300  1.0060
    0.700   0.583950    1.000000    1.022520    0.705600  14.817000  10.670300   6.658390   1.397240   0.0000  0.0000  0.4990  1.0000
    0.800   0.583950    1.000000    1.071220    0.714290  14.817000  10.670300  30.000000   1.320290   0.0000  0.0000  0.3690  1.0000
    0.900   0.583950    1.000000    1.119910    0.703880  14.817000  10.670300  30.000000   1.266370   0.0000  0.0000  0.3000  0.9600
    1.000   0.583950    1.000000    1.168600    0.678130  14.817000  10.670300  30.000000   1.226800   0.0000  0.0000  0.2000  0.9040
    1.250   0.583950    1.000000    1.217290    0.611190  14.817000  10.670300  30.000000   1.220650   0.0000  0.0000  0.0000  0.7380
    1.500   0.583950    1.000000    1.265980    0.547360  14.817000  10.670300  30.000000   1.318050   0.0000  0.0000  0.0000  0.5350
    2.000   0.583950    1.000000    1.314670    0.459440  14.817000  10.670300  30.000000   2.124850   0.0000  0.0000  0.0000  0.3580
    2.500   0.583950    1.000000    1.363360    0.408460  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    3.000   0.583950    1.000000    1.412050    0.364210  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    3.500   0.583950    1.000000    1.460750    0.329840  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    4.000   0.583950    1.000000    1.509440    0.309120  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    4.500   0.583950    1.000000    1.558130    0.292510  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    5.000   0.583950    1.000000    1.606820    0.547360  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    """)


@get_magnitude_scaling_term.add(
    const.TRT.ACTIVE_SHALLOW_CRUST, const.TRT.UPPER_MANTLE)
def get_magnitude_scaling_term_asc(trt, C, ctx):
    """
    Returns the magnitude scaling term in equations 1 and 2
    """
    return np.where(ctx.mag <= CONSTANTS["m_c"],
                    C["ccr"] * ctx.mag,
                    C["ccr"] * CONSTANTS["m_c"] +
                    C["dcr"] * (ctx.mag - CONSTANTS["m_c"]))


@get_magnitude_scaling_term.add(const.TRT.SUBDUCTION_INTERFACE)
def get_magnitude_scaling_term_SInter(trt, C, ctx):
    """
    Returns magnitude scaling term, which is dependent on top of rupture
    depth - as described in equations 1 and 2
    """
    c_int = np.where(ctx.ztor > 25.0, C["cint"], C["cintS"])
    return np.where(ctx.mag <= CONSTANTS["m_c"], c_int * ctx.mag,
                    c_int * CONSTANTS["m_c"] +
                    C["dint"] * (ctx.mag - CONSTANTS["m_c"]))


@get_magnitude_scaling_term.add(const.TRT.SUBDUCTION_INTRASLAB)
def get_magnitude_scaling_term_sslab(trt, C, ctx):
    """
    Returns the magnitude scaling defined in equation 1
    """
    m_c = CONSTANTS["m_c"]
    return np.where(
        ctx.mag <= m_c,
        C["cSL"] * ctx.mag + C["cSL2"] * (ctx.mag - CONSTANTS["m_sc"]) ** 2.,
        C["cSL"] * m_c + C["cSL2"] * (m_c - CONSTANTS["m_sc"]) ** 2. +
        C["dSL"] * (ctx.mag - m_c))


get_sof_term = CallableDict()


@get_sof_term.add(const.TRT.ACTIVE_SHALLOW_CRUST)
def get_sof_term_asc(trt, C, ctx):
    """
    Shallow crustal faults have a style-of-faulting dependence as
    normal faulting is found to produce higher ground motion (equation 1)
    """
    res = np.zeros_like(ctx.rake)
    # adjustment for normal faulting
    res[(ctx.rake <= -45.0) & (ctx.rake >= -135.0)] = C["FN_CR"]
    return res


@get_sof_term.add(const.TRT.UPPER_MANTLE)
def get_sof_term_um(trt, C, ctx):
    """
    In the case of the upper mantle events separate coefficients
    are considered for normal, reverse and strike-slip
    """
    res = np.zeros_like(ctx.rake)
    # adjustment for normal faulting
    res[(ctx.rake <= -45.0) & (ctx.rake >= -135.0)] = C["FN_UM"]
    # adjustment for reverse faulting
    res[(ctx.rake > 45.0) & (ctx.rake < 135.0)] = C["FRV_UM"]
    return res


@get_sof_term.add(const.TRT.SUBDUCTION_INTERFACE)
def get_sof_term_SInter(trt, C, ctx):
    """
    No style of faulting dependence here
    """
    return 0.0


@get_sof_term.add(const.TRT.SUBDUCTION_INTRASLAB)
def get_sof_term_sslab(trt, C, ctx):
    """
    No style of faulting dependence here
    """
    return 0.0


get_depth_term = CallableDict()


@get_depth_term.add(const.TRT.ACTIVE_SHALLOW_CRUST)
def get_depth_term_asc(trt, C, ctx):
    """
    Returns the top-of-rupture depth scaling (equation 1)
    """
    return C["bcr"] * ctx.ztor


@get_depth_term.add(const.TRT.UPPER_MANTLE)
def get_depth_term_um(trt, C, ctx):
    """
    No top of rupture depth is considered for upper mantle events
    """
    return 0.0


@get_depth_term.add(const.TRT.SUBDUCTION_INTERFACE)
def get_depth_term_SInter(trt, C, ctx):
    """
    Returns depth term (dependent on top of rupture depth) as given
    in equations 1 and 2
    """
    return (C["bint"] * ctx.ztor)


@get_depth_term.add(const.TRT.SUBDUCTION_INTRASLAB)
def get_depth_term_sslab(trt, C, ctx):
    """
    Returns depth term (dependent on top of rupture depth) as given
    in equations 1

    Note that there is a ztor cap of 100 km that is introduced in the
    Fortran code but not mentioned in the original paper!
    """
    return np.where(ctx.ztor > 100., C["bSLH"] * 100.0, C["bSLH"] * ctx.ztor)


get_distance_term = CallableDict()


@get_distance_term.add(const.TRT.ACTIVE_SHALLOW_CRUST)
def get_distance_term_asc(trt, C, ctx, volc_arc_str=None, pgn_store=None,
                          pgn_per_zone=None):
    """
    Returns the distance scaling term defined in equation 3
    """
    x_ij = ctx.rrup
    gn_exp = np.exp(C["c1"] + 6.5 * C["c2"])

    # Geometric attenuation scaling described in equation 6
    g_n = C["gcrN"] * np.log(CONSTANTS["xcro"] + 30. + gn_exp) *\
        np.ones_like(x_ij)
    idx = x_ij <= 30.0
    if np.any(idx):
        g_n[idx] = C["gcrN"] * np.log(CONSTANTS["xcro"] +
                                      x_ij[idx] + gn_exp)
    # equation 5
    c_m = np.minimum(ctx.mag, CONSTANTS["m_c"])
    # equation 4
    r_ij = CONSTANTS["xcro"] + x_ij + np.exp(C["c1"] + C["c2"] * c_m)
    return C["gcr"] * np.log(r_ij) + C["gcrL"] * np.log(x_ij + 200.0) +\
        g_n + C["ecr"] * x_ij + C["ecrV"] * ctx.rvolc + C["gamma_S"]


@get_distance_term.add(const.TRT.UPPER_MANTLE)
def get_distance_term_um(trt, C, ctx, volc_arc_str=None, pgn_store=None,
                         pgn_per_zone=None):
    """
    Returns the distance attenuation term
    """
    x_ij = ctx.rrup
    gn_exp = np.exp(C["c1"] + 6.5 * C["c2"])
    g_n = C["gcrN"] * np.log(CONSTANTS["xcro"] + 30. + gn_exp) *\
        np.ones_like(x_ij)
    idx = x_ij <= 30.0
    if np.any(idx):
        g_n[idx] = C["gcrN"] * np.log(CONSTANTS["xcro"] +
                                      x_ij[idx] + gn_exp)
    c_m = np.minimum(ctx.mag, CONSTANTS["m_c"])
    r_ij = CONSTANTS["xcro"] + x_ij + np.exp(C["c1"] + C["c2"] * c_m)
    return (C["gUM"] * np.log(r_ij) +
            C["gcrL"] * np.log(x_ij + 200.0) +
            g_n + C["eum"] * x_ij + C["ecrV"] * ctx.rvolc + C["gamma_S"])


@get_distance_term.add(const.TRT.SUBDUCTION_INTERFACE)
def get_distance_term_SInter(trt, C, ctx, volc_arc_str=None, pgn_store=None,
                             pgn_per_zone=None):
    """
    Returns distance scaling term, dependent on top of rupture depth,
    as described in equation 6
    """
    x_ij = ctx.rrup
    # Get r_ij - distance for geometric spreading (equations 4 & 5)
    c_m = np.minimum(ctx.mag, CONSTANTS["m_c"])
    r_ij = CONSTANTS["xinto"] + x_ij + np.exp(C["alpha"] + C["beta"] * c_m)
    # Get factors common to both shallow and deep
    dterm = C["gint"] * np.log(r_ij) + C["eintV"] * ctx.rvolc + C["gammaint"]
    dterm += np.where(
        ctx.ztor < 25.,
        # Shallow events have geometric and anelastic attenuation term
        (C["gintLS"] * np.log(x_ij + 200.0) + C["eintS"] * x_ij +
         C["gamma_ints"]),
        # Deep events do not have an anelastic attenuation term
        C["gintLD"] * np.log(x_ij + 200.0))
    return dterm


@get_distance_term.add(const.TRT.SUBDUCTION_INTRASLAB)
def get_distance_term_sslab(trt, C, ctx, volc_arc_str=None, pgn_store=None,
                            pgn_per_zone=None):
    """
    Returns the distance scaling term in equation 2a

    Non-ergodic path effects are applied here if specified within an
    implementation of :class:`ZhaoEtAl2016SSlabPErg`.
    """
    cctx = copy.copy(ctx)
    # Check if need to apply non-ergodic path effects
    if volc_arc_str is not None:
        # Get distance traversed per travel path through volcanic zones (rvolc),
        # with rvolc capped at 80km if total distance traversed through zones is 
        # greater than 80km, and set to 12 km if zones are traversed but the
        # total distance is less than 12 km. This min/max constraint to rvolc
        # is detailed within the publications for the Zhao et al. 2016 GMMs
        r_volc = volc_perg.get_rvolcs(ctx, pgn_store, pgn_per_zone)     
        cctx.rvolc = r_volc
        
    x_ij = cctx.rrup
    # Get anelastic scaling term in equation 5
    qslh = np.where(cctx.ztor >= 50., C["eSLH"] * (0.02 * cctx.ztor - 1.0), 0)

    # Get r_ij - distance for geometric spreading (equations 3 and 4)
    c_m = np.minimum(cctx.mag, CONSTANTS["m_c"])
    r_ij = x_ij + np.exp(C["alpha"] + C["beta"] * c_m)
    return C["gSL"] * np.log(r_ij) + \
        C["gLL"] * np.log(x_ij + 200.) +\
        C["eSL"] * x_ij + qslh * x_ij +\
        C["eSLV"] * cctx.rvolc + C["gamma"]


def _get_ln_sf(trt, C, C_SITE, idx, n_sites, ctx):
    """
    Returns the log SF term required for equation 9

    For events deeper than 25 km the rock-site factor is slightly different
    for site classes SCII, SCIII, SCIV
    """
    ln_sf = np.zeros(n_sites)
    subint = trt == const.TRT.SUBDUCTION_INTERFACE
    for i in range(1, 5):
        ln_sf[idx[i]] += C["lnSC1AM"] - C_SITE["LnAmax1D{:g}".format(i)]
        if i > 1:
            for sid in idx[i].nonzero()[0]:
                if subint and ctx.ztor[sid] > 25.0:
                    # For deep events site classes 5, 6, and 7 are used
                    loc = i + 3
                else:
                    # For shallow events the conventional approach applies
                    loc = i
                ln_sf[sid] += C["S{:g}".format(loc)]
    return ln_sf


def _get_ln_a_n_max(trt, C, n_sites, idx, ctx):
    """
    Defines the rock site amplification defined in equations 7a and 7b

    For events deeper than 25 km the rock-site factor is slightly different
    for site classes SCII, SCIII, SCIV
    """
    ln_a_n_max = C["lnSC1AM"] * np.ones(n_sites)
    subint = trt == const.TRT.SUBDUCTION_INTERFACE
    for i in [2, 3, 4]:
        for sid in idx[i].nonzero()[0]:
            # For deep events site classes 5, 6 and 7 are used
            if subint and ctx.ztor[sid] > 25.0:
                loc = i + 3
            else:
                loc = i
            ln_a_n_max[sid] += C["S{:g}".format(loc)]
    return ln_a_n_max


def add_site_amplification(trt, C, C_SITE, sa_rock, idx, ctx):
    """
    Applies the site amplification scaling defined in equations from 10
    to 15
    """
    n_sites = len(ctx.vs30)
    # Convert from reference rock to hard rock
    hard_rock_sa = sa_rock - C["lnSC1AM"]
    # Gets the elastic site amplification ratio
    ln_a_n_max = _get_ln_a_n_max(trt, C, n_sites, idx, ctx)

    # Retrieves coefficients needed to determine smr
    sreff, sreffc, f_sr = _get_smr_coeffs(C, C_SITE, idx, n_sites,
                                          hard_rock_sa)
    snc = np.zeros(n_sites)
    alpha = CONSTANTS["alpha"]
    beta = CONSTANTS["beta"]
    smr = np.zeros(n_sites)
    sa_soil = hard_rock_sa + ln_a_n_max
    # Get lnSF
    ln_sf = _get_ln_sf(trt, C, C_SITE, idx, n_sites, ctx)
    lnamax_idx = np.exp(ln_a_n_max) < 1.25
    not_lnamax_idx = np.logical_not(lnamax_idx)
    for i in range(1, 5):
        idx_i = idx[i]
        if not np.any(idx_i):
            # No sites of the given site class
            continue
        idx2 = np.logical_and(lnamax_idx, idx_i)
        if np.any(idx2):
            # Use the approximate method for SRC and SNC
            c_a = C_SITE["LnAmax1D{:g}".format(i)] /\
                (np.log(beta) - np.log(sreffc[idx2] ** alpha + beta))
            c_b = -c_a * np.log(sreffc[idx2] ** alpha + beta)

            snc[idx2] = np.exp((c_a * (alpha - 1.) *
                               np.log(beta) * np.log(10.0 * beta) -
                               np.log(10.0) * (c_b + ln_sf[idx2])) /
                               (c_a * (alpha * np.log(10.0 * beta) -
                                np.log(beta))))
        # For the cases when ln_a_n_max >= 1.25
        idx2 = np.logical_and(not_lnamax_idx, idx_i)
        if np.any(idx2):
            snc[idx2] = (np.exp((ln_a_n_max[idx2] *
                         np.log(sreffc[idx2] ** alpha + beta) -
                         ln_sf[idx2] * np.log(beta)) /
                         C_SITE["LnAmax1D{:g}".format(i)]) - beta) **\
                         (1.0 / alpha)

        smr[idx_i] = sreff[idx_i] * (snc[idx_i] / sreffc[idx_i]) *\
            f_sr[idx_i]
        # For the cases when site class = i and SMR != 0
        idx2 = np.logical_and(idx_i, np.fabs(smr) > 0.0)
        if np.any(idx2):
            sa_soil[idx2] += (-C_SITE["LnAmax1D{:g}".format(i)] *
                              (np.log(smr[idx2] ** alpha + beta) -
                              np.log(beta)) /
                              (np.log(sreffc[idx2] ** alpha + beta) -
                               np.log(beta)))
    return sa_soil


def _get_smr_coeffs(C, C_SITE, idx, n_sites, sa_rock):
    """
    Returns the SReff and SReffC terms needed for equation 14 and 15
    """
    # Get SR
    sreff = np.zeros(n_sites)
    sreffc = np.zeros(n_sites)
    f_sr = np.zeros(n_sites)
    for i in range(1, 5):
        sreff[idx[i]] += (np.exp(sa_rock[idx[i]]) * IMF[i])
        sreffc[idx[i]] += (C_SITE["Src1D{:g}".format(i)] * IMF[i])
        # Get f_SR
        f_sr[idx[i]] += C_SITE["fsr{:g}".format(i)]
    return sreff, sreffc, f_sr


def _get_site_classification(vs30):
    """
    Define the site class categories based on Vs30. Returns a
    vector of site class values and a dictionary containing logical
    vectors for each of the site classes
    """
    site_class = np.ones(vs30.shape, dtype=int)
    idx = {}
    idx[1] = vs30 > 600.
    idx[2] = np.logical_and(vs30 > 300., vs30 <= 600.)
    idx[3] = np.logical_and(vs30 > 200., vs30 <= 300.)
    idx[4] = vs30 <= 200.
    for i in [2, 3, 4]:
        site_class[idx[i]] = i
    return site_class, idx


def get_volc_zones(volc_polygons):
    """
    Construct polygons from the vertex coordinates provided for each volcanic
    zone and assign the associated zone id
    """
    # Get the volc zone polygons
    with fiona.open(volc_polygons,'r') as inp:
        zone_id, zone_lons, zone_lats = {}, {}, {}
        for i, f in enumerate(inp):
            
            # Get zone_id
            zone_id[i] = pd.Series(f['properties']).iloc[0]
            
            # Per zone get lat and lon of each polygon vertices
            for c, coo in enumerate(f['geometry']['coordinates'][0]):
                zone_lons[zone_id[i], c] = f['geometry']['coordinates'][0][c][0]
                zone_lats[zone_id[i], c] = f['geometry']['coordinates'][0][c][1]

    # Store all required info in dict
    pgn_store = {'zone': zone_id,
                 'zone_lons': zone_lons,
                 'zone_lats': zone_lats}

    # Set dict for volcanic zones
    zone_dict = {pgn_store['zone'][z]: {} for z in pgn_store['zone']}

    # Get polygon per zone
    pnts_zone, zone_pgn = zone_dict, zone_dict
    for zone in pgn_store['zone']:
        zid = pgn_store['zone'][zone]
        for c, coo in enumerate(pgn_store['zone_lons']):
            if pgn_store['zone'][zone] in coo:
                pnts_zone[zid][c] = Point(pgn_store['zone_lons'][zid, coo[1]],
                                          pgn_store['zone_lats'][zid, coo[1]])
        zone_pnts = []
        for coo in pnts_zone[zid]:
            zone_pnts.append(pnts_zone[zid][coo])
        zone_pgn[zid] = Polygon(zone_pnts)
        
    return pgn_store, zone_pgn


class ZhaoEtAl2016Asc(GMPE):
    """
    Implements the GMPE of Zhao et al (2016a) for shallow crustal and upper
    mantle events from Japan. Only the shallow crustal version is implemented
    here.

    Zhao, J. X., Zhou, S., Zhou, J., Zhao, C., Zhang, H., Zhang, Y., Gao, P.,
    Lan, X., Rhoades, D. A., Fukushima, Y., Somerville, P., Irikura, K.,
    (2016c), "Ground-Motion Prediction Equations for Shallow Crustal and
    Uppe-Mantle Earthquakes in Japan Using Site Class and Simple Geometric
    Attenuation Functions", Bulletin of the Seismological Society of America,
    106(4), 1518-1534

    Main version with standard deviations independent of site term
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components :
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters is Vs30 (converted to site class)
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, top-of-rupture depth and
    #: style of faulting (rake)
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor', 'rake'}

    #: Required distance measure is Rrup and Rvolc
    REQUIRES_DISTANCES = {'rrup', 'rvolc'}

    def __init__(self, volc_arc_file=None):
        if volc_arc_file is not None:
            with open(volc_arc_file, 'rb') as fle:
                self.volc_arc_str = fle.read().decode('utf-8')
            self.pgn_store, self.pgn_per_zone = get_volc_zones(
                self.volc_arc_str)
        else:
            self.volc_arc_str = None
            self.pgn_store = None
            self.pgn_per_zone = None

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            C_SITE = self.COEFFS_SITE[imt]
            trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
            _s_c, idx = _get_site_classification(ctx.vs30)
            volc_arc_str = self.volc_arc_str
            pgn_store = self.pgn_store
            pgn_per_zone = self.pgn_per_zone
            sa_rock = (get_magnitude_scaling_term(trt, C, ctx) +
                       get_sof_term(trt, C, ctx) +
                       get_depth_term(trt, C, ctx) +
                       get_distance_term(trt, C, ctx, volc_arc_str, pgn_store,
                                         pgn_per_zone))
            mean[m] = add_site_amplification(trt, C, C_SITE, sa_rock, idx, ctx)
            
            if self.__class__.__name__.endswith('SiteSigma'):
                for i in range(1, 5):
                    phi[m, idx[i]] += C["sc{:g}_sigma_S".format(i)]
            else:
                phi[m] = C["sigma"]

            tau[m] = C["tau"]
            sig[m] = np.sqrt(phi[m] ** 2. + tau[m] ** 2.)

    # Coefficients taken from Excel spreadsheet provided by the author
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt        c1     c2      ccr      cum      dcr              FN_CR    FRV_UM              FN_UM  FUM                 bcr       gcr       gUM      gcrN               gcrL       ecr                 eum      ecrV              gamma_S  lnSC1AM         S2        S3        S4  sigma    tau  sigma_T  sc1_sigma_S  sc1_tau_S  sc1_sigma_ST   sc2_sigma_S  sc2_tau_S  sc2_sigma_ST  sc3_sigma_S  sc3_tau_S  sc3_sigma_ST  sc4_sigma_S  sc4_tau_S  sc4_sigma_ST
    pga    -3.224  0.900  1.07312  1.07312  0.20000  0.312820000000000  -0.20236  0.251935430429416  0.0   0.009070000000000  -1.26034  -1.09985  -0.49919  1.265640000000000  -0.00794  -0.010830000000000  -0.00628   -9.087242726439600    0.323    0.28877   0.12210   0.20813  0.556  0.391    0.680       0.4153     0.3581        0.5484        0.4363     0.3620        0.5669       0.4235     0.3486        0.5485       0.4426     0.2778        0.5225
    0.005  -3.224  0.900  1.07312  1.07312  0.20000  0.312820000000000  -0.20236  0.251935430429416  0.0   0.009070000000000  -1.26034  -1.09985  -0.49919  1.265640000000000  -0.00794  -0.010830000000000  -0.00628   -9.087242726439600    0.323    0.28877   0.12210   0.20813  0.556  0.391    0.680       0.4153     0.3581        0.5484        0.4363     0.3620        0.5669       0.4235     0.3486        0.5485       0.4426     0.2778        0.5225
    0.010  -3.357  0.909  1.07850  1.07850  0.20000  0.315680000000000  -0.21425  0.258372637504816  0.0   0.009070000000000  -1.26949  -1.10720  -0.48684  1.241487880676370  -0.00772  -0.010580000000000  -0.00629   -9.052058022318450    0.205    0.29991   0.10321   0.21925  0.556  0.390    0.679       0.4142     0.3581        0.5475        0.4356     0.3627        0.5668       0.4230     0.3482        0.5479       0.4419     0.2804        0.5233
    0.020  -3.552  0.927  1.07254  1.07254  0.20000  0.318540000000000  -0.22125  0.260697166781076  0.0   0.009070000000000  -1.28775  -1.11766  -0.44645  1.198941940195550  -0.00756  -0.010505216376958  -0.00634   -8.857750749461700    0.083    0.29778   0.11109   0.21713  0.555  0.396    0.682       0.4123     0.3581        0.5460        0.4344     0.3646        0.5671       0.4226     0.3483        0.5477       0.4418     0.2823        0.5243
    0.030  -3.640  0.937  1.05736  1.05736  0.20000  0.320220000000000  -0.22306  0.260150407731831  0.0   0.009070000000000  -1.29619  -1.11392  -0.42175  1.186537103020870  -0.00788  -0.011005243836384  -0.00647   -8.627942448779750    0.041    0.22535   0.08972   0.15948  0.553  0.408    0.687       0.4089     0.3625        0.5465        0.4307     0.3580        0.5601       0.4207     0.3544        0.5501       0.4415     0.2857        0.5259
    0.040  -3.758  0.944  1.03568  1.03568  0.20000  0.321410000000000  -0.22334  0.258909018258196  0.0   0.009070000000000  -1.25147  -1.07971  -0.37622  1.142133802990220  -0.00863  -0.011487892527436  -0.00681   -8.398219253745690    0.034    0.15865   0.04037   0.07029  0.558  0.438    0.710       0.4072     0.3832        0.5591        0.4275     0.3666        0.5632       0.4208     0.3544        0.5501       0.4435     0.2881        0.5289
    0.050  -3.826  0.948  1.00578  1.00578  0.20000  0.321850000000000  -0.22297  0.257458255516038  0.0   0.009070000000000  -1.14724  -0.98606  -0.43576  1.141373265957230  -0.00988  -0.012291799210266  -0.00710   -8.153070000000000    0.046    0.08257  -0.05934  -0.03529  0.564  0.460    0.728       0.4059     0.4052        0.5735        0.4294     0.3760        0.5708       0.4168     0.3508        0.5448       0.4446     0.2945        0.5332
    0.060  -3.890  0.956  0.98413  0.98413  0.20000  0.324710000000000  -0.22229  0.255956496918906  0.0   0.009070000000000  -1.09126  -0.93901  -0.46789  1.157491249527060  -0.01075  -0.012739417109939  -0.00724   -8.003270000000000    0.069    0.05542  -0.10956  -0.09017  0.577  0.481    0.751       0.4066     0.4341        0.5948        0.4304     0.3911        0.5816       0.4156     0.3453        0.5404       0.4415     0.3082        0.5384
    0.070  -3.965  0.967  0.98059  0.98059  0.20000  0.328600000000000  -0.22145  0.254464785542036  0.0   0.009070000000000  -1.04676  -0.90036  -0.50260  1.186791451212470  -0.01130  -0.013080135792042  -0.00734   -8.047830000000000    0.098    0.04177  -0.13262  -0.09583  0.599  0.488    0.772       0.4171     0.4517        0.6148        0.4329     0.4057        0.5933       0.4215     0.3605        0.5546       0.4407     0.3378        0.5552
    0.080  -4.055  0.980  0.98634  0.98634  0.20000  0.329844812501483  -0.22053  0.253008191936176  0.0   0.009070000000000  -1.01364  -0.87064  -0.53802  1.223378486073060  -0.01164  -0.013312834482819  -0.00741   -8.196910000000000    0.132    0.06040  -0.13537  -0.07321  0.616  0.481    0.782       0.4255     0.4745        0.6374        0.4361     0.4247        0.6088       0.4220     0.3821        0.5693       0.4351     0.3557        0.5619
    0.090  -4.153  0.995  0.99121  0.99121  0.20000  0.336373431249984  -0.21956  0.251596694854290  0.0   0.009070000000000  -0.99232  -0.85080  -0.57301  1.264040913700510  -0.01182  -0.013454810030999  -0.00746   -8.350790000000000    0.169    0.09304  -0.12513  -0.03629  0.629  0.477    0.789       0.4315     0.4884        0.6517        0.4417     0.4445        0.6266       0.4161     0.3958        0.5743       0.4374     0.3784        0.5784
    0.100  -4.255  1.009  1.00033  1.00033  0.20000  0.340964949991461  -0.21858  0.250233442665255  0.0   0.009070000000000  -0.98315  -0.84175  -0.60839  1.305257984164180  -0.01184  -0.013478869951054  -0.00749   -8.524300000000000    0.208    0.15210  -0.07090   0.01110  0.641  0.460    0.789       0.4371     0.4932        0.6590        0.4478     0.4485        0.6338       0.4241     0.4229        0.5989       0.4402     0.4182        0.6072
    0.120  -4.466  1.040  1.03440  1.03440  0.20000  0.345623419543235  -0.21661  0.247649908306841  0.0   0.009579251858235  -0.97311  -0.82925  -0.67012  1.392835221341830  -0.01174  -0.013487990193394  -0.00751   -9.054780000000000    0.288    0.26161   0.00261   0.10298  0.657  0.437    0.789       0.4515     0.4927        0.6683        0.4476     0.4641        0.6448       0.4332     0.4768        0.6442       0.4594     0.4216        0.6236
    0.140  -4.677  1.070  1.08388  1.08388  0.20000  0.345964793275106  -0.21469  0.245243568556044  0.0   0.010548033973543  -0.98324  -0.83484  -0.72524  1.477695244453800  -0.01142  -0.013335243001700  -0.00748   -9.676400000000000    0.370    0.35467   0.11202   0.21434  0.663  0.414    0.782       0.4559     0.4906        0.6697        0.4553     0.4758        0.6586       0.4347     0.4592        0.6323       0.4697     0.3869        0.6085
    0.150  -4.781  1.085  1.10602  1.10602  0.20000  0.344999481637875  -0.21374  0.244100676565134  0.0   0.011218017682426  -0.99261  -0.84153  -0.74977  1.518814263594270  -0.01123  -0.013231344388198  -0.00746   -9.965950000000000    0.412    0.39410   0.15670   0.25574  0.666  0.402    0.778       0.4594     0.4815        0.6655        0.4547     0.4817        0.6624       0.4380     0.4519        0.6294       0.4707     0.3867        0.6092
    0.160  -4.883  1.100  1.12674  1.12674  0.20000  0.343465417412490  -0.21282  0.242994687815017  0.0   0.011700559401692  -1.00423  -0.85033  -0.77240  1.558838786529320  -0.01101  -0.013114569632387  -0.00743  -10.241600000000000    0.453    0.42523   0.19678   0.29811  0.671  0.384    0.773       0.4647     0.4725        0.6627        0.4607     0.4820        0.6668       0.4419     0.4617        0.6391       0.4744     0.3788        0.6071
    0.180  -5.085  1.129  1.16455  1.16455  0.20000  0.339107164829684  -0.21102  0.240884343952180  0.0   0.012332909878059  -1.03299  -0.87328  -0.81285  1.634757732666460  -0.01054  -0.012840476069927  -0.00735  -10.752000000000000    0.535    0.47642   0.27414   0.36360  0.680  0.380    0.779       0.4721     0.4640        0.6619        0.4697     0.4830        0.6737       0.4514     0.4660        0.6488       0.4784     0.3903        0.6174
    0.200  -5.233  1.151  1.19837  1.19837  0.20000  0.333545099152249  -0.20929  0.238895952015333  0.0   0.013457084876985  -1.06493  -0.89945  -0.84625  1.706045133394880  -0.01007  -0.012558176324852  -0.00725  -11.224920000000000    0.606    0.51169   0.33785   0.42568  0.692  0.359    0.780       0.4722     0.4708        0.6668        0.4800     0.4932        0.6882       0.4493     0.4452        0.6325       0.4825     0.4010        0.6274
    0.250  -5.229  1.151  1.27000  1.27000  0.20000  0.316942763583834  -0.20526  0.234370987754789  0.0   0.016170000000000  -1.15136  -0.97276  -0.90575  1.862468560694100  -0.00890  -0.011816876971470  -0.00696  -12.262750000000000    0.670    0.55177   0.47868   0.55643  0.694  0.340    0.773       0.4780     0.4650        0.6669        0.4882     0.5436        0.7306       0.4626     0.4192        0.6243       0.4843     0.3942        0.6244
    0.300  -5.226  1.151  1.32852  1.32852  0.20000  0.299124734648411  -0.20159  0.230357423625167  0.0   0.018310000000000  -1.23723  -1.04809  -0.93933  1.991624592628190  -0.00784  -0.011099993928613  -0.00661  -13.141810000000000    0.710    0.55325   0.57391   0.65844  0.688  0.344    0.770       0.4906     0.4595        0.6722        0.4991     0.5246        0.7241       0.4833     0.4356        0.6507       0.4930     0.3725        0.6179
    0.350  -5.223  1.151  1.37801  1.37801  0.20000  0.281669557686284  -0.19822  0.226742010930494  0.0   0.019800000000000  -1.31736  -1.12034  -0.95403  2.098225191698050  -0.00691  -0.010436248715154  -0.00624  -13.902540000000000    0.719    0.53555   0.63824   0.73536  0.675  0.353    0.762       0.4918     0.4432        0.6621        0.5043     0.4872        0.7012       0.4783     0.4689        0.6698       0.4914     0.3421        0.5988
    0.400  -5.221  1.151  1.42087  1.42087  0.20000  0.265209162746323  -0.19511  0.223445783566271  0.0   0.020780000000000  -1.38989  -1.18735  -0.95484  2.186300573524260  -0.00610  -0.009830759490494  -0.00586  -14.573550000000000    0.706    0.50855   0.67945   0.79334  0.667  0.363    0.759       0.4951     0.4296        0.6555        0.5074     0.4722        0.6931       0.4720     0.4821        0.6747       0.4783     0.3466        0.5907
    0.450  -5.218  1.151  1.45868  1.45868  0.20000  0.249966529741596  -0.19221  0.220411614509675  0.0   0.021380000000000  -1.45461  -1.24859  -0.94513  2.259336928898360  -0.00541  -0.009285306710044  -0.00548  -15.173840000000000    0.693    0.47913   0.70517   0.83853  0.665  0.359    0.756       0.4927     0.4310        0.6546        0.5074     0.4651        0.6883       0.4944     0.4638        0.6779       0.4787     0.3594        0.5986
    0.500  -5.216  1.151  1.49250  1.49250  0.19000  0.235980866829892  -0.18950  0.217596832776964  0.0   0.021680000000000  -1.51219  -1.30439  -0.92771  2.319726842585720  -0.00482  -0.008788091918160  -0.00511  -15.715670000000000    0.681    0.45094   0.72065   0.87505  0.664  0.361    0.756       0.4890     0.4323        0.6527        0.5149     0.4493        0.6834       0.4949     0.4327        0.6574       0.4764     0.3998        0.6220
    0.600  -5.213  1.151  1.55102  1.55102  0.17800  0.211571038601388  -0.18454  0.212501492886060  0.0   0.021610000000000  -1.60834  -1.40097  -0.87661  2.410718513737190  -0.00387  -0.007921609069809  -0.00439  -16.662190000000000    0.658    0.39849   0.72820   0.92621  0.669  0.362    0.761       0.4792     0.4402        0.6507        0.5177     0.4472        0.6841       0.4848     0.4577        0.6668       0.4854     0.4454        0.6588
    0.700  -5.210  1.151  1.60051  1.60051  0.16200  0.191334420072367  -0.18008  0.207971451817460  0.0   0.020940000000000  -1.68374  -1.48074  -0.81164  2.471787807358160  -0.00315  -0.007193263566848  -0.00374  -17.467280000000000    0.637    0.35254   0.71582   0.95627  0.670  0.370    0.765       0.4665     0.4390        0.6406        0.5044     0.4515        0.6770       0.4816     0.4712        0.6737       0.4707     0.4982        0.6854
    0.800  -5.208  1.151  1.64337  1.64337  0.14800  0.174557580328734  -0.17602  0.203882937318070  0.0   0.019870000000000  -1.74306  -1.54711  -0.73894  2.511003526994950  -0.00261  -0.006567782184498  -0.00315  -18.164530000000000    0.618    0.31707   0.69660   0.97619  0.674  0.378    0.773       0.4600     0.4491        0.6429        0.4954     0.4504        0.6696       0.4751     0.4622        0.6628       0.4837     0.5183        0.7089
    0.900  -5.206  1.151  1.68118  1.68118  0.13600  0.160616866070260  -0.17229  0.200149921480523  0.0   0.018540000000000  -1.78967  -1.60263  -0.66214  2.534178788957430  -0.00220  -0.006025164356083  -0.00261  -18.777980000000000    0.600    0.28896   0.67366   0.98819  0.673  0.386    0.775       0.4541     0.4579        0.6449        0.4834     0.4559        0.6645       0.4554     0.4781        0.6603       0.4729     0.5358        0.7146
    1.000  -5.204  1.151  1.71500  1.71500  0.12500  0.149000000000001  -0.16883  0.196710000000000  0.0   0.017040000000000  -1.82603  -1.64914  -0.58347  2.545383253429940  -0.00189  -0.005550701319875  -0.00214  -19.325620000000000    0.583    0.26685   0.64985   0.99485  0.670  0.390    0.776       0.4475     0.4663        0.6463        0.4720     0.4593        0.6586       0.4415     0.4743        0.6480       0.4709     0.5240        0.7045
    1.250  -5.200  1.151  1.78663  1.78663  0.10100  0.127608506221474  -0.16113  0.189110834221069  0.0   0.012920000000000  -1.88672  -1.73810  -0.40237  2.547066045238380  -0.00139  -0.004579681056724  -0.00119  -20.467050000000000    0.545    0.22889   0.59394   0.99639  0.660  0.399    0.771       0.4404     0.4644        0.6400        0.4595     0.4606        0.6506       0.4380     0.4495        0.6276       0.4627     0.4932        0.6763
    1.500  -5.196  1.151  1.84515  1.84515  0.08300  0.113816631375633  -0.15447  0.182585464558957  0.0   0.008630000000000  -1.91705  -1.79802  -0.24053  2.525806060977580  -0.00116  -0.003841842878586  -0.00054  -21.388220000000000    0.511    0.20778   0.55120   0.98814  0.656  0.397    0.767       0.4284     0.4546        0.6247        0.4499     0.4688        0.6497       0.4219     0.4633        0.6266       0.4564     0.4942        0.6727
    2.000  -5.191  1.151  1.93750  1.93750  0.05300  0.099176091595634  -0.14326  0.171710489423896  0.0   0.000420000000000  -1.93178  -1.86912  -0.03590  2.497512890223570  -0.00109  -0.002838451894609   0.00000  -22.811700000000000    0.454    0.18675   0.50247   0.96004  0.631  0.381    0.737       0.4148     0.4190        0.5896        0.4374     0.4530        0.6297       0.4172     0.4718        0.6298       0.4323     0.5195        0.6758
    2.500  -5.187  1.151  2.00913  2.00913  0.02967  0.093289958829313  -0.13399  0.162787337116202  0.0  -0.006870000000000  -1.91787  -1.90393   0.08743  2.478890119830560  -0.00125  -0.002226291691253   0.00000  -23.905120000000000    0.406    0.17749   0.48879   0.92903  0.605  0.376    0.713       0.4003     0.4084        0.5718        0.4343     0.4310        0.6119       0.3955     0.4530        0.6014       0.4128     0.5059        0.6529
    3.000  -5.183  1.151  2.06765  2.06765  0.01078  0.091055639803074  -0.12604  0.155180191692808  0.0  -0.013150000000000  -1.89632  -1.92241   0.17408  2.464735244149810  -0.00144  -0.001844374770841   0.00000  -24.794480000000000    0.364    0.16807   0.48245   0.89351  0.591  0.363    0.694       0.4033     0.4052        0.5717        0.4328     0.4152        0.5997       0.3995     0.4030        0.5674       0.4170     0.4886        0.6424
    3.500  -5.181  1.151  2.12357  2.12357  0.00000  0.090028774676100  -0.11905  0.148526449306405  0.0  -0.018490000000000  -1.87695  -1.93474   0.24501  2.452674190639510  -0.00159  -0.001603938312670   0.00000  -25.588720000000000    0.327    0.15988   0.47612   0.85603  0.578  0.363    0.682       0.4026     0.3861        0.5578        0.4214     0.3953        0.5778       0.4131     0.3803        0.5615       0.4265     0.4928        0.6517
    4.000  -5.178  1.151  2.13734  2.13734  0.00000  0.088965758728213  -0.11280  0.142598301048652  0.0  -0.022980000000000  -1.86168  -1.94360   0.31173  2.442705939276230  -0.00171  -0.001487903801684   0.00000  -26.046350000000000    0.294    0.15433   0.46978   0.81676  0.556  0.376    0.671       0.3804     0.3756        0.5346        0.4264     0.3681        0.5633       0.4060     0.3228        0.5187       0.4259     0.4510        0.6203
    4.500  -5.176  1.151  2.13734  2.13734  0.00000  0.087216625027152  -0.10713  0.137242613236394  0.0  -0.026720000000000  -1.85415  -1.95343   0.37949  2.433909230947000  -0.00176  -0.001451647632538   0.00000  -26.370080000000000    0.263    0.15116   0.46344   0.77379  0.542  0.377    0.661       0.3736     0.3595        0.5185        0.4290     0.3589        0.5593       0.3921     0.3069        0.4979       0.4256     0.4386        0.6111
    5.000  -5.174  1.151  2.13734  2.13734  0.00000  0.084444226520033  -0.10194  0.132351162212196  0.0  -0.029800000000000  -1.85292  -1.96352   0.45204  2.426728340621800  -0.00177  -0.001498616447348   0.00000  -26.677970000000000    0.235    0.15275   0.45711   0.72802  0.538  0.395    0.667       0.3831     0.3594        0.5253        0.4378     0.3298        0.5481       0.3779     0.3076        0.4873       0.4195     0.3774        0.5643
    """)

    # Coefficients specific to the site amplification
    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    imt    LnAmax1D1   LnAmax1D2   LnAmax1D3   LnAmax1D4     Src1D1     Src1D2     Src1D3     Src1D4      fsr1      fsr2      fsr3      fsr4
    pga     0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440  1.000000  1.000000  1.000000  1.000000
    0.005   0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440  1.000000  1.000000  1.000000  1.000000
    0.010   0.651810    0.706790    0.646240    0.404280   8.090000   1.882560   1.114440   0.836440  1.000000  1.200000  1.000000  1.000000
    0.020   0.653620    0.694650    0.638650    0.387890   6.992000   1.778610   1.124370   0.830000  1.000000  1.300000  1.000000  0.949000
    0.030   0.654670    0.687550    0.634210    0.378300   6.350000   1.717810   1.130170   0.826240  1.000000  1.253000  1.000000  0.550000
    0.040   0.652850    0.698920    0.606040    0.317370   4.883000   2.052340   1.150800   0.767580  1.000000  1.064000  1.000000  0.477000
    0.050   0.672640    0.701370    0.617160    0.309340   5.043000   2.387130   1.239710   0.786320  1.000000  1.120000  1.000000  0.492000
    0.060   0.699660    0.724450    0.637970    0.325300   6.271000   2.833990   1.348190   0.837750  1.000000  1.207000  1.000000  0.531000
    0.070   0.717130    0.743430    0.654370    0.354120   7.667000   3.294470   1.451810   0.926160  1.000000  1.238000  1.000000  0.613000
    0.080   0.716030    0.785980    0.680190    0.392820   9.034000   3.990910   1.583150   1.022280  1.000000  1.360000  1.000000  0.693000
    0.090   0.725610    0.797210    0.708890    0.421840  11.251000   4.465760   1.732920   1.118020  1.000000  1.355000  1.000000  0.780000
    0.100   0.742000    0.816680    0.718810    0.437360  14.817000   5.045610   1.841340   1.165780  1.000000  1.341000  1.080000  0.816000
    0.120   0.762360    0.845230    0.725810    0.472080  14.817000   5.899600   2.030290   1.285510  0.000000  1.195000  1.093000  0.998000
    0.140   0.752150    0.782960    0.745250    0.512780  14.817000   5.053530   2.281330   1.398080  0.000000  0.835000  0.948000  0.954000
    0.150   0.738190    0.794800    0.761030    0.534320  14.817000   5.204900   2.444130   1.443270  0.000000  0.781000  0.908000  0.942000
    0.160   0.719110    0.808610    0.768130    0.550220  14.817000   5.386940   2.580170   1.471770  0.000000  0.738000  0.862000  0.927000
    0.180   0.654080    0.843310    0.756900    0.572790  14.817000   5.871650   2.741610   1.546940  0.000000  0.684000  0.745000  0.927000
    0.200   0.583950    0.877700    0.717850    0.596740  14.817000   6.573910   2.825870   1.644010  0.000000  0.654000  0.623000  0.949000
    0.250   0.583950    0.937670    0.654700    0.611360  14.817000   8.500000   2.718930   1.790130  0.000000  0.683000  0.436000  0.970000
    0.300   0.583950    0.950000    0.696190    0.626380  14.817000  10.670300   2.417590   1.823450  0.000000  0.691000  0.400000  0.961000
    0.350   0.583950    1.000000    0.779070    0.630120  14.817000  10.670300   2.303750   1.790370  0.000000  0.800000  0.433000  0.948000
    0.400   0.583950    1.000000    0.827760    0.647730  14.817000  10.670300   2.236250   1.768440  0.000000  0.876000  0.460000  0.965000
    0.450   0.583950    1.000000    0.876450    0.641520  14.817000  10.670300   2.216780   1.675390  0.000000  0.966000  0.496000  0.958000
    0.500   0.583950    1.000000    0.925140    0.655820  14.817000  10.670300   2.243380   1.625390  0.000000  1.034000  0.529000  0.984000
    0.600   0.583950    1.000000    0.973830    0.686680  14.817000  10.670300   2.805350   1.524530  0.000000  1.206000  0.578000  1.055000
    0.700   0.583950    1.000000    1.022520    0.705600  14.817000  10.670300   6.658390   1.397240  0.000000  1.314000  0.578000  1.114000
    0.800   0.583950    1.000000    1.071220    0.714290  14.817000  10.670300  30.000000   1.320290  0.000000  1.357000  0.578000  1.175000
    0.900   0.583950    1.000000    1.119910    0.703880  14.817000  10.670300  30.000000   1.266370  0.000000  1.357000  0.578000  1.216000
    1.000   0.583950    1.000000    1.168600    0.678130  14.817000  10.670300  30.000000   1.226800  0.000000  1.357000  0.000000  1.230000
    1.250   0.583950    1.000000    1.217290    0.611190  14.817000  10.670300  30.000000   1.220650  0.000000  0.000000  0.000000  1.192000
    1.500   0.583950    1.000000    1.265980    0.547360  14.817000  10.670300  30.000000   1.318050  0.000000  0.000000  0.000000  0.942000
    2.000   0.583950    1.000000    1.314670    0.459440  14.817000  10.670300  30.000000   2.124850  0.000000  0.000000  0.000000  0.000000
    2.500   0.583950    1.000000    1.363360    0.408460  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    3.000   0.583950    1.000000    1.412050    0.364210  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    3.500   0.583950    1.000000    1.460750    0.329840  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    4.000   0.583950    1.000000    1.509440    0.309120  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    4.500   0.583950    1.000000    1.558130    0.292510  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    5.000   0.583950    1.000000    1.606820    0.547360  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    """)


class ZhaoEtAl2016AscSiteSigma(ZhaoEtAl2016Asc):
    """
    Adaption of the Zhao et al (2016a) GMPE for active shallow crust
    events for the case when within-event variability is dependent on site
    class
    """


class ZhaoEtAl2016UpperMantle(ZhaoEtAl2016Asc):
    """
    Adaptation of the Zhao et al. (2016a) GMPE for the upper mantle events
    """
    #: Supported tectonic region type is upper mantle
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.UPPER_MANTLE

    # For Upper Mantle
    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    imt    LnAmax1D1   LnAmax1D2   LnAmax1D3   LnAmax1D4     Src1D1     Src1D2     Src1D3     Src1D4      fsr1      fsr2      fsr3      fsr4
    pga     0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440  1.000000  1.000000  1.000000  1.000000
    0.005   0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440  1.000000  1.000000  1.000000  1.000000
    0.010   0.651810    0.706790    0.646240    0.404280   8.090000   1.882560   1.114440   0.836440  1.000000  1.000000  1.000000  1.000000
    0.020   0.653620    0.694650    0.638650    0.387890   6.992000   1.778610   1.124370   0.830000  1.000000  1.000000  1.000000  1.150000
    0.030   0.654670    0.687550    0.634210    0.378300   6.350000   1.717810   1.130170   0.826240  1.000000  1.000000  1.000000  0.800000
    0.040   0.652850    0.698920    0.606040    0.317370   4.883000   2.052340   1.150800   0.767580  1.000000  1.000000  1.000000  0.613000
    0.050   0.672640    0.701370    0.617160    0.309340   5.043000   2.387130   1.239710   0.786320  1.000000  1.000000  1.000000  0.542000
    0.060   0.699660    0.724450    0.637970    0.325300   6.271000   2.833990   1.348190   0.837750  1.000000  1.000000  1.000000  0.534000
    0.070   0.717130    0.743430    0.654370    0.354120   7.667000   3.294470   1.451810   0.926160  1.000000  1.000000  1.000000  0.583000
    0.080   0.716030    0.785980    0.680190    0.392820   9.034000   3.990910   1.583150   1.022280  1.000000  1.000000  0.830000  0.643000
    0.090   0.725610    0.797210    0.708890    0.421840  11.251000   4.465760   1.732920   1.118020  1.000000  1.000000  0.706000  0.674000
    0.100   0.742000    0.816680    0.718810    0.437360  14.817000   5.045610   1.841340   1.165780  1.000000  1.000000  0.800000  0.694000
    0.120   0.762360    0.845230    0.725810    0.472080  14.817000   5.899600   2.030290   1.285510  0.000000  1.000000  0.759000  0.763000
    0.140   0.752150    0.782960    0.745250    0.512780  14.817000   5.053530   2.281330   1.398080  0.000000  0.767000  0.715000  0.684000
    0.150   0.738190    0.794800    0.761030    0.534320  14.817000   5.204900   2.444130   1.443270  0.000000  0.708000  0.686000  0.645000
    0.160   0.719110    0.808610    0.768130    0.550220  14.817000   5.386940   2.580170   1.471770  0.000000  0.657000  0.644000  0.610000
    0.180   0.654080    0.843310    0.756900    0.572790  14.817000   5.871650   2.741610   1.546940  0.000000  0.568000  0.549000  0.532000
    0.200   0.583950    0.877700    0.717850    0.596740  14.817000   6.573910   2.825870   1.644010  0.000000  0.509000  0.434000  0.468000
    0.250   0.583950    0.937670    0.654700    0.611360  14.817000   8.500000   2.718930   1.790130  0.000000  0.433000  0.292000  0.291000
    0.300   0.583950    0.950000    0.696190    0.626380  14.817000  10.670300   2.417590   1.823450  0.000000  0.337000  0.275000  0.275000
    0.350   0.583950    1.000000    0.779070    0.630120  14.817000  10.670300   2.303750   1.790370  0.000000  0.337000  0.295000  0.295000
    0.400   0.583950    1.000000    0.827760    0.647730  14.817000  10.670300   2.236250   1.768440  0.000000  0.337000  0.293000  0.293000
    0.450   0.583950    1.000000    0.876450    0.641520  14.817000  10.670300   2.216780   1.675390  0.000000  0.000000  0.000000  0.000000
    0.500   0.583950    1.000000    0.925140    0.655820  14.817000  10.670300   2.243380   1.625390  0.000000  0.000000  0.000000  0.000000
    0.600   0.583950    1.000000    0.973830    0.686680  14.817000  10.670300   2.805350   1.524530  0.000000  0.000000  0.000000  0.000000
    0.700   0.583950    1.000000    1.022520    0.705600  14.817000  10.670300   6.658390   1.397240  0.000000  0.000000  0.000000  0.000000
    0.800   0.583950    1.000000    1.071220    0.714290  14.817000  10.670300  30.000000   1.320290  0.000000  0.000000  0.000000  0.000000
    0.900   0.583950    1.000000    1.119910    0.703880  14.817000  10.670300  30.000000   1.266370  0.000000  0.000000  0.000000  0.000000
    1.000   0.583950    1.000000    1.168600    0.678130  14.817000  10.670300  30.000000   1.226800  0.000000  0.000000  0.000000  0.000000
    1.250   0.583950    1.000000    1.217290    0.611190  14.817000  10.670300  30.000000   1.220650  0.000000  0.000000  0.000000  0.000000
    1.500   0.583950    1.000000    1.265980    0.547360  14.817000  10.670300  30.000000   1.318050  0.000000  0.000000  0.000000  0.000000
    2.000   0.583950    1.000000    1.314670    0.459440  14.817000  10.670300  30.000000   2.124850  0.000000  0.000000  0.000000  0.000000
    2.500   0.583950    1.000000    1.363360    0.408460  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    3.000   0.583950    1.000000    1.412050    0.364210  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    3.500   0.583950    1.000000    1.460750    0.329840  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    4.000   0.583950    1.000000    1.509440    0.309120  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    4.500   0.583950    1.000000    1.558130    0.292510  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    5.000   0.583950    1.000000    1.606820    0.547360  14.817000  10.670300  30.000000  14.381810  0.000000  0.000000  0.000000  0.000000
    """)


class ZhaoEtAl2016UpperMantleSiteSigma(ZhaoEtAl2016UpperMantle):
    """
    Adaption of the Zhao et al (2016a) GMPE for upper mantle events for the
    case when within-event variability is dependent on site class
    """


class ZhaoEtAl2016SInter(ZhaoEtAl2016Asc):
    """
    Implements the subduction interface GMPE of Zhao et al (2016b)

    Zhao, J. X., Liang, X., Jiang, F., Xing, H., Zhu, M., Hou, R., Zhang, Y.,
    Lan, X., Rhoades, D. A., Irikura, K., Fukushima, Y.,
    Somerville, P. (2016b), "Ground-Motion Prediction Equations for
    Subduction Interface Earthquakes in Japan Using Site Class and Simple
    Geometric Attenuation Functions", Bulletin of the Seismological
    Society of America, 106(4), 1518-1534

    Main version with standard deviations independent of site term
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required rupture parameters are magnitude and top-of-rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}

    # Coefficients table taken from spreadsheet supplied by the author
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt                  alpha   beta     cint    cintS   dint  gamma_ints     bint      gint             gintLD             gintLS     eintV     eintS   gammaint       S2                   S3        S4       S5                   S6       S7              lnSC1AM   sigma    tau    sigma_T  sc1_sigma_S  sc1_tau_S  sc1_sigma_ST  sc2_sigma_S  sc2_tau_T  sc2_sigma_ST  sc3_sigma_S  sc3_tau_S  sc3_sigma_ST  sc4_sigma_S  sc4_tau_S  sc4_sigma_ST
    pga    -5.3011890395444800  1.151  1.09973  1.31479  0.553    -3.89528  0.01999  -2.05587  0.545410000000000  1.133644136349760  -0.01123  -0.00628   -4.49858  0.31288  -0.0043099999999998   0.22838  0.31288  -0.0043099999999998  0.22838   0.3059054757248630   0.553  0.377      0.669        0.398      0.419         0.571        0.417      0.424         0.597        0.409      0.376         0.544        0.415      0.346         0.574
    0.005  -5.3011890395444800  1.151  1.09973  1.31479  0.553    -3.89528  0.01999  -2.05587  0.545410000000000  1.133644136349760  -0.01123  -0.00628   -4.49858  0.31288  -0.0043099999999998   0.22838  0.31288  -0.0043099999999998  0.22838   0.3059054757248630   0.553  0.377      0.669        0.398      0.419         0.571        0.417      0.424         0.597        0.409      0.376         0.544        0.415      0.346         0.574
    0.010  -5.2884351314221800  1.151  1.09848  1.31739  0.553    -3.89528  0.01999  -2.06565  0.549750000000000  1.133647532106160  -0.01125  -0.00625   -4.45894  0.30850  -0.0111500000000002   0.22305  0.30850  -0.0111500000000002  0.22305   0.2211189175034500   0.554  0.377      0.670        0.397      0.420         0.571        0.417      0.424         0.598        0.409      0.377         0.545        0.415      0.348         0.543
    0.020  -5.2756812232998800  1.151  1.09227  1.31919  0.553    -3.89528  0.01999  -2.10231  0.561715000000000  1.133645539711160  -0.01127  -0.00616   -4.25807  0.29297  -0.0216599999999998   0.20892  0.29297  -0.0216599999999998  0.20892   0.1391818272825550   0.553  0.384      0.673        0.395      0.425         0.574        0.417      0.425         0.598        0.408      0.376         0.544        0.416      0.352         0.544
    0.030  -5.2682206653106900  1.151  1.10690  1.34096  0.553    -3.89528  0.02066  -2.19232  0.578870000000000  1.133638051189290  -0.01158  -0.00572   -3.91800  0.22869  -0.1129091455512500   0.13314  0.22869  -0.0829091455512501  0.16314   0.0928148352701154   0.555  0.397      0.682        0.389      0.444         0.586        0.418      0.422         0.595        0.409      0.386         0.553        0.417      0.355         0.546
    0.040  -5.2629273151775800  1.151  1.11578  1.38051  0.553    -3.89528  0.02308  -2.24640  0.493330000000000  0.988105377906839  -0.01203  -0.00532   -3.11423  0.16316  -0.1887005077743300   0.06959  0.16316  -0.1887005077743300  0.05959   0.0626979621246270   0.565  0.428      0.709        0.387      0.474         0.611        0.420      0.434         0.604        0.413      0.393         0.557        0.420      0.362         0.555
    0.050  -5.2588214738333900  1.151  1.10234  1.43246  0.553    -3.89528  0.02709  -2.29341  0.491000000000000  0.904439734658832  -0.01256  -0.00503   -2.76035  0.12129  -0.2283118706921090   0.02845  0.12129  -0.2283118706921090  0.00845   0.0360112352938003   0.570  0.463      0.734        0.387      0.486         0.620        0.422      0.440         0.608        0.409      0.384         0.554        0.422      0.375         0.562
    0.060  -5.2554667571883900  1.151  1.08611  1.46238  0.553    -3.89528  0.02972  -2.31172  0.508475000000000  0.887664211721920  -0.01312  -0.00528   -2.64088  0.12345  -0.2192024788530120   0.00070  0.12345  -0.2192024788530120  0.00070   0.0372315296271544   0.583  0.488      0.760        0.397      0.500         0.632        0.416      0.449         0.614        0.401      0.379         0.550        0.423      0.388         0.571
    0.070  -5.2526303846795600  1.151  1.07291  1.47120  0.553    -3.89528  0.03207  -2.31101  0.527500000000000  0.904912893427476  -0.01359  -0.00569   -2.65622  0.13970  -0.1900877585085220  -0.00949  0.13970  -0.1900877585085220  0.00551   0.0491648511532895   0.602  0.501      0.784        0.403      0.531         0.658        0.412      0.466         0.628        0.394      0.377         0.558        0.420      0.410         0.587
    0.080  -5.2501734070552700  1.151  1.06383  1.46432  0.553    -3.89461  0.03196  -2.28778  0.545953146186990  0.942062229717542  -0.01382  -0.00619   -2.75266  0.16385  -0.1549929496094120  -0.00485  0.16385  -0.1549929496094120  0.01415   0.0983337731804003   0.614  0.501      0.793        0.413      0.553         0.681        0.412      0.489         0.647        0.389      0.374         0.552        0.423      0.416         0.591
    0.090  -5.2480061991992000  1.151  1.05863  1.44695  0.553    -3.90179  0.02972  -2.24680  0.563067703920420  0.986519531877540  -0.01393  -0.00673   -2.89920  0.20501  -0.1125034957053890   0.03047  0.20501  -0.1125034957053890  0.04047   0.1753764826899090   0.625  0.495      0.797        0.422      0.559         0.688        0.412      0.521         0.672        0.391      0.381         0.557        0.427      0.435         0.604
    0.100  -5.2460675657110900  1.151  1.05673  1.42323  0.553    -3.90765  0.02789  -2.20410  0.576153228856880  1.035532649999650  -0.01395  -0.00718   -3.07698  0.24449  -0.0750832172171707   0.06080  0.24449  -0.0750832172171707  0.07080   0.2447184227049870   0.637  0.478      0.796        0.429      0.562         0.693        0.418      0.540         0.687        0.394      0.409         0.574        0.426      0.469         0.632
    0.120  -5.2427128490660800  1.151  1.06051  1.36833  0.553    -3.91644  0.02470  -2.12011  0.592575859588849  1.135292002539040  -0.01381  -0.00793   -3.48283  0.32284   0.0150002886394358   0.14231  0.32284   0.0150002886394358  0.14031   0.3366973661131230   0.646  0.453      0.789        0.440      0.564         0.697        0.429      0.537         0.684        0.428      0.480         0.635        0.445      0.517         0.670
    0.140  -5.2398764765572600  1.151  1.07135  1.31558  0.553    -3.92273  0.02117  -2.04337  0.609834200714791  1.234237180364630  -0.01351  -0.00853   -3.91612  0.40120   0.0969875152845021   0.22696  0.40120   0.0969875152845021  0.20196   0.4219918629306410   0.654  0.412      0.773        0.441      0.556         0.692        0.435      0.560         0.712        0.433      0.440         0.599        0.442      0.507         0.670
    0.150  -5.2386070077219000  1.151  1.07856  1.29277  0.553    -3.92526  0.01951  -2.01088  0.619605756588544  1.281341268532020  -0.01333  -0.00879   -4.13481  0.43622   0.1458772263727260   0.25758  0.43622   0.1358772263727260  0.23258   0.4561999113437010   0.659  0.404      0.773        0.450      0.552         0.690        0.440      0.574         0.724        0.420      0.427         0.592        0.440      0.504         0.663
    0.160  -5.2374194989329700  1.151  1.08664  1.27319  0.553    -3.92753  0.01793  -1.98301  0.630846000686806  1.326585227368230  -0.01312  -0.00902   -4.35243  0.46736   0.1879291503650610   0.30748  0.46736   0.1729291503650610  0.26248   0.4857829542311720   0.663  0.398      0.774        0.452      0.548         0.688        0.444      0.573         0.726        0.424      0.429         0.589        0.437      0.496         0.661
    0.180  -5.2352522910768900  1.151  1.10470  1.24828  0.553    -3.93130  0.01505  -1.94607  0.661957417503245  1.411336369650280  -0.01269  -0.00927   -4.78030  0.51201   0.2515429577444550   0.35974  0.51201   0.2415429577444550  0.31974   0.5337861886971570   0.672  0.387      0.776        0.454      0.534         0.681        0.447      0.557         0.719        0.446      0.436         0.600        0.436      0.488         0.667
    0.200  -5.2333136575887900  1.151  1.12443  1.23715  0.553    -3.93446  0.01255  -1.92702  0.699775273836698  1.488543999616950  -0.01223  -0.00942   -5.19439  0.53926   0.3029826435245730   0.40313  0.53926   0.3029826435245730  0.37313   0.5700442187746950   0.678  0.382      0.778        0.462      0.528         0.679        0.450      0.532         0.710        0.441      0.437         0.602        0.432      0.481         0.663
    0.250  -5.2292078162446100  1.151  1.17689  1.22387  0.553    -3.94068  0.00769  -1.89876  0.784470723616457  1.652089063569910  -0.01108  -0.00959   -6.15803  0.58602   0.4269231521787280   0.50765  0.58602   0.4269231521787280  0.48765   0.6247924955873390   0.659  0.365      0.753        0.474      0.493         0.650        0.470      0.551         0.723        0.459      0.398         0.572        0.432      0.448         0.637
    0.300  -5.2258530995996000  1.151  1.22970  1.22846  0.553    -3.94547  0.00438  -1.89141  0.859387831257168  1.781266639239090  -0.00998  -0.00952   -7.02003  0.60465   0.5161970850888910   0.57779  0.60465   0.5161970850888910  0.57779   0.6505259707420690   0.640  0.348      0.729        0.472      0.471         0.632        0.475      0.509         0.695        0.437      0.421         0.579        0.432      0.442         0.623
    0.350  -5.2230167270907800  1.151  1.28058  1.24219  0.553    -3.94943  0.00215  -1.89299  0.923381083222217  1.884375114633360  -0.00898  -0.00933   -7.79153  0.60640   0.5695125616089470   0.63821  0.60640   0.5795125616089470  0.64821   0.6617360212939630   0.634  0.360      0.729        0.468      0.474         0.629        0.478      0.485         0.683        0.444      0.457         0.607        0.432      0.442         0.618
    0.400  -5.2205597494664900  1.151  1.32873  1.26077  0.553    -3.95273  0.00000  -1.89531  0.980106570565885  1.967625670226430  -0.00808  -0.00911   -8.49551  0.60277   0.6236634605365610   0.70323  0.60277   0.6336634605365610  0.71323   0.6649532313027650   0.627  0.354      0.720        0.457      0.449         0.610        0.484      0.496         0.683        0.453      0.463         0.607        0.416      0.435         0.607
    0.450  -5.2183925416104100  1.151  1.37394  1.28190  0.553    -3.95558  0.00000  -1.90578  1.022203929823320  2.035537053673680  -0.00727  -0.00888   -9.11351  0.58043   0.6581416274761160   0.75082  0.58043   0.6581416274761160  0.75082   0.6654266030879300   0.620  0.363      0.719        0.450      0.423         0.595        0.477      0.495         0.679        0.477      0.447         0.593        0.408      0.418         0.592
    0.500  -5.2164539081223000  1.151  1.41630  1.30432  0.553    -3.95795  0.00000  -1.91467  1.058737908474810  2.091423339372400  -0.00656  -0.00866   -9.68515  0.55692   0.6867116556863830   0.79378  0.55692   0.6867116556863830  0.79378   0.6635290829305090   0.612  0.364      0.712        0.445      0.415         0.583        0.470      0.473         0.658        0.472      0.435         0.579        0.409      0.432         0.603
    0.600  -5.2130991914773000  1.151  1.49310  1.35019  0.553    -3.96181  0.00000  -1.92743  1.118034334349720  2.176403198118720  -0.00534  -0.00824  -10.68946  0.50969   0.7122000042516460   0.84953  0.50969   0.7122000042516460  0.84953   0.6564608147533650   0.613  0.379      0.720        0.448      0.419         0.576        0.460      0.450         0.636        0.459      0.434         0.580        0.407      0.442         0.598
    0.700  -5.2102628189684700  1.151  1.56069  1.39523  0.560    -3.96483  0.00000  -1.93452  1.163018824473690  2.235996913698260  -0.00437  -0.00787  -11.54596  0.46501   0.7123896083711760   0.87979  0.46501   0.7123896083711760  0.87979   0.6475225398028140   0.625  0.393      0.739        0.440      0.429         0.583        0.460      0.454         0.634        0.461      0.448         0.591        0.403      0.454         0.613
    0.800  -5.2078058413441800  1.151  1.62055  1.43824  0.580    -3.96729  0.00000  -1.93739  1.197347867256100  2.278310911386920  -0.00359  -0.00755  -12.28722  0.42440   0.6993827558539090   0.89539  0.42440   0.6993827558539090  0.89539   0.6378151725112400   0.628  0.396      0.743        0.441      0.427         0.580        0.460      0.448         0.631        0.457      0.440         0.590        0.407      0.468         0.627
    0.900  -5.2056386334881000  1.151  1.67390  1.47881  0.602    -3.96962  0.00000  -1.93725  1.223616172806850  2.308465259401480  -0.00296  -0.00726  -12.93630  0.38841   0.6799630664371980   0.90256  0.38841   0.6799630664371980  0.90256   0.6275299463931780   0.628  0.397      0.743        0.435      0.433         0.586        0.456      0.446         0.622        0.449      0.445         0.593        0.408      0.485         0.633
    1.000  -5.2037000000000000  1.151  1.72171  1.51685  0.622    -3.97202  0.00000  -1.93505  1.243670000000000  2.329852618176160  -0.00244  -0.00700  -13.51000  0.35703   0.6582841883037910   0.90528  0.35703   0.6582841883037910  0.90528   0.6166948032035810   0.633  0.403      0.750        0.427      0.453         0.606        0.448      0.445         0.617        0.442      0.422         0.578        0.408      0.498         0.642
    1.250  -5.1995941586558200  1.151  1.82188  1.60148  0.667    -3.97949  0.00000  -1.92471  1.272450000000000  2.358529248389570  -0.00153  -0.00644  -14.69034  0.29673   0.6192828473123780   0.91793  0.29673   0.6192828473123780  0.91793   0.5871136982629510   0.636  0.404      0.753        0.413      0.457         0.613        0.442      0.457         0.624        0.428      0.428         0.587        0.412      0.507         0.657
    1.500  -5.1962394420108100  1.151  1.90081  1.67280  0.705    -3.99048  0.00000  -1.91189  1.285410000000000  2.366526445593360  -0.00097  -0.00597  -15.60298  0.25785   0.5828781633806380   0.92130  0.25785   0.5828781633806380  0.92130   0.5541350591719840   0.644  0.392      0.754        0.416      0.464         0.619        0.448      0.448         0.628        0.418      0.434         0.604        0.418      0.505         0.653
    2.000  -5.1909460918777000  1.151  2.01482  1.78372  0.768    -4.02652  0.00000  -1.88859  1.288300000000000  2.355357695068850  -0.00043  -0.00518  -16.90010  0.22262   0.5262044723719100   0.91709  0.22262   0.5262044723719100  0.91709   0.4823188293988830   0.635  0.382      0.741        0.409      0.464         0.623        0.437      0.458         0.633        0.406      0.470         0.625        0.413      0.524         0.665
    2.500  -5.1868402505335200  1.151  2.08892  1.86241  0.820    -4.08299  0.00000  -1.87252  1.277270000000000  2.331055616102490  -0.00023  -0.00451  -17.73658  0.21840   0.4871991042586300   0.90551  0.21840   0.4871991042586300  0.90551   0.4108485356913110   0.619  0.393      0.734        0.398      0.441         0.599        0.429      0.443         0.623        0.387      0.446         0.612        0.414      0.529         0.676
    3.000  -5.1834855338885100  1.151  2.13574  1.91711  0.863    -4.15939  0.00000  -1.86345  1.260490000000000  2.304087350833550  -0.00016  -0.00393  -18.27135  0.21595   0.4569807448342530   0.88668  0.21595   0.4569807448342530  0.88668   0.3476970039189440   0.599  0.385      0.712        0.390      0.412         0.572        0.423      0.441         0.623        0.369      0.400         0.565        0.412      0.524         0.668
    3.500  -5.1806491613796900  1.151  2.16254  1.95322  0.902    -4.25418  0.00000  -1.85969  1.241065000000000  2.277938604223720   0.00000  -0.00344  -18.59264  0.21595   0.4280893607115190   0.85880  0.21595   0.4280893607115190  0.85880   0.2981089167617070   0.581  0.376      0.692        0.386      0.394         0.553        0.410      0.424         0.608        0.376      0.353         0.536        0.402      0.535         0.672
    4.000  -5.1781921837553900  1.151  2.17393  1.97450  0.935    -4.36584  0.00000  -1.85953  1.220255000000000  2.253713119173820   0.00000  -0.00302  -18.75474  0.21595   0.3952406635315720   0.82025  0.21595   0.3952406635315720  0.82025   0.2652398018598770   0.568  0.377      0.682        0.377      0.376         0.541        0.410      0.409         0.603        0.362      0.365         0.540        0.394      0.542         0.671
    4.500  -5.1760249758993200  1.151  2.17301  1.98361  0.966    -4.49267  0.00000  -1.86151  1.198585000000000  2.231608900335380   0.00000  -0.00267  -18.79351  0.21595   0.3548841036361290   0.76990  0.21595   0.3548841036361290  0.76990   0.2508917433151500   0.551  0.376      0.667        0.360      0.363         0.528        0.412      0.393         0.591        0.368      0.349         0.519        0.385      0.530         0.652
    5.000  -5.1740863424112100  1.151  2.16199  1.98255  0.994    -4.63313  0.00000  -1.86451  1.176285000000000  2.211490595470470   0.00000  -0.00240  -18.73393  0.21595   0.3046830024209600   0.70705  0.21595   0.3046830024209600  0.70705   0.2365436847704230   0.563  0.374      0.675        0.361      0.346         0.525        0.447      0.408         0.615        0.381      0.293         0.476        0.380      0.514         0.633
    """)

    # Coefficients specific to the site amplification
    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    imt    LnAmax1D1   LnAmax1D2   LnAmax1D3   LnAmax1D4     Src1D1     Src1D2     Src1D3     Src1D4     fsr1    fsr2    fsr3    fsr4
    pga     0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440   1.0000  1.0000  1.1650  1.0000
    0.005   0.650220    0.709730    0.644340    0.404280   8.429000   1.913680   1.117140   0.836440   1.0000  1.0000  1.1650  1.0000
    0.010   0.651810    0.706790    0.646240    0.404280   8.090000   1.882560   1.114440   0.836440   1.0000  1.0000  0.9440  1.0000
    0.020   0.653620    0.694650    0.638650    0.387890   6.992000   1.778610   1.124370   0.830000   1.0000  1.0000  1.0120  1.0000
    0.030   0.654670    0.687550    0.634210    0.378300   6.350000   1.717810   1.130170   0.826240   1.0000  0.9990  1.1000  1.0000
    0.040   0.652850    0.698920    0.606040    0.317370   4.883000   2.052340   1.150800   0.767580   1.0000  0.8430  0.9590  0.5570
    0.050   0.672640    0.701370    0.617160    0.309340   5.043000   2.387130   1.239710   0.786320   1.0000  0.6630  0.8890  0.5430
    0.060   0.699660    0.724450    0.637970    0.325300   6.271000   2.833990   1.348190   0.837750   1.0000  0.8410  0.9460  0.5740
    0.070   0.717130    0.743430    0.654370    0.354120   7.667000   3.294470   1.451810   0.926160   1.0000  1.0290  1.0060  0.6480
    0.080   0.716030    0.785980    0.680190    0.392820   9.034000   3.990910   1.583150   1.022280   1.0000  1.2350  1.0650  0.7210
    0.090   0.725610    0.797210    0.708890    0.421840  11.251000   4.465760   1.732920   1.118020   1.0000  1.1440  1.0930  0.8090
    0.100   0.742000    0.816680    0.718810    0.437360  14.817000   5.045610   1.841340   1.165780   1.0000  1.0920  1.0770  1.0150
    0.120   0.762360    0.845230    0.725810    0.472080  14.817000   5.899600   2.030290   1.285510   0.0000  0.9450  1.0360  0.9720
    0.140   0.752150    0.782960    0.745250    0.512780  14.817000   5.053530   2.281330   1.398080   0.0000  0.6240  0.8950  0.9670
    0.150   0.738190    0.794800    0.761030    0.534320  14.817000   5.204900   2.444130   1.443270   0.0000  0.5770  0.8600  0.9630
    0.160   0.719110    0.808610    0.768130    0.550220  14.817000   5.386940   2.580170   1.471770   0.0000  0.5450  0.8220  0.9530
    0.180   0.654080    0.843310    0.756900    0.572790  14.817000   5.871650   2.741610   1.546940   0.0000  0.5270  0.7430  0.9670
    0.200   0.583950    0.877700    0.717850    0.596740  14.817000   6.573910   2.825870   1.644010   0.0000  0.5460  0.6630  1.0050
    0.250   0.583950    0.937670    0.654700    0.611360  14.817000   8.500000   2.718930   1.790130   0.0000  0.5960  0.4870  1.0450
    0.300   0.583950    0.950000    0.696190    0.626380  14.817000  10.670300   2.417590   1.823450   0.0000  0.6230  0.4470  1.0350
    0.350   0.583950    1.000000    0.779070    0.630120  14.817000  10.670300   2.303750   1.790370   0.0000  0.7010  0.4730  1.0080
    0.400   0.583950    1.000000    0.827760    0.647730  14.817000  10.670300   2.236250   1.768440   0.0000  0.7080  0.4870  1.0070
    0.450   0.583950    1.000000    0.876450    0.641520  14.817000  10.670300   2.216780   1.675390   0.0000  0.7370  0.5110  0.9810
    0.500   0.583950    1.000000    0.925140    0.655820  14.817000  10.670300   2.243380   1.625390   0.0000  0.7480  0.5360  0.9900
    0.600   0.583950    1.000000    0.973830    0.686680  14.817000  10.670300   2.805350   1.524530   0.0000  0.7280  0.5400  1.0160
    0.700   0.583950    1.000000    1.022520    0.705600  14.817000  10.670300   6.658390   1.397240   0.0000  0.6340  0.4770  1.0220
    0.800   0.583950    1.000000    1.071220    0.714290  14.817000  10.670300  30.000000   1.320290   0.0000  0.0000  0.0000  1.0230
    0.900   0.583950    1.000000    1.119910    0.703880  14.817000  10.670300  30.000000   1.266370   0.0000  0.0000  0.0000  0.9970
    1.000   0.583950    1.000000    1.168600    0.678130  14.817000  10.670300  30.000000   1.226800   0.0000  0.0000  0.0000  0.9480
    1.250   0.583950    1.000000    1.217290    0.611190  14.817000  10.670300  30.000000   1.220650   0.0000  0.0000  0.0000  0.8020
    1.500   0.583950    1.000000    1.265980    0.547360  14.817000  10.670300  30.000000   1.318050   0.0000  0.0000  0.0000  0.0000
    2.000   0.583950    1.000000    1.314670    0.459440  14.817000  10.670300  30.000000   2.124850   0.0000  0.0000  0.0000  0.0000
    2.500   0.583950    1.000000    1.363360    0.408460  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    3.000   0.583950    1.000000    1.412050    0.364210  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    3.500   0.583950    1.000000    1.460750    0.329840  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    4.000   0.583950    1.000000    1.509440    0.309120  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    4.500   0.583950    1.000000    1.558130    0.292510  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    5.000   0.583950    1.000000    1.606820    0.547360  14.817000  10.670300  30.000000  14.381810   0.0000  0.0000  0.0000  0.0000
    """)


class ZhaoEtAl2016SInterSiteSigma(ZhaoEtAl2016SInter):
    """
    Subclass of the Zhao et al. (2016b) subduction interface GMPE for the
    case of site-dependent within-event variability
    """


class ZhaoEtAl2016SSlab(ZhaoEtAl2016Asc):
    """
    Implements the subduction slab GMPE of Zhao et al (2016c)

    Zhao, J. X., Jiang, F., Shi, P., Xing, H., Huang, H., Hou, R.,
    Zhang, Y., Yu, P., Lan, X., Rhoades, D. A., Somerville, P. G., Irikura, K.,
    Fukushima, Y. (2016c), "Ground-Motion Prediction Equations for
    Subduction Slab Earthquakes in Japan Using Site Class and Simple
    Geometric Attenuation Functions", Bulletin of the Seismological
    Society of America, 106(4), 1535-1551

    Main version with standard deviations independent of site term
    """

    #: Supported tectonic region type is subduction inslab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Required rupture parameters are magnitude and top of rupture depth.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}

    # Set coeff tables
    COEFFS = COEFFS_SLAB
    COEFFS_SITE = COEFFS_SITE_SLAB


class ZhaoEtAl2016SSlabPErg(ZhaoEtAl2016Asc):
    """
    Implements the subduction in-slab GMPE of Zhao et al (2016c) with
    non-ergodic path correction for propagation through volcanic regions.

    Zhao, J. X., Jiang, F., Shi, P., Xing, H., Huang, H., Hou, R.,
    Zhang, Y., Yu, P., Lan, X., Rhoades, D. A., Somerville, P. G., Irikura, K.,
    Fukushima, Y. (2016c), "Ground-Motion Prediction Equations for
    Subduction Slab Earthquakes in Japan Using Site Class and Simple
    Geometric Attenuation Functions", Bulletin of the Seismological
    Society of America, 106(4), 1535-1551

    Main version with standard deviations independent of site term
    """
    experimental = True

    #: Supported tectonic region type is subduction inslab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    # Additional rupture parameters required for ray tracing
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_lat', 'hypo_lon', 'hypo_depth',
                                   'ztor', 'rake', 'strike', 'dip'}

    # Requires site coordinates for ray tracing
    REQUIRES_SITES_PARAMETERS = {'vs30', 'lon', 'lat'}

    #: Required distance measure is Rrup, Rvolc and clon, clat
    REQUIRES_DISTANCES = {'rrup', 'rvolc', 'clon', 'clat'}

    # Set coeff tables
    COEFFS = COEFFS_SLAB
    COEFFS_SITE = COEFFS_SITE_SLAB


class ZhaoEtAl2016SSlabSiteSigma(ZhaoEtAl2016SSlab):
    """
    Subclass of the Zhao et al. (2016c) subduction in-slab GMPE for the
    case of site-dependent within-event variability
    """
