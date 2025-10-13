# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Module exports class:`MorikawaFujiwara2013`
"""

import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA, JMA

CONSTS = {
    "D0": 300.,
    "e": 0.5,
    "Mw01": 8.2,
    "Mw1": 16.0}


def _get_basin_term(C, ctx, region=None):
    d0 = CONSTS["D0"]
    tmp = np.ones_like(ctx.z1pt4) * C['Dlmin']
    return C['pd'] * np.log10(np.maximum(tmp, ctx.z1pt4) / d0)


def _get_intensity_correction_term(C, region, xvf, focal_depth):
    if region == 'NE':
        gamma = C['gNE']
    elif region == 'SW':
        gamma = C['gEW']
    elif region is None:
        gamma = 0.
    else:
        raise ValueError('Unsupported region')
    return (gamma * np.minimum(xvf, 75.0) *
            np.maximum(focal_depth-30., 0.))


_get_magnitude_term = CallableDict()


@_get_magnitude_term.add(const.TRT.ACTIVE_SHALLOW_CRUST)
def _get_magnitude_term_1(trt, region, C, rrup, mw1prime, mw1, rhypo):
    return (C['a'] * (mw1prime - mw1)**2 + C['b1'] * rrup + C['c1'] -
            np.log10(rrup + C['d'] * 10.**(CONSTS['e'] * mw1prime)))


@_get_magnitude_term.add(const.TRT.SUBDUCTION_INTERFACE)
def _get_magnitude_term_2(trt, region, C, rrup, mw1prime, mw1, rhypo):
    return (C['a'] * (mw1prime - mw1)**2 + C['b2'] * rrup + C['c2'] -
            np.log10(rrup + C['d'] * 10.**(CONSTS['e']*mw1prime)))


@_get_magnitude_term.add(const.TRT.SUBDUCTION_INTRASLAB)
def _get_magnitude_term_3(trt, region, C, rrup, mw1prime, mw1, rhypo):
    tmp = (C['a'] * (mw1prime - mw1)**2 + C['b3'] * rrup + C['c3'] -
           np.log10(rrup + C['d'] * 10.**(CONSTS['e']*mw1prime)))
    if region == "SW":
        tmp[rhypo < 80] += C['PH']
    return tmp


def _get_shallow_amplification_term(C, vs30):
    tmp = np.ones_like(vs30) * C['Vsmax']
    return C['ps'] * np.log10(np.minimum(tmp, vs30)/C['V0'])


class MorikawaFujiwara2013Crustal(GMPE):
    """
    Implements the GMM from Morikawa and Fujiwara published as "A New Ground
    Motion Prediction Equation for Japan Applicable up to M9 Mega-Earthquake",
    Journal of Disaster Research, Vol.8, No.5, 2013.
    """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA, JMA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equation 2, pag 106.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters are:
    #: - Vs30 - time averaged shear-wave velocity [m/s]
    #: - z1p4 - Depth to the 1.4 km/s interface [m]
    #: - xvf - Distance from the volcanic front [km, positive in the forearc]
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt4', 'xvf'}

    #: Required rupture parameters are magnitude, and hypocentral depth [km].
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is Rrup [km]
    REQUIRES_DISTANCES = {'rrup'}

    region = None
    model = 'model1'

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        mw01 = CONSTS["Mw01"]
        mw1 = CONSTS["Mw1"]
        mw1prime = np.array(ctx.mag)
        mw1prime[ctx.mag >= mw01] = mw01
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            if self.model == 'model1':
                mag_term = _get_magnitude_term(
                    trt, self.region, C, ctx.rrup, mw1prime, mw1,
                    ctx.hypo_depth)
            else:
                msg = "Model not supported"
                raise ValueError(msg)

            mean[m] = (mag_term + _get_basin_term(C, ctx) +
                       _get_shallow_amplification_term(C, ctx.vs30) +
                       _get_intensity_correction_term(
                           C, self.region, ctx.xvf, ctx.hypo_depth))

            mean[m] = np.log(10**mean[m] / 980.665)
            sig[m] = C['sigma'] * np.log(10)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
  IMT       a        b1        b2        b3      c1      c2      c3         d        pd  Dlmin        ps   Vsmax   V0       gNE       gEW      PH   sigma
  jma -0.0321 -0.003736 -0.003320 -0.004195  6.9301  6.9042  7.2975  0.005078  0.032214  320.0 -0.756496  1200.0  350  0.000061  0.000059 -0.2284  0.3493
  pga -0.0321 -0.005315 -0.005042 -0.005605  7.0830  7.1181  7.5035  0.011641 -0.055358   15.0 -0.523212  1950.0  350  0.000076  0.000063 -0.2426  0.3761
  pgv -0.0325 -0.002654 -0.002408 -0.003451  5.6952  5.6026  6.0030  0.002266  0.129142  105.0 -0.693402   850.0  350  0.000047  0.000037 -0.2643  0.3399
 0.05 -0.0321 -0.005912 -0.005674 -0.006231  7.2151  7.2759  7.6801  0.012812 -0.071415   15.0 -0.368827  2000.0  350  0.000088  0.000066 -0.2414  0.3938
 0.06 -0.0321 -0.006097 -0.005864 -0.006405  7.2852  7.3523  7.7504  0.014508 -0.081796   15.0 -0.309232  2000.0  350  0.000087  0.000066 -0.2427  0.4039
 0.07 -0.0321 -0.006142 -0.005967 -0.006507  7.3397  7.4152  7.8127  0.015574 -0.089891   15.0 -0.247786  2000.0  350  0.000086  0.000066 -0.2439  0.4149
 0.08 -0.0323 -0.006104 -0.006033 -0.006594  7.4122  7.4929  7.8938  0.016465 -0.093581   15.0 -0.234067  2000.0  350  0.000085  0.000066 -0.2451  0.4219
 0.09 -0.0325 -0.006112 -0.006079 -0.006689  7.4817  7.5649  7.9649  0.017390 -0.089604   15.0 -0.252853  2000.0  350  0.000084  0.000066 -0.2461  0.4259
  0.1 -0.0327 -0.006116 -0.006061 -0.006686  7.5396  7.6214  8.0219  0.018438 -0.084855   15.0 -0.284416  2000.0  350  0.000084  0.000066 -0.2470  0.4266
 0.11 -0.0324 -0.005998 -0.005971 -0.006576  7.5072  7.5947  7.9960  0.017396 -0.076412   15.0 -0.305700  2000.0  350  0.000083  0.000066 -0.2479  0.4256
 0.12 -0.0322 -0.005896 -0.005878 -0.006448  7.4920  7.5837  7.9782  0.016457 -0.076948   15.0 -0.351975  2000.0  350  0.000083  0.000066 -0.2486  0.4243
 0.13 -0.0321 -0.005786 -0.005757 -0.006331  7.4788  7.5645  7.9644  0.015607 -0.072886   15.0 -0.395130  2000.0  350  0.000082  0.000066 -0.2494  0.4229
 0.15 -0.0321 -0.005564 -0.005579 -0.006078  7.4630  7.5471  7.9360  0.014118 -0.061401   15.0 -0.461774  2000.0  350  0.000082  0.000066 -0.2506  0.4193
 0.17 -0.0321 -0.005398 -0.005382 -0.005813  7.4557  7.5245  7.9097  0.012855 -0.051288   15.0 -0.536789  2000.0  350  0.000081  0.000066 -0.2516  0.4162
  0.2 -0.0321 -0.005151 -0.005027 -0.005476  7.4307  7.4788  7.8719  0.011273 -0.043392   15.0 -0.633661  2000.0  350  0.000080  0.000065 -0.2528  0.4152
 0.22 -0.0322 -0.005000 -0.004827 -0.005204  7.4139  7.4461  7.8311  0.010380 -0.035431   15.0 -0.665914  2000.0  350  0.000080  0.000065 -0.2535  0.4130
 0.25 -0.0321 -0.004836 -0.004519 -0.004907  7.3736  7.3728  7.7521  0.009225 -0.032667   15.0 -0.719524  2000.0  350  0.000079  0.000065 -0.2543  0.4089
  0.3 -0.0321 -0.004543 -0.004095 -0.004621  7.2924  7.2797  7.6656  0.007670 -0.019984   15.0 -0.793002  2000.0  350  0.000078  0.000065 -0.2553  0.4063
 0.35 -0.0321 -0.004379 -0.003717 -0.004305  7.2417  7.1832  7.5796  0.006448 -0.010959   15.0 -0.845946  2000.0  350  0.000077  0.000065 -0.2559  0.4043
  0.4 -0.0321 -0.004135 -0.003342 -0.003989  7.1785  7.0883  7.4889  0.005464  0.003891   15.0 -0.875246  2000.0  350  0.000076  0.000065 -0.2562  0.4029
 0.45 -0.0321 -0.003973 -0.003063 -0.003934  7.1202  7.0100  7.4287  0.004657  0.017120   15.0 -0.892051  1973.0  350  0.000073  0.000065 -0.2564  0.4033
  0.5 -0.0321 -0.003767 -0.002832 -0.003783  7.0604  6.9439  7.3615  0.003986  0.030246   15.0 -0.891130  1900.0  350  0.000071  0.000065 -0.2564  0.4019
  0.6 -0.0321 -0.003389 -0.002450 -0.003351  6.9357  6.8166  7.2161  0.002946  0.057955   15.0 -0.869468  1779.9  350  0.000066  0.000065 -0.2561  0.4032
  0.7 -0.0321 -0.002981 -0.002059 -0.002988  6.8272  6.6957  7.0854  0.002193  0.071145   15.0 -0.873924  1684.3  350  0.000062  0.000059 -0.2555  0.4038
  0.8 -0.0321 -0.002640 -0.001692 -0.002587  6.7325  6.5864  6.9659  0.001641  0.089675   15.0 -0.846494  1605.7  350  0.000059  0.000054 -0.2547  0.4053
  0.9 -0.0325 -0.002341 -0.001445 -0.002421  6.6845  6.5349  6.9211  0.001234  0.109109   15.0 -0.814706  1539.4  350  0.000056  0.000049 -0.2538  0.4085
    1 -0.0327 -0.002138 -0.001322 -0.002331  6.6284  6.4748  6.8605  0.000936  0.128832   15.0 -0.778652  1482.4  350  0.000053  0.000045 -0.2527  0.4091
  1.1 -0.0331 -0.001912 -0.001140 -0.002194  6.5971  6.4383  6.8304  0.000723  0.146198   15.3 -0.732989  1432.7  350  0.000051  0.000041 -0.2516  0.4074
  1.2 -0.0337 -0.001790 -0.001053 -0.002213  6.5912  6.4200  6.8224  0.000576  0.161540   17.1 -0.703167  1388.7  350  0.000049  0.000038 -0.2505  0.4061
  1.3 -0.0339 -0.001671 -0.000979 -0.002159  6.5588  6.3848  6.7827  0.000482  0.171349   19.0 -0.686586  1349.5  350  0.000047  0.000035 -0.2493  0.4046
  1.5 -0.0347 -0.001516 -0.000811 -0.002020  6.5419  6.3510  6.7540  0.000417  0.195287   23.0 -0.650103  1282.1  350  0.000043  0.000030 -0.2469  0.4035
  1.7 -0.0352 -0.001526 -0.000714 -0.001909  6.5209  6.3011  6.7004  0.000471  0.220718   27.2 -0.602410  1225.9  350  0.000040  0.000025 -0.2444  0.4007
    2 -0.0359 -0.001604 -0.000673 -0.001576  6.4982  6.2617  6.6087  0.000703  0.253945   33.7 -0.543585  1156.6  350  0.000036  0.000019 -0.2407  0.3927
  2.2 -0.0365 -0.001516 -0.000610 -0.001349  6.4920  6.2463  6.5766  0.000702  0.270206   38.3 -0.505691  1117.8  350  0.000033  0.000015 -0.2382  0.3883
  2.5 -0.0375 -0.001457 -0.000586 -0.001266  6.4964  6.2485  6.5667  0.000826  0.291435   45.4 -0.458523  1067.8  350  0.000030  0.000010 -0.2346  0.3831
    3 -0.0382 -0.001345 -0.000505 -0.001105  6.4414  6.1858  6.4858  0.001202  0.323118   57.8 -0.413921  1000.3  350  0.000025  0.000003 -0.2288  0.3775
  3.5 -0.0384 -0.001270 -0.000512 -0.001000  6.3464  6.0849  6.3681  0.001647  0.355950   70.9 -0.375806   946.6  350  0.000022 -0.000003 -0.2232  0.3713
    4 -0.0385 -0.001075 -0.000610 -0.001005  6.2459  6.0035  6.2727  0.002087  0.380773   84.7 -0.348309   902.4  350  0.000018 -0.000008 -0.2178  0.3646
  4.5 -0.0389 -0.000904 -0.000605 -0.001061  6.1868  5.9423  6.2145  0.002489  0.405714   99.0 -0.309662   865.1  350  0.000015 -0.000012 -0.2126  0.3603
    5 -0.0393 -0.000739 -0.000564 -0.001155  6.1466  5.8960  6.1817  0.002841  0.419676  113.8 -0.294664   833.1  350  0.000015 -0.000012 -0.2077  0.3552
  5.5 -0.0398 -0.000570 -0.000626 -0.001254  6.1084  5.8725  6.1566  0.003139  0.434776  129.2 -0.289487   805.2  350  0.000015 -0.000012 -0.2029  0.3494
    6 -0.0402 -0.000456 -0.000702 -0.001317  6.0920  5.8536  6.1257  0.003384  0.453344  145.0 -0.290399   780.5  350  0.000015 -0.000012 -0.1983  0.3428
  6.5 -0.0405 -0.000308 -0.000785 -0.001361  6.0636  5.8218  6.0778  0.003580  0.455404  155.0 -0.281808   758.4  350  0.000015 -0.000012 -0.1939  0.3366
    7 -0.0410 -0.000195 -0.000856 -0.001392  6.0586  5.8197  6.0652  0.003728  0.440951  155.0 -0.283250   738.5  350  0.000015 -0.000012 -0.1896  0.3300
  7.5 -0.0412 -0.000109 -0.000880 -0.001413  6.0367  5.7971  6.0388  0.003833  0.427237  155.0 -0.275643   720.5  350  0.000015 -0.000012 -0.1855  0.3242
    8 -0.0417 -0.000100 -0.000908 -0.001466  6.0378  5.7885  6.0381  0.003898  0.410255  155.0 -0.277723   704.1  350  0.000015 -0.000012 -0.1814  0.3185
  8.5 -0.0419 -0.000100 -0.000940 -0.001496  6.0238  5.7674  6.0180  0.003927  0.393707  155.0 -0.278975   688.9  350  0.000015 -0.000012 -0.1775  0.3130
    9 -0.0420 -0.000100 -0.001012 -0.001488  5.9972  5.7463  5.9881  0.003924  0.378643  155.0 -0.284384   675.0  350  0.000015 -0.000012 -0.1737  0.3090
  9.5 -0.0423 -0.000100 -0.001098 -0.001485  5.9880  5.7507  5.9807  0.003890  0.363717  155.0 -0.290498   662.0  350  0.000015 -0.000012 -0.1701  0.3047
   10 -0.0427 -0.000100 -0.001179 -0.001498  5.9820  5.7595  5.9869  0.003828  0.348396  155.0 -0.298398   650.0  350  0.000015 -0.000012 -0.1665  0.3007
""")


class MorikawaFujiwara2013SubInterface(MorikawaFujiwara2013Crustal):
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    region = None
    model = 'model1'


class MorikawaFujiwara2013SubInterfaceNE(MorikawaFujiwara2013SubInterface):
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    region = 'NE'
    model = 'model1'


class MorikawaFujiwara2013SubInterfaceSW(MorikawaFujiwara2013SubInterface):
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    region = 'SW'
    model = 'model1'


class MorikawaFujiwara2013SubSlab(MorikawaFujiwara2013Crustal):
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    region = None
    model = 'model1'


class MorikawaFujiwara2013SubSlabNE(MorikawaFujiwara2013SubSlab):
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    region = 'NE'
    model = 'model1'


class MorikawaFujiwara2013SubSlabSW(MorikawaFujiwara2013SubSlabNE):
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    region = 'SW'
    model = 'model1'
