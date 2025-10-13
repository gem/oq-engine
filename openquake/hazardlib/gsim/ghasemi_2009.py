# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:'GhasemiEtAl2009' 
"""
import numpy as np
from scipy.constants import g


from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_distance_scaling(C, rrup, mag):
    """
    Returns the distance scaling term
    """
    a5 = 0.42
    rscale1 = rrup + C["a4"] * (10.0 ** (a5 * mag))
    return C["a3"]*np.log10(rscale1)


def _compute_magnitude_scaling(C, mag):
    """
    Returns the magnitude scaling term
    """
    return C["a2"] * mag + C["a1"]


def _compute_site_amplification(C, ctx):
    """
    Compute the fourth and fifth terms of the equation 1 described on paragraph
    """
    sSoil, sRock = _get_site_type_dummy_variables(ctx)
    return (C["a6"] * sRock + C['a7'] * sSoil)

def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, two site type is considered
    based on the shear wave velocity intervals in the uppermost 30 m, Vs30:
    Soil: Vs30 < 760 m/s
    Rock: Vs30 >= 760 m/s
    """
    sRock = np.zeros(len(ctx.vs30))
    sSoil = np.zeros(len(ctx.vs30))

    # Soil;  Vs30 < 760 m/s.
    idx = (ctx.vs30 >= 1E-10) & (ctx.vs30 < 760)
    sSoil[idx] = 1.0
    # Rock; Vs30 >= 760 m/s.
    idx = (ctx.vs30 >= 760)
    sRock[idx] = 1.0
    return sSoil, sRock

class GhasemiEtAl2009(GMPE):
    """
    Implements the PGA GMPE of H.Ghasemi, M.Zare, Y,Fukushima, K.Koketsu
    (2009a) An empirical spectral ground-motion model for Iran, 
    J Seismol, 13:499-515, DOI 10.1007/s10950-008-9143-x.
    """
    #: The GMPE is derived from shallow earthquakes in California and Japan
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types is spectral acceleration
    #: The attenuation relation developed by Ghasemi et. al estimates only the 'SA'.
    #: Here in this code, the intensity measure of 'PGA' is also considered 
    #: with the same coefficients as SA(0.05 s), in case of need.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the average horizontal
    #: component
    #: :attr:`openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is rupture distance
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            imean = (_compute_magnitude_scaling(C, ctx.mag) +
                     _compute_distance_scaling(C, ctx.rrup, ctx.mag) +
                     _compute_site_amplification(C, ctx))
            # Original GMPE returns log10 acceleration in cm/s/s
            # Converts to natural logarithm of g
            mean[m] = np.log((10.0 ** (imean - 2.0)) / g)


            # Convert from common logarithm to natural logarithm
            sig[m] = np.log(10 ** C['sigma'])

    
    #: The attenuation relation developed by Ghasemi et. al estimates only the 'SA'.
    #: Here in this code, a line for intensity measure of 'PGA' is also considered 
    #: with the same coefficients as SA(0.05 s), in case of need. 

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a1       a2       a3       a4       a6       a7       sigma
    PGA     0.868    0.405   -1.424    0.014    0.859    0.836    0.319               
    0.05    0.868    0.405   -1.424    0.014    0.859    0.836    0.319
    0.06    0.906    0.398   -1.440    0.015    0.944    0.911    0.322    
    0.07    0.957    0.394   -1.449    0.015    0.978    0.937    0.325
    0.08    0.700    0.387   -1.427    0.015    1.282    1.238    0.325
    0.09    0.966    0.384   -1.413    0.016    1.046    1.005    0.326
    0.10    0.904    0.380   -1.396    0.016    1.136    1.096    0.331
    0.20    0.786    0.425   -1.215    0.015    0.663    0.748    0.319
    0.30    0.432    0.474   -1.134    0.014    0.477    0.605    0.318
    0.40    0.246    0.528   -1.080    0.011    0.135    0.289    0.327
    0.50    0.003    0.571   -1.069    0.010    0.002    0.173    0.333
    0.60   -0.118    0.608   -1.053    0.010   -0.209   -0.037    0.337
    0.70   -0.234    0.635   -1.034    0.009   -0.361   -0.194    0.347
    0.80   -0.331    0.673   -1.083    0.010   -0.450   -0.300    0.336
    0.90   -0.459    0.706   -1.092    0.011   -0.570   -0.424    0.335
    1.00   -0.567    0.727   -1.071    0.011   -0.678   -0.533    0.336
    2.00   -1.209    0.876   -1.104    0.011   -1.291   -1.183    0.363
    3.00   -1.436    0.920   -1.151    0.012   -1.515   -1.411    0.370
    """)

