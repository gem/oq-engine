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
from openquake.hazardlib.gsim import utils
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA

def _compute_distance(ctx, C):
    """
    ``r = sqrt(dist**2 + C['h']**2)``
    """
    return np.sqrt(ctx.rjb**2 + C['h']**2)

def _compute_mean(ctx, C):
    """
    Functional form (e.g., equation 5 in p. 262)
    """
    mean = C['a'] + (C['b'] + C['c'] * ctx.mag) * ctx.mag + (C['d'] + C['e'] * ctx.mag**3) * np.log10(_compute_distance)

    reture mean


class BragatoSlejko2005(GMPE):
    """
    Implements the Bragato P.L. and Slejko D. (2005) GMPE for the estimates of ONLY PGAs.
    Reference: 'Empirical Ground-Motion Attenuation Relations for the Eastern Alps in the Magnitude Range 2.5–6.3'.
    """

    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    
    #: Supported intensity measure types (IMTs, only PGA is considered)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA}

    #: Supported intensity measure component is the running vectorial composition of two horizontal components
    #: "Vectorial addition: a_V = sqrt(max|a_NS(t)|^2 + max|a_EW(t)|^2)).
    #: This means that the maximum ground amplitudes occur simultaneously on
    #: the two horizontal components; this is a conservative assumption."
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rjb (Repi is not considered)
    REQUIRES_DISTANCES = {'rjb'}
    
    #: Distance metric used
    DISTANCE_METRIC = 'joyner-boore'

    sgn = 0

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = _compute_mean(ctx, C)

            # Convert units to g,
            # but only for PGA and SA (not PGV):
            if imt.string.startswith(('PGA', 'SA')):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:
                # PGV
                mean[m] = np.log(10.0 ** imean)

            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['s'])

            if self.sgn:
                mean[m] += self.sgn * sig[m]

_________________________________________________________________________________        
        # Compute the distance term
        r = np.sqrt(rjb**2 + coeffs['h']**2)
        
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


    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT      a     b        c      d         e    h       s
    PGA  -3.37  1.93   -0.203  -3.02   0.00744  7.3   0.358
    """)
