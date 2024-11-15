# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2024 GEM Foundation
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


def _get_z1pt0_usgs_basin_scaling(z, period):
    """
    Get the USGS basin model scaling factor for z1pt0-based GMM basin terms.
    """
    z_scale = _get_usgs_basin_scaling(
        z, basin_upper=0.3, basin_lower=0.5, period=period)

    return z_scale


def _get_z2pt5_usgs_basin_scaling(z, period):
    """
    Get the USGS basin model scaling factor for z2pt5 based GMM basin terms.
    """
    z_scale = _get_usgs_basin_scaling(
        z, basin_upper=1.0, basin_lower=3.0, period=period)

    return z_scale


def _get_usgs_basin_scaling(z2pt5, basin_upper, basin_lower, period):
    """
    Get the USGS basin model scaling factor to be applied to the
    basin amplification term.
    """
    constr = np.clip(z2pt5, basin_upper, basin_lower)
    basin_range = basin_lower - basin_upper
    z_scale = (constr - basin_upper) / basin_range
    if period == 0.75:
        return 0.585 * z_scale
    else:
        return z_scale