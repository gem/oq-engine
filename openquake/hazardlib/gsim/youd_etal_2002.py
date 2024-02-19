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
Module
:mod:`openquake.hazardlib.gsim.youd_etal_2002`
exports
:class:`YoudEtAl2002`
"""

import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.imt import LSD
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable


def _compute_magnitude_term(rup, c0, c1):
    """
    Returns the magnitude scaling term
    """
    return c0 + c1 * rup.mag


def _compute_distance_term(dists, R, c2, c3):
    """
    Returns the distance scaling term
    """
    return c3 * dists.repi + c2 * np.log10(R)


def _compute_site_term(sites, c4, c5, c6, c7):
    """
    Returns the distance scaling term
    """
    return (c4 * np.log10(sites.slope) +
            c5 * np.log10(sites.T_15) +
            c6 * np.log10(100 - sites.F_15) +
            c7 * np.log10(sites.D50_15 + 0.1))


class YoudEtAl2002(GMPE):
    """
    Implements the GMPE of Youd et al. (2002) for calculating Permanent
    ground defomation(m) from lateral spread

    Youd, T. L., Hansen, C. M., & Bartlett, S. F. (2002). Revised
    multilinear regression equations for prediction of lateral spread
    displacement. Journal of Geotechnical and Geoenvironmental Engineering,
    128(12), 1007-1017.
    """
    #: This GMPE is based on non-subduction earthquakes with M<8
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

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

    #: Required rupture parameters are magnitude (ML is used)
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is epicentral distance
    REQUIRES_DISTANCES = {'repi'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True


    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        for m, imt in enumerate(imts):
            #Adjustment done by Prajakta Jadhav and Dharma Wijewickreme: 
            #To adopt epicentral distance of 5km for deep sources (depth>50km)
            #and within epicentral distance of 5km
            ctx = ctx.copy()
            ctx.repi[(ctx.repi < 5.) & (ctx.hypo_depth >= 50.)] = 5.0
            
            R = (10 ** ((0.89 * ctx.mag) - 5.64)) + ctx.repi
            zslope = ctx.slope == 0.0
            ctx.slope[zslope] = ctx.freeface_ratio[zslope]
            c = np.zeros((8, len(ctx.sids)))  # slope coeffs updated
            for i in range(8):
                # where the slope is zero use the freeface coeffs
                c[i, zslope] = self.COEFFS_FREEFACE[imt][f'c{i}']
                c[i, ~zslope] = self.COEFFS_SLOPE[imt][f'c{i}']

            mean[m] = (
                _compute_magnitude_term(ctx, c[0], c[1]) +
                _compute_distance_term(ctx, R, c[2], c[3]) +
                _compute_site_term(ctx, c[4], c[5], c[6], c[7]))
            mean[m] = np.log(10.0 ** mean[m])
            sig[m] = np.log(10.0 ** self.COEFFS_SLOPE[imt]["sigma"])

    COEFFS_SLOPE = CoeffsTable(table="""\
    IMT                c0     c1       c2      c3     c4     c5     c6      c7     sigma
    LSD           -16.213  1.532   -1.406  -0.012  0.338   0.54  3.413  -0.795     0.197
    """)
    COEFFS_FREEFACE = CoeffsTable(table="""\
    IMT                c0     c1       c2      c3     c4     c5     c6      c7     sigma
    LSD           -16.713  1.532   -1.406  -0.012  0.592   0.54  3.413  -0.795     0.197
    """)
