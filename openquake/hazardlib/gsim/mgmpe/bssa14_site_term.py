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
Module :mod:`openquake.hazardlib.mgmpe.bssa14_site_term` implements
:class:`~openquake.hazardlib.mgmpe.bss14_site_term.BSSA14SiteTerm`
"""

import copy
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.boore_2014 import (
    _get_pga_on_rock,
    _get_linear_site_term,
    _get_nonlinear_site_term)


def _get_bssa14_site_term(imt, ctx):
    """
    Returns the linear and non-linear site amplification terms of
    the BSSA14 GMM. The basin term is excluded, and we assume the
    user is using the default parameters (kind=base, region="CAL"
    and SoF=True).
    """
    # Get PGA on rock
    C_PGA = BooreEtAl2014.COEFFS[PGA()]
    pga_rock = _get_pga_on_rock(kind="base", 
                                region="CAL",
                                sof=True,
                                C=C_PGA,
                                ctx=ctx)

    # Get coeffs for IMT
    C_IMT = BooreEtAl2014.COEFFS[imt]

    # Get linear component
    flin = _get_linear_site_term(C_IMT, ctx.vs30)
    
    # Get non-linear component
    fnl = _get_nonlinear_site_term(C_IMT, ctx.vs30, pga_rock)
    
    return flin + fnl


class BSSA14SiteTerm(GMPE):
    """
    Implements a modified GMPE class that can be used to account for local
    soil conditions in the estimation of ground motion using the site term
    from :class:`openquake.hazardlib.gsim.boore_2014.BooreEtAl2014`.

    The user should be mindful of ensuring the base GMM was derived for an
    appropriate reference velocity (the BSSA14 site term was developed for a
    reference of 760 m/s).

    The user should also be mindful that the provided basin term is using the
    California region (region="CAL"), the "base" kind (as opposed to the
    "stewart" kind is used) and the SoF is considered (sof=True).

    Lastly, the basin term is not applied here, only the linear and non-linear
    components.

    :param gmpe_name:
        The name of a GMPE class
    """
    # Parameters
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, **kwargs):
        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        # Check if GMM has rake in req rup params + add if missing
        if 'rake' not in self.gmpe.REQUIRES_RUPTURE_PARAMETERS:
            self.REQUIRES_RUPTURE_PARAMETERS |= {'rake'}

        # Check if GMM has vs30 in req site params + add if missing
        if 'vs30' not in self.gmpe.REQUIRES_SITES_PARAMETERS:
            self.REQUIRES_SITES_PARAMETERS |= {'vs30'}

        # Check if GMM has Rjb in req dist params + add if missing
        if 'rjb' not in self.gmpe.REQUIRES_DISTANCES:
            self.REQUIRES_DISTANCES |= {'rjb'}


    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Make sites with ref bedrock vs30
        rup_rock = copy.copy(ctx)
        rup_rock.vs30 = np.full_like(ctx.vs30, 760.)

        # Compute mean on bedrock
        self.gmpe.compute(rup_rock, imts, mean, sig, tau, phi)
        
        # Compute and apply the site term for each IMT
        for m, imt in enumerate(imts):
            mean[m] += _get_bssa14_site_term(imt, ctx)