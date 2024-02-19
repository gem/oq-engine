# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
Module exports :class:`Zhang_Zhao2005SInter`,
               :class:`Zhang_Zhao2005SSlab`,
               :class:`Zhang_Zhao2005Crust`,
"""
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.imt import LSD
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable

    
def _SDinter_term(ctx):
    SD = 0.2485 * np.exp(-3.5387 + (1.438 * ctx.mag) - (
        0.0066 * (10 - ctx.mag) ** 3) - (
            1.785 * np.log(ctx.rrup + (1.097 * np.exp(0.617 * ctx.mag)))) +
                         (0.00648 * ctx.hypo_depth))
    return (1.856 * np.log10(SD))
    

def _SDslab_term(ctx):    
    SD = 0.2485 * np.exp(-3.5387 + (1.438 * ctx.mag) - (
        0.0066 * (10 - ctx.mag) ** 3) - (
            1.785 * np.log(ctx.rrup + (1.097 * np.exp(0.617 * ctx.mag)))
        ) + (0.00648 * ctx.hypo_depth) + 0.3643)
    return (1.856 * np.log10(SD))        
    

def _SDCrust_term(ctx, rake, mag):    
     # Reverse faulting
    if (rake >= 45.) & (rake <= 135.):
        C1 = -1.92
        C6 = 0.8285
    else:
        C1 = -2.17
        C6 = 0.8494
    
            
    if mag >= 6.5:
        SD = 0.06212 * np.exp(C1 + ctx.mag - (
            1.7 * (np.log(ctx.rrup + (0.3825 * np.exp(0.5882 * ctx.mag))))
        ) + C6 - (0.033 * (8.5 - ctx.mag) ** 2.5))
    else:
        SD = 0.06212 * np.exp(C1 + ctx.mag - (1.7 * (np.log(ctx.rrup + (
            2.1863 * np.exp(0.32 * ctx.mag))))) + C6 - (
                0.033 * (8.5 - ctx.mag) ** 2.5))
    return (1.856 * np.log10(SD))


def _compute_site_term(sites, c4, c5, c6, c7, c8):
   
    return (c4 * np.log10(sites.slope) +
            c5 * (sites.T_15) +
            c6 * np.log10(100 - sites.F_15) +
            (c7 * np.log10(sites.D50_15 + 0.1)) + c8)


class Zhang_Zhao2005SInter(GMPE):
    """
    Implements the GMPE of Zhang and Zhao. (2005) for Permanent ground
    deformation (m) from lateral spread 
    Zhang, J., & Zhao, J. X. (2005). Empirical models for estimating
    liquefaction-induced lateral spread displacement. Soil Dynamics and
    Earthquake Engineering, 25(6), 439-450.
    This model is based on Sadigh et al. (1997) and Young et al. (1997) models
    """
    #: This GMPE is based on subduction interface earthquakes 
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are Permanent ground deformation (m)
    #: from lateral spread
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {LSD}

    #: Supported intensity measure component is the horizontal
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {
        'slope',
        'freeface_ratio',
        'T_15',
        'F_15',
        'D50_15'}

    #: Required rupture parameters are magnitude and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is closest distance to rupture surface
    REQUIRES_DISTANCES = {'rrup'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True
            
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        for m, imt in enumerate(imts):
            ctx = ctx.copy()
            zslope = ctx.slope == 0.0
            ctx.slope[zslope] = ctx.freeface_ratio[zslope]
            c = np.zeros((5, len(ctx.sids)))  # slope coeffs updated
            for i in range(5):
                # where the slope is zero use the freeface coeffs
                c[i, zslope] = self.COEFFS_FREEFACE[imt][f'c{i+4}']
                c[i, ~zslope] = self.COEFFS_SLOPE[imt][f'c{i+4}']

            mean[m] = (
                _SDinter_term(ctx) +                 
                _compute_site_term(ctx, c[0], c[1], c[2], c[3], c[4]))
            mean[m] = np.log(10.0 ** mean[m])
            sig[m] = np.log(10.0 ** self.COEFFS_SLOPE[imt]["sigma"])

    COEFFS_SLOPE = CoeffsTable(table="""\
    IMT              c4       c5     c6       c7      c8   sigma
    LSD           0.356   0.0606  3.204  -1.0248  -4.292    0.22
    """)
    COEFFS_FREEFACE = CoeffsTable(table="""\
    IMT              c4       c5     c6       c7      c8   sigma
    LSD           0.456   0.0552  3.204  -1.0248  -4.743    0.22
    """)


class Zhang_Zhao2005SSlab(Zhang_Zhao2005SInter):
    """
    Implements the GMPE of Zhang and Zhao. (2005) for Permanent ground
    deformation (m) from lateral spread
    Zhang, J., & Zhao, J. X. (2005). Empirical models for estimating
    liquefaction-induced lateral spread displacement. Soil Dynamics and
    Earthquake Engineering, 25(6), 439-450. This model is based on Sadigh et
    al. (1997) and Young et al. (1997) models
    """
    #: This GMPE is based on subduction intraslab earthquakes
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        for m, imt in enumerate(imts):
            ctx = ctx.copy()
            zslope = ctx.slope == 0.0
            ctx.slope[zslope] = ctx.freeface_ratio[zslope]
            c = np.zeros((5, len(ctx.sids)))  # slope coeffs updated
            for i in range(5):
                # where the slope is zero use the freeface coeffs
                c[i, zslope] = self.COEFFS_FREEFACE[imt][f'c{i+4}']
                c[i, ~zslope] = self.COEFFS_SLOPE[imt][f'c{i+4}']

            mean[m] = (
                _SDslab_term(ctx) +                 
                _compute_site_term(ctx, c[0], c[1], c[2], c[3], c[4]))
            mean[m] = np.log(10.0 ** mean[m])
            sig[m] = np.log(10.0 ** self.COEFFS_SLOPE[imt]["sigma"])


    
class Zhang_Zhao2005Crust(Zhang_Zhao2005SInter):
    """
    Implements the GMPE of Zhang and Zhao. (2005) for Permanent ground
    deformation (m) from lateral spread 
    Zhang, J., & Zhao, J. X. (2005). Empirical models for estimating
    liquefaction-induced lateral spread displacement. Soil Dynamics and
    Earthquake Engineering, 25(6), 439-450.
    This model is based on Sadigh et al. (1997) and Young et al. (1997) models
    """
    #: This GMPE is based on crustal earthquakes 
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Required rupture parameters are magnitude 
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}
            
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        for m, imt in enumerate(imts):
            ctx = ctx.copy()
            zslope = ctx.slope == 0.0
            ctx.slope[zslope] = ctx.freeface_ratio[zslope]
            c = np.zeros((5, len(ctx.sids)))  # slope coeffs updated
            for i in range(5):
                # where the slope is zero use the freeface coeffs
                c[i, zslope] = self.COEFFS_FREEFACE[imt][f'c{i+4}']
                c[i, ~zslope] = self.COEFFS_SLOPE[imt][f'c{i+4}']

            mean[m] = (
                _SDCrust_term(ctx, ctx.rake[m], ctx.mag[m]) +   
                _compute_site_term(ctx,  c[0], c[1], c[2], c[3], c[4]))
               
            mean[m] = np.log(10.0 ** mean[m])
            sig[m] = np.log(10.0 ** self.COEFFS_SLOPE[imt]["sigma"])

