# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
Module :mod:`openquake.hazardlib.gsim.mgmpe.stewartEtAl2020` implements the
ergodic amplification model of Stewart et al. (2020)
"""

import numpy as np
import openquake.hazardlib.gsim.nga_east as ngae
from openquake.hazardlib.gsim.base import CoeffsTable

CONSTS = {"vref": 760.0,
          "vl": 200.0,
          "vu": 2000.0}


def _get_f760_imp_weights(vs30, vw1=600., vw2=400., w1=0.767, w2=0.1):
    # Computes the weights for the large impedance contrast case. The default
    # values of the parameters are specified at page 62 of Stewart et al.
    # (2020)
    #
    # param vs30
    #   A 1D :class:`numpy.ndarray` with Vs30 values

    # From scalar to array
    if not hasattr(vs30, "__len__"):
        vs30 = np.array([vs30])

    # Initialising the output
    out = np.zeros_like(vs30)

    # This is eq 6 in Stewart et al. (2020)
    out[vs30 >= vw1] = w1

    idx = np.nonzero((vs30 < vw1) & (vw2 <= vs30))
    term1 = np.log(vs30[idx] / vw2)
    term2 = np.log(vw1 / vw2)
    out[idx] = (w1 - w2) *  term1 / term2 + w2

    out[vs30 < vw2] = w2

    return out


def _get_f760_model(C760, wimp):
    # Implements eq. 5 in SeA2020
    #
    # param C760
    #   Coefficients for
    # param vs30
    #   A 1D numpy array with vs30 values
    # param wimp
    #   A scalar or an array of values in [0, 1]. The array must have the
    #   same cardinality of vs30

    # Compute the weight for gradient
    wgr = 1.0 - wimp

    # Compute the scaling factor
    return C760['f760i'] * wimp + C760['f760g'] * wgr


def _get_vs30_scaling_model(C, vs30, f760):
    # Implements eq. 3 in SeA2020
    #
    # param C
    #   Coefficients for a given IMT from table COEFFS
    # param vs30
    #   A 1D numpy array with vs30 values
    # param f760
    #   The f760 scaling factors

    # Initialise fv
    fv = np.zeros(len(vs30))

    # First interval - In the paper eq.3 they indicate vs30 > 200 but in figure
    # 13 they show results for this vs30 value
    idx = np.nonzero((vs30 >= CONSTS['vl']) & (vs30 <= C['v1']))[0]
    if len(idx):
        tmp = C['c'] * np.log(C['v1'] / CONSTS['vref'])
        fv[idx] = tmp

    # Second interval
    idx = (vs30 > C['v1']) & (vs30 <= C['v2'])
    if len(idx):
        tmp = C['c'] * np.log(vs30[idx] / CONSTS['vref'])
        fv[idx] = tmp

    # Third interval
    idx = (vs30 > C['v2']) & (vs30 <= CONSTS['vu'])
    if len(idx):
        fv[idx] = C['c'] * np.log(C['v2'] / CONSTS['vref'])

    # Fourth interval
    idx = (vs30 > CONSTS['vu']) & (vs30 <= 3000)
    if len(idx):
        term1 = C['c'] * np.log(C['v2'] / CONSTS['vref'])
        term2 = C['c'] * np.log(C['v2'] / CONSTS['vref']) + f760[idx]
        term3 = np.log(vs30[idx] / CONSTS['vu']) / np.log(3000.0 / CONSTS['vu'])
        fv[idx] = term1 - term2 * term3
    return fv


def stewart2020_linear_scaling(imt, vs30, wimp=None, usgs=False):
    """
    Implements the Vs30 scaling model of Stewart et al. (2020; EQS).

    NOTE a similar function is embedded in the NGA East implementation
    `nga_east.py`.  For the time being we retain this implementation as this
    code better fits the purpouse of being used within the modifiable GMPE.

    :param imt:
        Intensity measure type
    :param vs30:
        A vector with values of Vs30
    :param wimp:
        Weight for the impedance model (see eq. 5 of Stewart et al., 2020)
    :param usgs:
        Flag determining the use of the default coefficients or the ones
        proposed by the USGS
    :returns:
        The natual logaritm of the ground-motion scaling due to the linear
        component of amplification
    """

    # Check the Vs30 provided
    if np.any(vs30 < CONSTS['vl']):
        msg = 'Vs30 values are beyond the limits '
        msg += ' admitted by the Stewart et al. (2020) model'
        raise ValueError(msg)

    # Get f760
    if usgs:
        C = ngae.COEFFS_F760[imt]
    else:
        C = COEFFS_F760[imt]

    # Set weights for high impedance case
    if not hasattr(wimp, '__len__') and wimp is not None:
        wimp = np.ones_like(vs30) * wimp
    else:
        wimp = _get_f760_imp_weights(vs30)

    # Compute the f760 correction
    f760 = _get_f760_model(C, wimp)

    # Amplification factor
    C = COEFFS[imt]
    fv = _get_vs30_scaling_model(C, vs30, f760)

    return fv + f760


COEFFS_F760 = CoeffsTable(table="""\
       imt     f760i     f760g    f760is    f760gs
       pgv  0.375300   0.29700     0.313     0.117
       pga  0.185000   0.12100     0.434     0.248
     0.010  0.185000   0.12100     0.434     0.248
     0.020  0.185000   0.03100     0.434     0.270
     0.030  0.224000   0.00000     0.404     0.229
     0.040  0.283000   0.01200     0.390     0.139
     0.050  0.337000   0.06200     0.363     0.093
     0.075  0.475000   0.21100     0.322     0.102
     0.080  0.512000   0.23700     0.335     0.103
     0.100  0.674000   0.33800     0.366     0.088
     0.110  0.729980   0.37700     0.352     0.076
     0.112  0.741370   0.38400     0.348     0.075
     0.113  0.747420   0.38800     0.345     0.075
     0.114  0.753000   0.39100     0.343     0.075
     0.115  0.757590   0.39400     0.340     0.074
     0.116  0.760650   0.39700     0.338     0.073
     0.117  0.761780   0.40000     0.335     0.072
     0.118  0.761100   0.40300     0.333     0.072
     0.119  0.758940   0.40600     0.330     0.071
     0.120  0.755620   0.40900     0.327     0.071
     0.125  0.732340   0.42200     0.313     0.070
     0.130  0.716410   0.43400     0.299     0.070
     0.135  0.668700   0.44400     0.286     0.071
     0.140  0.660260   0.45400     0.273     0.070
     0.150  0.586000   0.47000     0.253     0.066
     0.200  0.419000   0.50900     0.214     0.053
     0.250  0.332000   0.50900     0.177     0.052
     0.300  0.270000   0.49800     0.131     0.055
     0.400  0.209000   0.47300     0.112     0.060
     0.500  0.175000   0.44700     0.105     0.067
     0.750  0.127000   0.38600     0.138     0.077
     0.800  0.120000   0.37800     0.133     0.077
     1.000  0.095000   0.34400     0.124     0.078
     1.500  0.083000   0.28900     0.112     0.081
     2.000  0.079000   0.25800     0.118     0.088
     3.000  0.073000   0.23300     0.111     0.100
     4.000  0.066000   0.22400     0.120     0.109
     5.000  0.064000   0.22000     0.108     0.115
     7.500  0.056000   0.21600     0.082     0.130
    10.000  0.053000   0.21800     0.069     0.137
