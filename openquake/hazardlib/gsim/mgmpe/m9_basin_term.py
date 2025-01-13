# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.hazardlib.mgmpe.m9_basin_term` implements
:class:`~openquake.hazardlib.mgmpe.M9BasinTerm`
"""
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry


def _apply_m9_basin_term(ctx, imt, mean):
    if imt.period > 1.9: # Only apply to long-period SA
        fb_m9 = np.log(2.0)
        idx = ctx.z2pt5 >= 6.0 # Apply only to sites with z2pt5 >= 6
        mean[idx] += fb_m9
            
    return mean


class M9BasinTerm(GMPE):
    """
    Implements a modified GMPE class that can be used to implement the "M9"
    US 2023 NSHM basin amplification adjustment (an additive factor for long
    period ground-motions in the Seattle Basin region).
     
    This implementation is based on the description of the M9 adjustment 
    within the Moschetti et al. (2024) EQ Spectra article on the conterminous
    US 2023 NSHM GMC (pp. 1178).

    :param gmpe_name:
        The name of a GMPE class
    """
    # Req Params
    REQUIRES_SITES_PARAMETERS = {'z2pt5'}

    # Others are set from underlying GMM
    REQUIRES_DISTANCES = set() 
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, **kwargs):
        self.gmpe = registry[gmpe_name]()
        self.set_parameters()    
        
        # Need z2pt5 in req site params to ensure in ctx site col 
        if 'z2pt5' not in self.gmpe.REQUIRES_SITES_PARAMETERS:
            self.REQUIRES_SITES_PARAMETERS = frozenset(
                self.gmpe.REQUIRES_SITES_PARAMETERS | {'z2pt5'})

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):      
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        self.gmpe.compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
             mean[m] = _apply_m9_basin_term(ctx, imt, mean[m])