# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module exports :class:`ChiouYoungs2014`.
"""
from __future__ import division

import numpy as np
import math

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class ChiouYoungs2014(GMPE):
    """
    Implements GMPE developed by Brian S.-J. Chiou and Robert R. Youngs
    and published as "Updated of the Chiou and Youngs NGA Model for the
    Average Horizontal Component of Peak Ground Motion and Response Spectra"
    (2014, Earthquake Spectra).
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see chapter "Variance model".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters are Vs30, Vs30 measured flag
    #: and Z1.0.
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'vs30measured', 'z1pt0'))

    #: Required rupture parameters are magnitude, rake,
    #: dip and ztor.
    REQUIRES_RUPTURE_PARAMETERS = set(('dip', 'rake', 'mag', 'ztor'))

    #: Required distance measures are RRup, Rjb and Rx.
    REQUIRES_DISTANCES = set(('rrup', 'rjb', 'rx'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        # intensity on a reference soil is used for both mean
        # and stddev calculations.
        ln_y_ref = self._get_ln_y_ref(rup, dists, C)
        # exp1 and exp2 are parts of eq. 12 and eq. 13,
        # calculate it once for both.
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))
        mean = self._get_mean(sites, C, ln_y_ref, exp1, exp2)
        stddevs = self._get_stddevs(sites, rup, C, stddev_types,
                                    ln_y_ref, exp1, exp2)

        return mean, stddevs

    def _get_mean(self, sites, C, ln_y_ref, exp1, exp2):
        """
        Add site effects to an intensity.

        Implements eq. 13b.
        """
        # we do not support estimating of basin depth and instead
        # rely on it being available (since we require it).
        # centered_z1pt0
        centered_z1pt0 = self._get_centered_z1pt0(sites)
        # we consider random variables being zero since we want
        # to find the exact mean value.
        eta = epsilon = 0.

        ln_y = (
            # first line of eq. 12
            ln_y_ref + eta
            # second line
            + C['phi1'] * np.log(sites.vs30 / 1130).clip(-np.inf, 0)
            # third line
            + C['phi2'] * (exp1 - exp2)
            * np.log((np.exp(ln_y_ref) * np.exp(eta) + C['phi4']) / C['phi4'])
            # fourth line
            + C['phi5']
            * (1.0 - np.exp(-1. * centered_z1pt0 / C['phi6']))
            # fifth line
            + epsilon
        )

        return ln_y

    def _get_stddevs(self, sites, rup, C, stddev_types, ln_y_ref, exp1, exp2):
        """
        Get standard deviation for a given intensity on reference soil.

        Implements equations 13 for inter-event, intra-event
        and total standard deviations.
        """
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 13 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 6.5) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 1.5 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 13
        NL = b * y_ref / (y_ref + c)
        sigma = ((C['sig1'] + (C['sig2'] - C['sig1']) * mag_test / 1.5)
                 * np.sqrt((C['sig3'] * Finferred + 0.7 * Fmeasured) +
                           (1. + NL) ** 2.))

        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 13
                ret += [np.sqrt(((1 + NL) ** 2) * (tau ** 2) + (sigma ** 2))]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                ret.append(sigma)
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                ret.append(np.abs((1 + NL) * tau))
        return ret

    def _get_ln_y_ref(self, rup, dists, C):
        """
        Get an intensity on a reference soil.

        Implements eq. 13a.
        """
        # reverse faulting flag
        Frv = 1. if 30 <= rup.rake <= 150 else 0.
        # normal faulting flag
        Fnm = 1. if -120 <= rup.rake <= -60 else 0.
        # hanging wall flag

        Fhw = np.zeros_like(dists.rx)
        idx = np.nonzero(dists.rx >= 0.)
        Fhw[idx] = 1.

        # a part in eq. 11
        mag_test1 = np.cosh(2. * max(rup.mag - 4.5, 0))

        # centered DPP
        centered_dpp = self._get_centered_cdpp(dists)
        # centered_ztor
        centered_ztor = self._get_centered_ztor(rup, Frv)
        #
        dist_taper = np.fmax(1 - (np.fmax(dists.rrup - 40,
                                  np.zeros_like(dists)) / 30.),
                             np.zeros_like(dists))
        dist_taper = dist_taper.astype(np.float64)
        ln_y_ref = (
            # first part of eq. 11
            C['c1']
            + (C['c1a'] + C['c1c'] / mag_test1) * Frv
            + (C['c1b'] + C['c1d'] / mag_test1) * Fnm
            + (C['c7'] + C['c7b'] / mag_test1) * centered_ztor
            + (C['c11'] + C['c11b'] / mag_test1) *
            np.cos(math.radians(rup.dip)) ** 2
            # second part
            + C['c2'] * (rup.mag - 6)
            + ((C['c2'] - C['c3']) / C['cn'])
            * np.log(1 + np.exp(C['cn'] * (C['cm'] - rup.mag)))
            # third part
            + C['c4']
            * np.log(dists.rrup + C['c5']
                     * np.cosh(C['c6'] * max(rup.mag - C['chm'], 0)))
            + (C['c4a'] - C['c4'])
            * np.log(np.sqrt(dists.rrup ** 2 + C['crb'] ** 2))
            # forth part
            + (C['cg1'] + C['cg2'] / (np.cosh(max(rup.mag - C['cg3'], 0))))
            * dists.rrup
            # fifth part
            + C['c8'] * dist_taper
            * min(max(rup.mag - 5.5, 0) / 0.8, 1.0)
            * np.exp(-1 * C['c8a'] * (rup.mag - C['c8b']) ** 2) * centered_dpp
            # sixth part
            + C['c9'] * Fhw * np.cos(math.radians(rup.dip)) *
            (C['c9a'] + (1 - C['c9a']) * np.tanh(dists.rx / C['c9b']))
            * (1 - np.sqrt(dists.rjb ** 2 + rup.ztor ** 2)
               / (dists.rrup + 1.0))
        )

        return ln_y_ref

    def _get_centered_z1pt0(self, sites):
        """
        Get z1pt0 centered on the Vs30- dependent avarage z1pt0(m)
        California and non-Japan regions

        """
        #: California and non-Japan regions

        mean_z1pt0 = (-7.15 / 4.) * np.log(((sites.vs30) ** 4. + 570.94 ** 4.)
                                           / (1360 ** 4. + 570.94 ** 4.))
        centered_z1pt0 = sites.z1pt0 - np.exp(mean_z1pt0)

        return centered_z1pt0

    def _get_centered_ztor(self, rup, Frv):
        """
        Get ztor centered on the M- dependent avarage ztor(km)
        by different fault types.
        """
        if Frv == 1:

            mean_ztor = max(2.704 - 1.226 * max(rup.mag - 5.849, 0.0), 0.) ** 2
            centered_ztor = rup.ztor - mean_ztor
        else:

            mean_ztor = max(2.673 - 1.136 * max(rup.mag - 4.970, 0.0), 0.) ** 2
            centered_ztor = rup.ztor - mean_ztor

        return centered_ztor

    def _get_centered_cdpp(self, dists):
        """
        Get directivity prediction parameter centered on the avgerage
        directivity prediction parameter. Here we set the centered_dpp
        equals to zero, since the near fault directivity effect prediction is
        off in our calculation.

        """
        centered_dpp = 0.

        return centered_dpp

    #: Coefficient tables are constructed from values in tables 1 - 5

    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT     c1      c1a     c1b     c1c     c1d     cn      cm    c2      c3    c4     c4a  crb   c5      chm     c6      c7      c7b     c8     c8a    c8b       c9     c9a    c9b     c11      c11b        cg1        cg2       cg3     phi1       phi2      phi3     phi4     phi5   phi6  gjpit  gwn      phi1jp  phi5jp   phi6jp     tau1    tau2    sig1    sig2    sig3    sig2jp
