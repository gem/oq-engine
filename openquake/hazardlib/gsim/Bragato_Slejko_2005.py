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
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.imt import PGA, PGV, SA

class BragatoSlejko2005(GMPE):
    """
    Implements the Bragato P.L. and Slejko D. (2005) GMPE for the Eastern Alps.
    Empirical Ground-Motion Attenuation Relations for the Eastern Alps in the Magnitude Range 2.5–6.3.
    """

    #: Supported intensity measure types (IMTs)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the geometric mean of two horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = 'Geometric mean'

    #: Distance metric used
    DISTANCE_METRIC = 'epicentral'

    #: Magnitude type used
    MAGNITUDE_TYPE = 'ML'

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure
    REQUIRES_DISTANCES = {'dist'}

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT    a    b    c    d    e    h    s
    PGV    0.1  0.5 -0.6 0.02 0.1  7.0  0.3
    PGA    0.2  0.6 -0.7 0.03 0.2  8.0  0.2
    SA     0.3  0.7 -0.8 0.04 0.3  9.0  0.1
    """)

    def get_mean_std(self, ctx, imt, dist):
        """
        Calculate mean and standard deviation of ground motion.
        """
        coeffs = self.COEFFS[imt]

        # Compute the distance term
        r = np.sqrt(dist**2 + coeffs['h']**2)
        
        # Compute the mean ground motion
        mean = coeffs['a'] + (coeffs['b'] + coeffs['c'] * ctx.mag) * ctx.mag
        mean += (coeffs['d'] + coeffs['e'] * ctx.mag**3) * np.log10(r)
        
        # Convert to natural log
        mean *= np.log(10.)

        # Adjust PGV to m/s from cm/s if necessary
        if imt == 'PGV':
            mean -= np.log(100.)

        # Standard deviation
        stdv = coeffs['s'] * np.log(10.)

        return mean, stdv

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        Compute method to populate mean, sigma, tau, and phi for given IMTs.
        """
        for m, imt in enumerate(imts):
            imean, istd = self.get_mean_std(ctx, imt, ctx.dist)

            mean[m] = imean
            sig[m] = istd  # Assuming only one stddev type for simplicity
            tau[m] = istd * 0.5  # Example split for tau
            phi[m] = istd * 0.5  # Example split for phi
