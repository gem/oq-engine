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
from openquake.hazardlib.gsim.base import CoeffsTable

CONSTANTS = {"vref": 760.0,
             "vl": 200.0,
             "vu": 2000.0}


def _get_sigma(vs30):
    pass


def _get_f760_model(C760, vs30, wimp):
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
    return C760['impedance'] * wimp + C760['gradient'] * wgr


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
    idx = np.nonzero((vs30 >= CONSTANTS['vl']) & (vs30 <= C['v1']))[0]
    tmp = C['c'] * np.log(C['v1'] / CONSTANTS['vref'])
    fv[idx] = tmp

    # Second interval
    idx = (vs30 > C['v1']) & (vs30 <= C['v2'])
    fv[idx] = C['c'] * np.log(vs30[idx] / CONSTANTS['vref'])

    # Third interval
    idx = (vs30 > C['v2']) & (vs30 <= CONSTANTS['vu'])
    fv[idx] = C['c'] * np.log(C['v2'] / CONSTANTS['vref'])

    # Fourth interval
    idx = (vs30 > CONSTANTS['vu']) & (vs30 <= 3000)
    fv[idx] = (C['c'] * np.log(C['v2'] / CONSTANTS['vref']) -
               ((C['c'] * np.log(C['v2'] / CONSTANTS['vref']) + f760) *
                np.log(vs30[idx] / CONSTANTS['vu']) /
                np.log(3000.0 / CONSTANTS['vu'])))

    return fv


def stewart2020_linear_scaling(imt, vs30, wimp):
    """
    Implements the Vs30 scaling model of Stewart et al. (2020; EQS).

    NOTE a similar function is embedded in the NGA East implementation
    `nga_east.py`.  For the time being we retain this implementation as this
    code better fit the purpouse of being used within the modifiable GMPE.

    :param imt:
        Intensity measure type
    :param vs30:
        A vector with values of Vs30
    :param wimp:
        Weight for the impedance model
    """

    # Check the Vs30 provided
    if np.any(vs30 < CONSTANTS['vl']):
        msg = 'Vs30 values are beyond the limits '
        msg += ' admitted by the Stewart et al. (2020) model'
        raise ValueError(msg)

    # Get f760
    C = COEFFS_F760[imt]
    f760 = _get_f760_model(C, vs30, wimp)

    # Amplification factor
    C = COEFFS[imt]
    fv = _get_vs30_scaling_model(C, vs30, f760)

    return fv + f760


COEFFS_F760 = CoeffsTable(table="""\
       IMT impedance  gradient sigma_imp sigma_grad
       pgv  0.375300   0.29700     0.313     0.117
       pga  0.185000   0.12100     0.434     0.248
      0.01  0.185000   0.12100     0.434     0.248
      0.02  0.185000   0.03100     0.434     0.270
      0.03  0.224000   0.00000     0.404     0.229
      0.04  0.283000   0.01200     0.390     0.139
      0.05  0.337000   0.06200     0.363     0.093
      0.07  0.475000   0.21100     0.322     0.102
      0.08  0.512000   0.23700     0.335     0.103
      0.10  0.674000   0.33800     0.366     0.088
      0.11  0.729980   0.37700     0.352     0.076
      0.11  0.741370   0.38400     0.348     0.075
      0.11  0.747420   0.38800     0.345     0.075
      0.11  0.753000   0.39100     0.343     0.075
      0.12  0.757590   0.39400     0.340     0.074
      0.12  0.760650   0.39700     0.338     0.073
      0.12  0.761780   0.40000     0.335     0.072
      0.12  0.761100   0.40300     0.333     0.072
      0.12  0.758940   0.40600     0.330     0.071
      0.12  0.755620   0.40900     0.327     0.071
      0.12  0.732340   0.42200     0.313     0.070
      0.13  0.716410   0.43400     0.299     0.070
      0.14  0.668700   0.44400     0.286     0.071
      0.14  0.660260   0.45400     0.273     0.070
      0.15  0.586000   0.47000     0.253     0.066
      0.20  0.419000   0.50900     0.214     0.053
      0.25  0.332000   0.50900     0.177     0.052
      0.30  0.270000   0.49800     0.131     0.055
      0.40  0.209000   0.47300     0.112     0.060
      0.50  0.175000   0.44700     0.105     0.067
      0.75  0.127000   0.38600     0.138     0.077
      0.80  0.120000   0.37800     0.133     0.077
      1.00  0.095000   0.34400     0.124     0.078
      1.50  0.083000   0.28900     0.112     0.081
      2.00  0.079000   0.25800     0.118     0.088
      3.00  0.073000   0.23300     0.111     0.100
      4.00  0.066000   0.22400     0.120     0.109
      5.00  0.064000   0.22000     0.108     0.115
      7.50  0.056000   0.21600     0.082     0.130
     10.00  0.053000   0.21800     0.069     0.137
""")

COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         c        v1        v2        vf  sigma_vc     sigma   sigma_u
    pgv -0.449000    331.00    760.00    314.00      0.25      0.31      0.33
    pga -0.290000    319.00    760.00    345.00      0.30      0.34      0.48
   0.01 -0.290000    319.00    760.00    345.00      0.30      0.34      0.48
   0.02 -0.303000    319.00    760.00    343.00      0.29      0.34      0.48
   0.03 -0.315000    319.00    810.00    342.00      0.28      0.33      0.48
   0.04 -0.331000    319.00    900.00    340.00      0.28      0.32      0.48
   0.05 -0.344000    319.00   1010.00    338.00      0.27      0.31      0.48
   0.07 -0.348000    319.00   1380.00    334.00      0.27      0.28      0.47
   0.08 -0.358000    318.38   1450.00    333.00      0.27      0.28      0.47
   0.10 -0.372000    317.13   1900.00    319.00      0.27      0.26      0.47
   0.11 -0.374100    315.27   2000.00    318.41      0.27      0.27      0.46
   0.11 -0.374560    314.78   2000.00    318.30      0.27      0.27      0.46
   0.11 -0.374790    314.52   2000.00    318.25      0.27      0.27      0.46
   0.11 -0.375030    314.25   2000.00    318.19      0.27      0.27      0.46
   0.12 -0.375260    313.98   2000.00    318.14      0.27      0.27      0.46
   0.12 -0.375490    313.70   2000.00    318.08      0.27      0.27      0.46
   0.12 -0.375730    313.41   2000.00    318.03      0.27      0.27      0.46
   0.12 -0.375970    313.12   2000.00    317.98      0.27      0.27      0.45
   0.12 -0.376210    312.82   2000.00    317.93      0.27      0.27      0.45
   0.12 -0.376450    312.51   2000.00    317.88      0.27      0.27      0.45
   0.12 -0.377680    310.90   2000.00    317.62      0.27      0.27      0.44
   0.13 -0.378980    309.19   2000.00    317.38      0.27      0.28      0.44
   0.14 -0.380360    307.38   1800.00    317.15      0.26      0.28      0.43
   0.14 -0.381820    305.51   1775.00    316.93      0.26      0.28      0.42
   0.15 -0.385000    301.63   1500.00    316.50      0.26      0.28      0.40
   0.20 -0.403000    279.00   1072.91    314.00      0.25      0.31      0.33
   0.25 -0.417000    249.88    944.81    282.00      0.24      0.29      0.36
   0.30 -0.426000    224.50    867.45    250.00      0.23      0.28      0.38
   0.40 -0.452000    216.50    842.72    250.00      0.23      0.28      0.38
   0.50 -0.480000    216.88    822.12    280.00      0.23      0.31      0.32
   0.75 -0.510000    226.88    814.21    280.00      0.23      0.33      0.31
   0.80 -0.523000    235.00    810.00    280.00      0.23      0.33      0.31
   1.00 -0.557000    254.75    790.00    300.00      0.23      0.38      0.36
   1.50 -0.574000    275.50    805.00    300.00      0.24      0.41      0.38
   2.00 -0.584000    296.00    810.00    300.00      0.26      0.41      0.39
   3.00 -0.588000    311.50    819.94    313.00      0.31      0.41      0.55
   4.00 -0.579000    321.25    821.33    322.00      0.34      0.41      0.58
   5.00 -0.558000    324.25    825.00    325.00      0.34      0.41      0.59
   7.50 -0.544000    325.00    819.76    328.00      0.34      0.42      0.59
  10.00 -0.507000    325.00    820.00    330.00      0.35      0.44      0.60
""")