""")

COEFFS = CoeffsTable(sa_damping=5, table="""\
       IMT         c        v1        v2        vf  sigma_vc     sigma   sigma_u
       pgv  -0.44900    331.00    760.00    314.00   0.25100   0.30600   0.33400
       pga  -0.29000    319.00    760.00    345.00   0.30000   0.34500   0.48000
     0.010  -0.29000    319.00    760.00    345.00   0.30000   0.34500   0.48000
     0.020  -0.30300    319.00    760.00    343.00   0.29000   0.33600   0.47900
     0.030  -0.31500    319.00    810.00    342.00   0.28200   0.32700   0.47800
     0.040  -0.33100    319.00    900.00    340.00   0.27500   0.31700   0.47700
     0.050  -0.34400    319.00   1010.00    338.00   0.27100   0.30800   0.47600
     0.075  -0.34800    319.00   1380.00    334.00   0.26900   0.28500   0.47300
     0.080  -0.35800    318.38   1450.00    333.00   0.26800   0.28100   0.47200
     0.100  -0.37200    317.13   1900.00    319.00   0.27000   0.26300   0.47000
     0.110  -0.37410    315.27   2000.00    318.41   0.26959   0.26794   0.46303
     0.112  -0.37456    314.78   2000.00    318.30   0.26933   0.26887   0.46106
     0.113  -0.37479    314.52   2000.00    318.25   0.26918   0.26933   0.46002
     0.114  -0.37503    314.25   2000.00    318.19   0.26903   0.26979   0.45894
     0.115  -0.37526    313.98   2000.00    318.14   0.26886   0.27024   0.45782
     0.116  -0.37549    313.70   2000.00    318.08   0.26868   0.27069   0.45666
     0.117  -0.37573    313.41   2000.00    318.03   0.26850   0.27113   0.45547
     0.118  -0.37597    313.12   2000.00    317.98   0.26831   0.27157   0.45425
     0.119  -0.37621    312.82   2000.00    317.93   0.26811   0.27201   0.45300
     0.120  -0.37645    312.51   2000.00    317.88   0.26791   0.27244   0.45171
     0.125  -0.37768    310.90   2000.00    317.62   0.26682   0.27456   0.44483
     0.130  -0.37898    309.19   2000.00    317.38   0.26565   0.27659   0.43729
     0.135  -0.38036    307.38   1800.00    317.15   0.26445   0.27854   0.42916
     0.140  -0.38182    305.51   1775.00    316.93   0.26325   0.28043   0.42053
     0.150  -0.38500    301.63   1500.00    316.50   0.26100   0.28400   0.40200
     0.200  -0.40300    279.00   1072.91    314.00   0.25100   0.30600   0.33400
     0.250  -0.41700    249.88    944.81    282.00   0.23800   0.29100   0.35700
     0.300  -0.42600    224.50    867.45    250.00   0.22500   0.27600   0.38100
     0.400  -0.45200    216.50    842.72    250.00   0.22500   0.27500   0.38100
     0.500  -0.48000    216.88    822.12    280.00   0.22500   0.31100   0.32300
     0.750  -0.51000    226.88    814.21    280.00   0.22500   0.33000   0.31000
     0.800  -0.52300    235.00    810.00    280.00   0.22500   0.33400   0.30800
     1.000  -0.55700    254.75    790.00    300.00   0.22500   0.37700   0.36100
     1.500  -0.57400    275.50    805.00    300.00   0.24200   0.40500   0.37500
     2.000  -0.58400    296.00    810.00    300.00   0.25900   0.41300   0.38800
     3.000  -0.58800    311.50    819.94    313.00   0.30600   0.41000   0.55100
     4.000  -0.57900    321.25    821.33    322.00   0.34000   0.40500   0.58500
     5.000  -0.55800    324.25    825.00    325.00   0.34000   0.40900   0.58700
     7.500  -0.54400    325.00    819.76    328.00   0.34500   0.42000   0.59400
    10.000  -0.50700    325.00    820.00    330.00   0.35000   0.44000   0.60000

""")
