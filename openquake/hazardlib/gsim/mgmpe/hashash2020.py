# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024, GEM Foundation
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
Module :mod:`openquake.hazardlib.gsim.mgmpe.hashash2020` implements the
ergodic non-linear amplification model of Hashash et al. (2020)
"""

import numpy as np
from openquake.hazardlib.gsim.base import CoeffsTable

C760OVER3000 = 2.275


def hashash2020_non_linear_scaling(imt, vs30, ref_pga, ref_vs30):
    """
    Implements the non-linear scaling model of Hashash et al. (2020; EQS).

    :param imt:
        The intensity measure type consided
    :param vs30:
        The value of vs30 at each site
    :param ref_pga:
        The reference PGA at each site computed considering a vs30 value of
        `ref_vs30`
    :param ref_vs30:
        Reference vs30. It can be either 3000 or 760 m/s
    :returns:
        The natural logarithm of the non-linear scaling factor
    """

    msg = 'Size of `ref_pga` does not match the one of `vs30`'
    assert len(vs30) == len(ref_pga), msg
    C = COEFFS[imt]

    if np.abs(ref_vs30 - 3000) < 1e-1:
        ref_pga = ref_pga
    elif np.abs(ref_vs30 - 760) < 1e-1:
        ref_pga = ref_pga / C760OVER3000
    else:
        msg = "The supported reference Vs30 is either 760 or 3000m/s"
        raise ValueError(msg)

    # Fixing reference (see text at the bottom of page 71)
    if imt.period < 0.4:
        ref_vs30 = 760.0

    # Compute the argument of the logarithm in eq. 2
    coeff = (ref_pga + C['f3']) / C['f3']

    if not hasattr(coeff, '__len__'):
        coeff = np.array([coeff])

    # Initialize the output
    fnl = np.zeros(vs30.shape)

    # Compute eq.3
    idx = vs30 < C['vc']
    vsmin = np.minimum(vs30[idx], ref_vs30)
    exp1 = np.exp(C['f5'] * (vsmin - 360.))
    exp2 = np.exp(C['f5'] * (ref_vs30 - 360.0))
    f2 = C['f4'] * (exp1 - exp2)

    # Compute the median nonlinear amplification term using eq.2
    msg = "Logarithm's argument lower than 0"
    assert np.all(coeff[idx] > 0.0), msg
    fnl[idx] = f2 * np.log(coeff[idx])

    return fnl


COEFFS = CoeffsTable(table="""\
    IMT     f3       f4       f5       vc        sigma_c
    pgv     0.06089  -0.08344 -0.00667 2260      0.12
    pga     0.089417 -0.44895 -0.00175 2990      0.12
    0.001   0.089417 -0.44895 -0.00175 2990      0.12
    0.01    0.075204 -0.43755 -0.00131 2990      0.12
    0.02    0.056603 -0.41511 -0.00098 2990      0.12
    0.03    0.103599 -0.49871 -0.00127 2990      0.12
    0.04    0.118356 -0.48734 -0.00169 2990      0.12
    0.05    0.16781  -0.58073 -0.00187 2990      0.12
    0.075   0.173858 -0.53646 -0.00259 2990      0.12
    0.08    0.162486 -0.50667 -0.00273 2990      0.12
    0.1     0.150834 -0.44661 -0.00335 2990      0.12
    0.11    0.14360  -0.42607 -0.00359 2990      0.12
    0.112   0.14122  -0.41883 -0.00364 2990      0.12
    0.113   0.14004  -0.41525 -0.00367 2990      0.12
    0.114   0.13887  -0.41171 -0.00369 2990      0.12
    0.115   0.13772  -0.40820 -0.00372 2990      0.12
    0.116   0.13657  -0.40472 -0.00374 2990      0.12
    0.117   0.13543  -0.40126 -0.00377 2990      0.12
    0.118   0.13431  -0.39784 -0.00379 2990      0.12
    0.119   0.13319  -0.39445 -0.00382 2990      0.12
    0.12    0.132082 -0.39108 -0.00384 2990      0.12
    0.125   0.131419 -0.38483 -0.00387 2990      0.12
    0.13    0.130782 -0.37882 -0.0039  2990      0.12
    0.135   0.13309  -0.37777 -0.00392 2990      0.12
    0.14    0.135578 -0.37864 -0.00396 2990      0.12
    0.15    0.142721 -0.38264 -0.0041  2335.376  0.12
    0.2     0.128154 -0.30481 -0.00488 1532.801  0.12
    0.25    0.132857 -0.27506 -0.00564 1317.97   0.135
    0.3     0.130701 -0.22825 -0.00655 1151.791  0.15
    0.4     0.094143 -0.11591 -0.00872 1018.069  0.15
    0.5     0.09888  -0.07793 -0.01028 938.516   0.15
    0.75    0.061011 -0.0178  -0.01456 834.7709  0.125
    0.8     0.073572 -0.01592 -0.01515 832.4085  0.1
    1.0     0.043672 -0.00478 -0.01823 950.9678  0.06
    1.5     0.004796 -0.00086 -0.02    882.2115  0.05
    2.0     0.00164  -0.00236 -0.01296 878.8883  0.04
    3.0     0.007458 -0.00626 -0.01043 894.3879  0.04
    4.0     0.002694 -0.00331 -0.01215 874.8681  0.03
    5.0     0.002417 -0.00256 -0.01325 856.1077  0.02
    7.5     0.042192 -0.00536 -0.01418 831.6034  0.02
    10      0.053289 -0.00631 -0.01403 837.0494  0.02
""")