pga   -1.5065  0.165  -0.255  -0.165  0.255  16.0875  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0956  0.4908  0.0352   0.0462  0.     0.2695  0.4833  0.9228  0.1202  6.8607  0.      -0.4536    -0.007146  -0.006758  4.2542  -0.521   -0.1417   -0.00701   0.102151  0.     300  1.5817  0.7594  -0.6846  0.459    800.        0.4     0.26    0.4912  0.3762  0.8     0.4528
pgv    2.3549  0.165  -0.0626 -0.165  0.0626  3.3024  5.423   1.06  2.3152  -2.1  -0.5  50  5.8096  3.0514  0.4407  0.0324   0.0097  0.2154 0.2695  5.      0.3079  0.1     6.5     0       -0.3834    -0.001852  -0.007403  4.3439  -0.7936  -0.0699   -0.008444  5.41      0.0202 300. 2.2306  0.335   -0.7966  0.9488   800.        0.3894  0.2578  0.4785  0.3629  0.7504  0.3918
0.01  -1.5065  0.165  -0.255  -0.165  0.255  16.0875  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0956  0.4908  0.0352   0.0462  0.     0.2695  0.4833  0.9228  0.1202  6.8607  0.      -0.4536    -0.007146  -0.006758  4.2542  -0.521   -0.1417   -0.00701   0.102151  0.     300  1.5817  0.7594  -0.6846  0.459    800.        0.4     0.26    0.4912  0.3762  0.8     0.4528
0.02  -1.4798  0.165  -0.255  -0.165  0.255  15.7118  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0963  0.4925  0.0352   0.0472  0.     0.2695  1.2144  0.9296  0.1217  6.8697  0.      -0.4536    -0.007249  -0.006758  4.2386  -0.5055  -0.1364   -0.007279  0.10836   0.     300  1.574   0.7606  -0.6681  0.458    800.        0.4026  0.2637  0.4904  0.3762  0.8     0.4551
0.03  -1.2972  0.165  -0.255  -0.165  0.255  15.8819  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0974  0.4992  0.0352   0.0533  0.     0.2695  1.6421  0.9396  0.1194  6.9113  0.      -0.4536    -0.007869  -0.006758  4.2519  -0.4368  -0.1403   -0.007354  0.119888  0.     300  1.5544  0.7642  -0.6314  0.462    800.        0.4063  0.2689  0.4988  0.3849  0.8     0.4571
0.04  -1.1007  0.165  -0.255  -0.165  0.255  16.4556  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0988  0.5037  0.0352   0.0596  0.     0.2695  1.9456  0.9661  0.1166  7.0271  0.      -0.4536    -0.008316  -0.006758  4.296   -0.3752  -0.1591   -0.006977  0.133641  0.     300  1.5502  0.7676  -0.5855  0.453    800.        0.4095  0.2736  0.5049  0.391   0.8     0.4642
0.05  -0.9292  0.165  -0.255  -0.165  0.255  17.6453  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.1011  0.5048  0.0352   0.0639  0.     0.2695  2.181   0.9794  0.1176  7.0959  0.      -0.4536    -0.008743  -0.006758  4.3578  -0.3469  -0.1862   -0.006467  0.148927  0.     300  1.5391  0.7739  -0.5457  0.436    800.        0.4124  0.2777  0.5096  0.3957  0.8     0.4716
0.075 -0.658   0.165  -0.254  -0.165  0.254  20.1772  5.0031  1.06  1.9636  -2.1  -0.5  50  6.4551  3.1094  0.5048  0.0352   0.063   0.     0.2695  2.6087  1.026   0.1171  7.3298  0.      -0.4536    -0.009537  -0.00619   4.5455  -0.3747  -0.2538   -0.005734  0.190596  0.     300  1.4804  0.7956  -0.4685  0.383    800.        0.4179  0.2855  0.5179  0.4043  0.8     0.5022
0.1   -0.5613  0.165  -0.253  -0.165  0.253  19.9992  5.0172  1.06  1.9636  -2.1  -0.5  50  6.8305  3.2381  0.5048  0.0352   0.0532  0.     0.2695  2.9122  1.0177  0.1146  7.2588  0.      -0.4536    -0.00983   -0.005332  4.7603  -0.444   -0.2943   -0.005604  0.230662  0.     300  1.4094  0.7932  -0.4985  0.375    800.        0.4219  0.2913  0.5236  0.4104  0.8     0.523
0.12  -0.5342  0.165  -0.252  -0.165  0.252  18.7106  5.0315  1.06  1.9795  -2.1  -0.5  50  7.1333  3.3407  0.5048  0.0352   0.0452  0.     0.2695  3.1045  1.0008  0.1128  7.2372  0.      -0.4536    -0.009913  -0.004732  4.8963  -0.4895  -0.3077   -0.005696  0.253169  0.     300  1.3682  0.7768  -0.5603  0.377    800.        0.4244  0.2949  0.527   0.4143  0.8     0.5278
0.15  -0.5462  0.165  -0.25   -0.165  0.25   16.6246  5.0547  1.06  2.0362  -2.1  -0.5  50  7.3621  3.43    0.5045  0.0352   0.0345  0.     0.2695  3.3399  0.9801  0.1106  7.2109  0.      -0.4536    -0.009896  -0.003806  5.0644  -0.5477  -0.3113   -0.005845  0.266468  0.     300  1.3241  0.7437  -0.6451  0.379    800.        0.4275  0.2993  0.5308  0.4191  0.8     0.5304
0.17  -0.5858  0.165  -0.248  -0.165  0.248  15.3709  5.0704  1.06  2.0823  -2.1  -0.5  50  7.4365  3.4688  0.5036  0.0352   0.0283  0.     0.2695  3.4719  0.9652  0.115   7.2491  0.      -0.4536    -0.009787  -0.00328   5.1371  -0.5922  -0.3062   -0.005959  0.26506   0.     300  1.3071  0.7219  -0.6981  0.38     800.        0.4292  0.3017  0.5328  0.4217  0.8     0.531
0.2   -0.6798  0.165  -0.2449 -0.165  0.2449 13.7012  5.0939  1.06  2.1521  -2.1  -0.5  50  7.4972  3.5146  0.5016  0.0352   0.0202  0.     0.2695  3.6434  0.9459  0.1208  7.2988  0.      -0.444     -0.009505  -0.00269   5.188   -0.6693  -0.2927   -0.006141  0.255253  0.     300  1.2931  0.6922  -0.7653  0.384    800.        0.4313  0.3047  0.5351  0.4252  0.8     0.5312
0.25  -0.8663  0.165  -0.2382 -0.165  0.2382 11.2667  5.1315  1.06  2.2574  -2.1  -0.5  50  7.5416  3.5746  0.4971  0.0352   0.009   0.     0.2695  3.8787  0.9196  0.1208  7.3691  0.      -0.3539    -0.008918  -0.002128  5.2164  -0.7766  -0.2662   -0.006439  0.231541  0.     300  1.315   0.6579  -0.8469  0.393    800.        0.4341  0.3087  0.5377  0.4299  0.7999  0.5309
0.3   -1.0514  0.165  -0.2313 -0.165  0.2313  9.1908  5.167   1.06  2.344   -2.1  -0.5  50  7.56    3.6232  0.4919  0.0352  -0.0004  0.     0.2695  4.0711  0.8829  0.1175  6.8789  0.      -0.2688    -0.008251  -0.001812  5.1954  -0.8501  -0.2405   -0.006704  0.207277  0.001  300  1.3514  0.6362  -0.8999  0.408    800.        0.4363  0.3119  0.5395  0.4338  0.7997  0.5307
0.4   -1.3794  0.165  -0.2146 -0.165  0.2146  6.5459  5.2317  1.06  2.4709  -2.1  -0.5  50  7.5735  3.6945  0.4807  0.0352  -0.0155  0.     0.2695  4.3745  0.8302  0.106   6.5334  0.      -0.1793    -0.007267  -0.001274  5.0899  -0.9431  -0.1975   -0.007125  0.165464  0.004  300  1.4051  0.6049  -0.9618  0.462    800.        0.4396  0.3165  0.5422  0.4399  0.7988  0.531
0.5   -1.6508  0.165  -0.1972 -0.165  0.1972  5.2305  5.2893  1.06  2.5567  -2.1  -0.5  50  7.5778  3.7401  0.4707  0.0352  -0.0278  0.0991 0.2695  4.6099  0.7884  0.1061  6.526   0.      -0.1428    -0.006492  -0.001074  4.7854  -1.0044  -0.1633   -0.007435  0.133828  0.01   300  1.4402  0.5507  -0.9945  0.524    800.        0.4419  0.3199  0.5433  0.4446  0.7966  0.5313
0.75  -2.1511  0.165  -0.162  -0.165  0.162   3.7896  5.4109  1.06  2.6812  -2.1  -0.5  50  7.5808  3.7941  0.4575  0.0352  -0.0477  0.1982 0.2695  5.0376  0.6754  0.1     6.5     0.      -0.1138    -0.005147  -0.001115  4.3304  -1.0602  -0.1028   -0.00812   0.085153  0.034  300  1.528   0.3582  -1.0225  0.658    800.        0.4459  0.3255  0.5294  0.4533  0.7792  0.5309
1     -2.5365  0.165  -0.14   -0.165  0.14    3.3024  5.5106  1.06  2.7474  -2.1  -0.5  50  7.5814  3.8144  0.4522  0.0352  -0.0559  0.2154 0.2695  5.3411  0.6196  0.1     6.5     0.      -0.1062    -0.004277  -0.001197  4.1667  -1.0941  -0.0699   -0.008444  0.058595  0.067  300  1.6523  0.2003  -1.0002  0.78     800.        0.4484  0.3291  0.5105  0.4594  0.7504  0.5302
1.5   -3.0686  0.165  -0.1184 -0.165  0.1184  2.8498  5.6705  1.06  2.8161  -2.1  -0.5  50  7.5817  3.8284  0.4501  0.0352  -0.063   0.2154 0.2695  5.7688  0.5101  0.1     6.5     0.      -0.102     -0.002979  -0.001675  4.0029  -1.1142  -0.0425   -0.007707  0.031787  0.143  300  1.8872  0.0356  -0.9245  0.96     800.        0.4515  0.3335  0.4783  0.468   0.7136  0.5276
2     -3.4148  0.1645 -0.11   -0.1645 0.11    2.5417  5.7981  1.06  2.8514  -2.1  -0.5  50  7.5818  3.833   0.45    0.0352  -0.0665  0.2154 0.2695  6.0723  0.3917  0.1     6.5     0.      -0.1009    -0.002301  -0.002349  3.8949  -1.1154  -0.0302   -0.004792  0.019716  0.203  300  2.1348  0.      -0.8626  1.11     800.        0.4534  0.3363  0.4681  0.4681  0.7035  0.5167
3     -3.9013  0.1168 -0.104  -0.1168 0.104   2.1488  5.9983  1.06  2.8875  -2.1  -0.5  50  7.5818  3.8361  0.45    0.016   -0.0516  0.2154 0.2695  6.5     0.1244  0.1     6.5     0.      -0.1003    -0.001344  -0.003306  3.7928  -1.1081  -0.0129   -0.001828  0.009643  0.277  300  3.5752  0.      -0.7882  1.291    800.        0.4558  0.3398  0.4617  0.4617  0.7006  0.4917
4     -4.2466  0.0732 -0.102  -0.0732 0.102  1.8957   6.1552  1.06  2.9058  -2.1  -0.5  50  7.5818  3.8369  0.45    0.0062  -0.0448  0.2154 0.2695  6.8035  0.0086  0.1     6.5     0.      -0.1001    -0.001084  -0.003566  3.7443  -1.0603  -0.0016   -0.001523  0.005379  0.309  300  3.8646  0.      -0.7195  1.387    800.        0.4574  0.3419  0.4571  0.4571  0.7001  0.4682
5     -4.5143  0.0484 -0.101  -0.0484 0.101  1.7228   6.2856  1.06  2.9169  -2.1  -0.5  50  7.5818  3.8376  0.45    0.0029  -0.0424  0.2154 0.2695  7.0389  0.      0.1     6.5     0.      -0.1001    -0.00101   -0.00364   3.709   -0.9872   0.       -0.00144   0.003223  0.321  300  3.7292  0.      -0.656   1.433    800.        0.4584  0.3435  0.4535  0.4535  0.7     0.4517
7.5   -5.0009  0.022  -0.101  -0.022  0.101  1.5737   6.5428  1.06  2.932   -2.1  -0.5  50  7.5818  3.838   0.45    0.0007  -0.0348  0.2154 0.2695  7.4666  0.      0.1     6.5     0.      -0.1       -0.000964  -0.003686  3.6632  -0.8274   0.       -0.001369  0.001134  0.329  300  2.3763  0.      -0.5202  1.46     800.        0.4601  0.3459  0.4471  0.4471  0.7     0.4167
10    -5.3461  0.0124 -0.1    -0.0124 0.1    1.5265   6.7415  1.06  2.9396  -2.1  -0.5  50  7.5818  3.838   0.45    0.0003  -0.0253  0.2154 0.2695  7.77    0.      0.1     6.5     0.      -0.1       -0.00095   -0.0037    3.623   -0.7053   0.       -0.001361  0.000515  0.33   300  1.7679  0.      -0.4068  1.464    800.        0.4612  0.3474  0.4426  0.4426  0.7     0.3755
""")


class ChiouYoungs2014PEER(ChiouYoungs2014):
    """
    This implements the Chiou & Youngs (2014) GMPE for use with the PEER
    tests. In this version the total standard deviation is fixed at 0.65
    """
    #: Only the total standars deviation is defined
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
    ])
    #: The PEER tests requires only PGA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
    ])

    def _get_stddevs(self, sites, rup, C, stddev_types, ln_y_ref, exp1, exp2):
        """
        Returns the standard deviation, which is fixed at 0.65 for every site
        """
        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 13
                ret.append(0.65 * np.ones_like(sites.vs30))
        return ret


class ChiouYoungs2014NearFaultEffect(ChiouYoungs2014):
    """
    This implements the Chiou & Youngs (2014) GMPE include the near fault
    effect prediction. In this version, we add the distance measure, rcdpp
    for directivity prediction.

    """
    #: Required distance measures are RRup, Rjb, Rx, and Rcdpp
    REQUIRES_DISTANCES = set(('rrup', 'rjb', 'rx', 'rcdpp'))

    def _get_centered_cdpp(self, dists):
        """
        Get directivity prediction parameter centered on the avgerage
        directivity prediction parameter.

        """
        centered_dpp = dists.rcdpp

        return centered_dpp
