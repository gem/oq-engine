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
Module :mod:`openquake.hazardlib.mgmpe.cb14_basin_term` implements
:class:`~openquake.hazardlib.mgmpe.CB14BasinTerm`
"""
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import CampbellBozorgnia2014


def _get_cb14_basin_term(imt, ctx, jpn_flag=False):
    """
    Get the basin response term defined in equation 20 of the Campbell and 
    Bozorgnia (2014) GMM paper.

    Currently the global basin term is provided (i.e. the Japan-regionalised
    basin term is for now turned off).
    """
    C = CampbellBozorgnia2014.COEFFS[imt]
    z2pt5 = ctx.z2pt5
    fb = np.zeros(len(z2pt5))
    idx = z2pt5 < 1.0
    fb[idx] = (C["c14"] + C["c15"] * jpn_flag) * (z2pt5[idx] - 1.0)
    idx = z2pt5 > 3.0
    fb[idx] = C["c16"] * C["k3"] * np.exp(-0.75) * (
        1. - np.exp(-0.25 * (z2pt5[idx] - 3.)))
    
    return fb


class CB14BasinTerm(GMPE):
    """
    Implements a modified GMPE class that can be used to implement the Campbell
    and Bozorgnia (2014) GMM's basin term

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
             mean[m] += _get_cb14_basin_term(imt, ctx)