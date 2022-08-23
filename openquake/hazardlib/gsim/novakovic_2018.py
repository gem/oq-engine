# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2022 GEM Foundation
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
Module exports :class:`NovakovicEtAl2018`
"""

import os
import pathlib
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.yenier_atkinson_2015 import (
    get_fs_SeyhanStewart2014)

TFP = pathlib.Path(__file__).parent.absolute()


def _magnitude_scaling(C, mag):
    """ Magnitude scaling as described in eq. 4 """
    fm = np.zeros_like(mag)
    dff = (mag - C['Mh'])
    idx = mag <= C['Mh']
    fm[idx] = C['e0'] + C['e1'] * dff[idx] + C['e2'] * dff[idx]**2
    idx = mag > C['Mh']
    fm[idx] = C['e0'] + C['e3'] * dff[idx]
    return fm


def _stress_param_scaling(C, d_sigma, mag):
    """ Stress scaling as defined in eq. 6 """
    fs = np.zeros_like(mag)
    idx = d_sigma <= 100
    fs[idx] = (C['s0'] + C['s1'] * mag[idx] + C['s2'] * mag[idx]**2 +
               C['s3'] * mag[idx]**3 + C['s4'] * mag[idx]**4)
    idx = d_sigma > 100
    fs[idx] = (C['s5'] + C['s6'] * mag[idx] + C['s7'] * mag[idx]**2 +
               C['s8'] * mag[idx]**3 + C['s9'] * mag[idx]**4)
    return fs*np.log(d_sigma/100)


def _source_scaling(C, d_sigma, mag, hypo_depth):
    """ Source scaling as per eq. 3 """
    if d_sigma is None:
        # Implements eq. 11 in Novokovic et al. 2018
        t1 = 0.097*(hypo_depth-10)
        t2 = 1.329*(mag-5.1)
        d_sigma = np.exp(5.65+np.minimum(0, t1)+np.minimum(0, t2))
    elif not hasattr(d_sigma, "__len__"):
        d_sigma = np.zeros_like(mag) * d_sigma
    return _magnitude_scaling(C, mag) + _stress_param_scaling(C, d_sigma, mag)


def _geometric_spreading(C, rrup, mag):

    # Effective depth
    heff = 10**(-0.405+0.235*mag)
    r = (rrup**2 + heff**2)**0.5
    rref = (1+heff**2)**0.5

    # Transition distances [km]. See right column page 5
    rt1 = 45
    rt2 = 200

    # Compute the spreading function
    fz = np.zeros_like(rrup)

    idx = r <= rt1
    fz[idx] = r[idx]**-1.3

    idx = (r > rt1) & (r <= rt2)
    fz[idx] = rt1**-1.3 * (r[idx]/rt1)**-0.05

    idx = (r > rt2)
    fz[idx] = rt1**-1.3 * (rt2/rt1)**-0.05 * (r[idx]/rt2)**-0.5

    return np.log(fz) + (C['b3'] + C['b4'] * mag) * np.log(r/rref)


def _anelastic_attenuation_term(gamma, rrup):
    """ Compute anelastic attenuation """
    return gamma * rrup


def get_gm_rock(C, ctx, d_sigma, REA):
    """ Compute ground-motion on bedrock """
    gamma = REA['gamma']
    calibration_factor = REA['C']
    gm = (_source_scaling(C, d_sigma, ctx.mag, ctx.hypo_depth) +
          _geometric_spreading(C, ctx.rrup, ctx.mag) +
          _anelastic_attenuation_term(gamma, ctx.rrup) +
          calibration_factor
          )
    return gm


class NovakovicEtAl2018(GMPE):
    """
    Implements the model of Novakovic et al. (2018) as described in:
        - Novakovic et al. (2018) "Empirically Calibrated Ground-Motion
          Prediction Equation for Oklahoma" - doi: 10.1785/0120170331
        - Novakovic et al. (2020) "Empirically Calibrated Ground-Motion
          Prediction Equation for Oklahoma" -

    Note that the default parameters used are for OK i.e. when the region_fle
    is left empty, the default file used is `novakovic_2018_reg_adj_ok.txt`

    :param d_sigma:
        The stress-drop [bar]
    :param region_fle:
        A .txt file (with the same formats of a coefficient table) containing
        the regional adjustements
    """

    #: This is ground-motion model for induced seismicity earthquakes by
    #: wastewater injection
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.INDUCED

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is geometric-mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total. This information must be provided in the regional adjustment
    #: file
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL,
                                            const.StdDev.INTER_EVENT,
                                            const.StdDev.INTRA_EVENT}

    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measures is Rrup
    REQUIRES_DISTANCES = {'rrup'}

    def __init__(self, d_sigma=None, region_fle=None, site_term=True,
                 **kwargs):
        super().__init__(d_sigma=d_sigma, region_fle=region_fle,
                         site_term=site_term, **kwargs)
        self.d_sigma = d_sigma
        self.site_term = site_term

        # Read the file and create the coefficient table for the regional
        # adjustment
        if region_fle is None:
            region_fle = os.path.join(TFP, 'novakovic_2018_reg_adj_ok.txt')
        with open(region_fle, 'r') as fle:
            data = fle.read()
            self.REA = CoeffsTable(sa_damping=5, table=data)

        # Boore et al. coefficients, used in the site model.
        self.BEA14 = BooreEtAl2014.COEFFS

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """ Compute mean """

        # Compute PGA on rock. This is used for computing the soil term.
        imt = PGA()
        C = self.COEFFS[imt]
        CR = self.REA[imt]
        pga_rock = np.exp(get_gm_rock(C, ctx, self.d_sigma, CR))

        # Compute ground-motion on soil.
        for m, imt in enumerate(imts):

            # Get the mean
            C = self.COEFFS[imt]
            CR = self.REA[imt]
            mean[m] = get_gm_rock(C, ctx, self.d_sigma, CR)

            # Site term
            if self.site_term:
                TMP = self.BEA14[imt]
                mean[m] += get_fs_SeyhanStewart2014(TMP, imt, pga_rock,
                                                    ctx.vs30)

            # Standard deviations
            tau[m] = np.ones_like(tau[m]) * CR['between_event']
            phi[m] = np.ones_like(tau[m]) * CR['within_event']
            sig[m] = (tau[m]**2 + phi[m]**2)**0.5

    COEFFS = CoeffsTable(sa_damping=5, table="""\
          IMT      Mh      e0      e1      e2      e3      b3      b4      s0      s1      s2      s3            s4      s5      s6      s7      s8      s9
          PGA    5.85  2.2156  0.6859 -0.1393  0.7656 -0.6187  0.0603 -2.1315   1.937  -0.504  0.0582    -0.0024982 -1.4442  1.2353 -0.2851  0.0302 -0.0012
          PGV     5.9  5.9604    1.03 -0.1651  1.0789 -0.5785  0.0574 -2.2458  1.9508 -0.5181  0.0614    -0.0027251 -1.7584  1.3793 -0.3256   0.035 -0.0014
 0.0199999996  5.9006  2.3793  0.6997 -0.1067  0.7489 -0.6376  0.0625 -1.1697  1.2816 -0.3364  0.0394 -0.0017102453 -1.2719  1.2532 -0.3167  0.0362 -0.0015
 0.0219635405  5.9431  2.4579   0.693 -0.1015  0.7457 -0.6346  0.0618 -1.3148  1.4061 -0.3734   0.044 -0.0019214568 -1.3553  1.3063  -0.327  0.0368 -0.0016
 0.0273298714  6.0306  2.6519  0.6779 -0.0941  0.7403 -0.6166  0.0587 -1.3383  1.4345 -0.3818   0.045 -0.0019621246 -1.8281  1.6476 -0.4136  0.0462 -0.0019
  0.032959789  6.0191  2.7818  0.6747 -0.0967  0.7387  -0.585  0.0537  -0.991  1.1522 -0.2983  0.0344 -0.0014775553 -2.5924  2.2044 -0.5609  0.0632 -0.0026
 0.0423190892  5.6497  2.6877   0.707  -0.123  0.7426 -0.5387  0.0468 -0.8906  1.0319 -0.2551  0.0283 -0.0011791884 -3.5399  2.8211 -0.7093  0.0789 -0.0033
 0.0494804569  5.3764  2.5728  0.7181 -0.1604  0.7536 -0.5115   0.043 -0.9678  0.9945 -0.2209  0.0217 -0.0007889064 -4.1732  3.2534 -0.8208  0.0917 -0.0038
 0.0655307993   5.625   2.889  0.7003 -0.1696  0.7602 -0.4634  0.0361 -2.3368  2.0173 -0.5053  0.0563 -0.0023391122 -3.8552  2.8013 -0.6513  0.0673 -0.0026
 0.0815660655  5.2451   2.612  0.7566 -0.2428  0.7864 -0.4174  0.0302 -3.6821  2.9469 -0.7444  0.0832 -0.0034585228 -3.0859  2.1292 -0.4532  0.0429 -0.0015
  0.098328419  5.4332  2.7636  0.7155 -0.2604  0.7935 -0.3807  0.0252 -4.0209  3.0878  -0.761  0.0833 -0.0033984683 -2.5045  1.6147 -0.3024  0.0246 -0.0007
 0.1262626201  5.3609  2.6555  0.7327 -0.3243  0.8098 -0.3575  0.0225  -4.157    3.09  -0.745  0.0801 -0.0032210921 -1.4994  0.7291  -0.042 -0.0072  0.0007
 0.1569858789  5.2587  2.4809  0.8026 -0.3823  0.8382 -0.3289  0.0194 -3.9816  2.8425 -0.6577  0.0683 -0.0026638928 -0.3022 -0.2533  0.2336 -0.0398  0.0021
    0.1953125  5.4307  2.5414   0.818 -0.3859  0.8423 -0.2908  0.0143 -2.8318  1.8381 -0.3622  0.0321 -0.0010772438  0.7143 -1.0055  0.4204 -0.0591  0.0028
 0.2512562871  5.6059  2.5206  0.8664 -0.3771  0.8783 -0.2423  0.0091  -1.733  0.9565 -0.1244  0.0052  0.0000218818  1.7886 -1.7704  0.6066 -0.0782  0.0035
 0.3030303121  5.8482  2.6187  0.8513 -0.3634  0.8798 -0.2146  0.0059 -0.2401 -0.1858  0.1799 -0.0293  0.0014404841  2.1854 -1.9496  0.6164  -0.075  0.0032
 0.3322259188  5.9569  2.6486  0.8482 -0.3573  0.8836 -0.2049  0.0051  0.5148 -0.7513  0.3278 -0.0457  0.0021057417  2.3083 -1.9797  0.6052 -0.0716   0.003
  0.375939846  6.0872  2.6658  0.8495 -0.3503  0.8924 -0.1966  0.0049  1.5292 -1.4975  0.5194 -0.0666  0.0029394061   2.385 -1.9513  0.5719 -0.0649  0.0026
 0.4694835544  6.2216  2.5819  0.8752  -0.348  0.9119 -0.2037  0.0075  3.3782   -2.86  0.8753 -0.1067  0.0045977338  1.3014 -0.8769  0.2053  -0.014  0.0001
          0.5  6.2509  2.5469  0.8848 -0.3483  0.9178 -0.2078  0.0085  3.9137 -3.2548  0.9791 -0.1185  0.0050909007  0.8735 -0.4705  0.0707  0.0044 -0.0008
 0.5847952962  6.4552  2.5866  0.8799 -0.3295  0.9223 -0.2195  0.0116  3.7737  -3.015   0.874 -0.1018  0.0042109804 -0.0375  0.3569 -0.1908  0.0384 -0.0024
 0.7246376872  6.7311  2.6414  0.8936 -0.3015  0.9068 -0.2413  0.0166  2.9309 -2.1566  0.5764   -0.06  0.0021569513 -1.4537  1.5845 -0.5622  0.0848 -0.0044
 0.9009009004  6.6235  2.2857  1.1469 -0.2652  0.9442  -0.277  0.0238  1.6778 -1.0035  0.2079 -0.0115 -0.0000997096 -3.4097  3.1906 -1.0274  0.1412 -0.0068
 0.9900990129  6.4642  2.0102  1.3242 -0.2472  0.9798 -0.2957  0.0273   1.116 -0.5002  0.0514  0.0085 -0.0010035093 -4.3861  3.9802 -1.2537  0.1685  -0.008
 1.1235954762  6.5833  1.9969  1.3605 -0.2279  0.9907 -0.3209  0.0321 -0.5218  0.8676 -0.3544  0.0593 -0.0032785707 -4.9268  4.3684 -1.3471  0.1772 -0.0083
 1.3888888359    6.73  1.8972  1.4604 -0.1919  1.0225 -0.3618  0.0399 -3.4682  3.2873 -1.0605  0.1461 -0.0071120951 -5.5938  4.8102  -1.439  0.1833 -0.0083
 1.7543859482    6.71  1.5588  1.6329 -0.1544   1.108 -0.4042  0.0478 -5.7412  5.0899 -1.5655  0.2054 -0.0095954046 -5.9214  4.9748 -1.4514  0.1799 -0.0079
 1.9607843161  6.6563  1.2828  1.7362  -0.134  1.1836 -0.4321   0.053 -6.5491   5.697 -1.7236  0.2222 -0.0102122375 -6.0007   4.984 -1.4353  0.1753 -0.0076
 2.7027027607   6.695  0.7877   1.852 -0.1018  1.3351 -0.4919  0.0638 -7.9988  6.7253 -1.9714  0.2457 -0.0109460534 -4.5705  3.6687 -1.0001  0.1144 -0.0046
 3.3333332539  6.7271  0.4494  1.9171  -0.084  1.4521 -0.5278  0.0702 -7.6498  6.3092 -1.8048  0.2188 -0.0094611053 -3.5814  2.7948 -0.7224  0.0771 -0.0028
 4.1666669846  6.8479  0.2606   1.941 -0.0723  1.5209 -0.5568  0.0751 -6.9827  5.6453 -1.5705  0.1843 -0.0076800415 -2.3926  1.7661 -0.4021  0.0348 -0.0008
 5.2631578445  6.8927 -0.0689  1.9793  -0.061  1.5919 -0.5823  0.0793 -6.1625  4.8839 -1.3179   0.149 -0.0059499122 -1.2368  0.7939 -0.1084 -0.0028  0.0009
""")
