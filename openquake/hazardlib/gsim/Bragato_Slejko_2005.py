# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
Module exports :class:`BragatoSlejko2005`.
"""

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

def _compute_distance(ctx, C):
    """
    equation 4, p.262:
    ``r = sqrt(d**2 + C['h']**2)``
    """
    return np.sqrt(ctx.rjb**2 + C['h']**2)

def _compute_mean(ctx, C):
    """
    Functional form (i.e., equation 5 in p. 262)
    """
    return C['a'] + (C['b'] + C['c'] * ctx.mag) * ctx.mag + (C['d'] + C['e'] * ctx.mag**3) * np.log10(_compute_distance)



class BragatoSlejko2005(GMPE):
    """
    Implements the Bragato P.L. and Slejko D. (2005) GMPE for the estimates of ONLY PGA, PGV or SA.
    Reference: 'Empirical Ground-Motion Attenuation Relations for the Eastern Alps in the Magnitude Range 2.5–6.3'.
    """
    
    #: Intensity measure types (IMTs, only PGA, PGV and SA are considered)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the running vectorial composition of two horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL

    #: Supported standard deviation type is the total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required rupture parameters is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rjb (Repi is not considered)
    REQUIRES_DISTANCES = {'rjb'}


    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = _compute_mean(ctx, C)

            # PGA and SA are already in g:
            mean[m] = np.log(10.0 ** imean)

            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['s'])


    #: Coefficients Table
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a       b       c       d       e       h       s
    PGA    -3.37   1.93  -0.203  -3.02  0.00744   7.3   0.358
    PGV    -2.72   2.04  -0.197  -2.81  0.00714   6.4   0.333
    0.05   -2.40   1.82  -0.201  -3.10  0.00758   8.2   0.423
    0.10   -3.23   2.03  -0.209  -2.91  0.00676   7.6   0.392
    0.11   -3.43   2.05  -0.209  -2.84  0.00649   7.4   0.388
    0.12   -3.51   2.04  -0.203  -2.80  0.00627   7.4   0.377
    0.13   -3.63   2.07  -0.205  -2.78  0.00631   7.4   0.364
    0.14   -3.73   2.16  -0.218  -2.84  0.00675   7.9   0.358
    0.15   -3.85   2.20  -0.223  -2.84  0.00694   7.9   0.353
    0.16   -3.93   2.26  -0.232  -2.86  0.00731   8.1   0.352
    0.17   -4.08   2.34  -0.244  -2.89  0.00753   8.5   0.346
    0.18   -4.20   2.36  -0.245  -2.86  0.00741   8.6   0.340
    0.19   -4.32   2.37  -0.241  -2.81  0.00715   8.6   0.336
    0.20   -4.42   2.41  -0.244  -2.82  0.00712   8.9   0.333
    0.22   -4.62   2.41  -0.240  -2.76  0.00679   8.8   0.330
    0.24   -4.90   2.42  -0.235  -2.67  0.00637   8.1   0.333
    0.26   -5.01   2.43  -0.231  -2.66  0.00610   8.2   0.336
    0.28   -5.18   2.47  -0.233  -2.64  0.00607   8.0   0.339
    0.30   -5.36   2.47  -0.231  -2.58  0.00596   7.4   0.344
    0.32   -5.45   2.46  -0.227  -2.55  0.00575   7.2   0.347
    0.34   -5.52   2.42  -0.220  -2.51  0.00557   6.8   0.347
    0.36   -5.64   2.41  -0.215  -2.46  0.00536   6.4   0.351
    0.38   -5.68   2.31  -0.200  -2.37  0.00500   5.8   0.351
    0.40   -5.72   2.26  -0.190  -2.31  0.00477   5.4   0.347
    0.42   -5.78   2.25  -0.188  -2.30  0.00469   5.4   0.346
    0.44   -5.89   2.31  -0.196  -2.34  0.00490   5.7   0.347
    0.46   -5.96   2.34  -0.201  -2.36  0.00515   5.8   0.347
    0.48   -5.96   2.33  -0.200  -2.37  0.00520   6.1   0.346
    0.50   -5.99   2.29  -0.194  -2.33  0.00511   5.8   0.340
    0.55   -6.10   2.27  -0.190  -2.29  0.00512   5.5   0.337
    0.60   -6.10   2.17  -0.174  -2.22  0.00480   5.3   0.332
    0.65   -6.17   2.13  -0.168  -2.19  0.00474   5.2   0.330
    0.70   -6.37   2.15  -0.168  -2.15  0.00464   5.0   0.328
    0.75   -6.45   2.15  -0.166  -2.15  0.00458   5.3   0.331
    0.80   -6.55   2.14  -0.162  -2.11  0.00446   5.1   0.330
    0.85   -6.53   2.09  -0.156  -2.10  0.00447   5.1   0.329
    0.90   -6.50   2.05  -0.152  -2.11  0.00449   5.2   0.330
    0.95   -6.59   2.08  -0.155  -2.12  0.00464   5.0   0.333
    1.00   -6.57   2.08  -0.157  -2.16  0.00480   5.3   0.335
    1.10   -6.66   2.09  -0.159  -2.18  0.00501   5.1   0.342
    1.20   -6.68   2.11  -0.162  -2.24  0.00528   5.5   0.350
    1.30   -6.86   2.23  -0.178  -2.34  0.00565   5.8   0.362
    1.40   -6.93   2.21  -0.173  -2.32  0.00558   5.3   0.369
    1.50   -6.97   2.21  -0.175  -2.34  0.00573   5.2   0.380
    1.60   -6.97   2.20  -0.173  -2.36  0.00579   5.2   0.389
    1.70   -7.03   2.21  -0.175  -2.37  0.00592   5.2   0.401
    1.80   -7.07   2.26  -0.184  -2.44  0.00621   5.9   0.412
    1.90   -7.06   2.16  -0.167  -2.36  0.00586   5.2   0.418
    2.00   -7.00   2.09  -0.159  -2.35  0.00583   5.3   0.423
    """)

