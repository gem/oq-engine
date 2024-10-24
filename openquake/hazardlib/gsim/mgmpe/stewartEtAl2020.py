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


def _get_fv(vs30, C):

    # Implements eq. 3 in SeA2020

    # Initialise fv
    fv = np.zeros_like(vs30)

    # First interval
    idx = (vs30 > CONSTANTS['vl']) & (vs30 <= C['v1'])
    fv[idx] = C['c'] * np.log(C['v1'] / CONSTANTS['vref'])

    # Second interval
    idx = (vs30 > C['v1']) & (vs30 <= C['v2'])
    fv[idx] = C['c'] * np.log(vs30[idx] / CONSTANTS['vref'])

    # Third interval
    idx = (vs30 > C['v2']) & (vs30 <= CONSTANTS['vu'])
    fv[idx] = C['c'] * np.log(C['v2'] / CONSTANTS['vref'])

    # Fourth interval
    idx = (vs30 > CONSTANTS['vu']) & (vs30 <= 3000)
    # TODO
    f760 = 0
    fv[idx] = (C['c'] * np.log(C['v2'] / CONSTANTS['vref']) -
               (C['c'] * np.log(C['v2'] / CONSTANTS['vref']) + f760) *
               (np.log(vs30[idx] / CONSTANTS['vu']) /
                (3000.0 / CONSTANTS['vu'])))

    return fv


def vs30_scaling_model(vs30, imtstr):
    C = COEFFS[imtstr]

    # Check the Vs30 provided
    if np.any(vs30 < CONSTANTS['vl']):
        msg = 'Vs30 values are beyond the limits supported by the limits'
        msg += ' admitted by the Stewart et al. (2020) model'
        raise ValueError(msg)

    # Amplification factor
    fv = _get_fv(vs30, C)

    return fv



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
