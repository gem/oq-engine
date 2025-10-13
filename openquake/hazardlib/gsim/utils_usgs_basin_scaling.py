# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
USGS basin scaling functions - these provide multiplicative adjustment factors
to apply to GMM basin terms based on the USGS basin model. The original java
code is available at:
https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/java/gov/usgs/earthquake/nshmp/gmm/GmmUtils.java 
"""
import numpy as np


def _get_z1pt0_usgs_basin_scaling(z1pt0, period):
    """
    Get the USGS basin model scaling factor for z1pt0-based GMM basin terms.
    """
    z_scale = _get_usgs_basin_scaling(
        z1pt0, basin_upper=0.3*1000, basin_lower=0.5*1000, period=period)

    return z_scale


def _get_z2pt5_usgs_basin_scaling(z2pt5, period):
    """
    Get the USGS basin model scaling factor for z2pt5 based GMM basin terms.
    """
    z_scale = _get_usgs_basin_scaling(
        z2pt5, basin_upper=1.0, basin_lower=3.0, period=period)

    return z_scale


def _get_usgs_basin_scaling(z, basin_upper, basin_lower, period):
    """
    Get the USGS basin model scaling factor to be applied to the GMM's
    basin amplification term. A non-zero scaling factor is applied to
    basin sites (defined by the z1pt0 or z2pt5 being deeper than the
    corresponding USGS basin model upper values) and for an SA with 
    T > 0.5 s only. For non-basin sites and/or short periods a scaling
    factor of 0.0 being returned in effect turns off the basin term in
    the GMM.

    If z is deeper than basin_upper a scaling factor of 1.0 will be
    returned (i.e. the basin term is unmodified).

    If z is shallower than basin_upper, a scaling factor of 0.0 will
    be returned (i.e. the basin term of the GMM will be turned off).

    If z is between basin_upper and basin_lower, a scaling factor
    of 0.0 < z_scale < 1.0 will be returned.
    """
    assert basin_lower > basin_upper
    z_scale = np.zeros(len(z))
    if period <= 0.5:
        return z_scale # Only apply basin scaling to T > 0.5 s (effectively
                       # turning off basin amplfication term for short-period
                       # ground-motions - zeros returned for each sites basin
                       # adjustment if the checkBasin function returns False
                       # in USGS java code)
    else:
        # First constrain z1pt0 or z2pt5 to basin limits
        z_constr = np.clip(z, basin_upper, basin_lower)
        basin_range = basin_lower - basin_upper
        # Get the multiplicative factor
        baf = (z_constr - basin_upper) / basin_range
        # And only apply for sites with z > basin_upper (i.e. z_min) - note
        # that it should inherently already be zero for sites with z shallower
        # than z_min given we are initially setting z_scale to zeros
        z_scale[z > basin_upper] = baf[z > basin_upper]
        if period == 0.75:
            return 0.585 * z_scale
        else:
            return z_scale