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
Utilities for implementation of the Chapman and Guo (2021) Coastal Plain
site amplification model as required for the 2023 Conterminous US NSHMP.

Chapman, M.C. and Guo, Z., 2021, A response spectral ratio model to account
for amplification and attenuation effects in the Atlantic and Gulf coastal
plain: Bulletin of the Seismological Society of America, 111 (4), pp.1849-1867.

The majority of the USGS java code for implementing this model is available here:
https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/java/gov/usgs/earthquake/nshmp/gmm/ChapmanGuo_2021.java?ref_type=heads

The code for obtaining the f_cpa parameter is available within
the USGS java code for the NGAEast GMMs which is taken from here:
https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/java/gov/usgs/earthquake/nshmp/gmm/NgaEast.java
"""
import numpy as np


def get_zscale(z_sed):
    """
    Provide the depth scaling factor for application of reference site
    scaling. The scaling factor increases to 1.0 as z_sed approaches a
    value of 1 km.

    :param z_sed: Depth to sediment site parameter considered in the
                  Chapman and Guo (2021) Coastal Plains site amplification
                  model as part of the 2023 Conterminous US NSHMP.
    """
    Z_CUT = 2.
    s = 1. - np.exp(z_sed / Z_CUT)
    return s ** 4


def get_fcpa(ctx, imt, z_scale, psa_df):
    """
    Get f_cpa param for the given sediment depth, Mw and rjb.

    This function returns both f_cpa and z_scale within a dictionary which is
    passed into the nga_east functions for computation of mean ground-motions.
    """
    # Set default f_cpa of zero for each site
    f_cpa = np.full(len(ctx.vs30), 0.)

    # Get sites with sed. depth greater than 0 km
    mask_z = z_scale > 0.

    # For these sites recompute f_cpa parameter
    if np.any(mask_z):
        f_cpa[mask_z] = get_psa_ratio(ctx, imt, psa_df)

    # Put Coastal Plain params into a dict for passing into nga_east functions
    coastal = {'f_cpa': f_cpa, 'z_scale': z_scale}

    return coastal


def get_psa_ratio(ctx, imt, psa_df):
    """
    Return the PSA ratio for the given sediment depth, M, rrup and IMT
    """
    breakpoint()