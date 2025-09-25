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
Module :mod:`openquake.hazardlib.mgmpe.cy14_site_term` implements
:class:`~openquake.hazardlib.mgmpe.cy14_site_term.CY14SiteTerm`
"""

import copy
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014


def _get_cy14_site_term(C, vs30, ln_y_ref):
    """
    Applies the linear and nonlinear site amplification term of Chiou &
    Youngs (2014) (excluding the basin amplification term)
    """
    y_ref = np.exp(ln_y_ref)
    exp1 = np.exp(C['phi3'] * (vs30.clip(-np.inf, 1130) - 360))
    exp2 = np.exp(C['phi3'] * (1130 - 360))
    af = (C['phi1'] * np.log(vs30 / 1130).clip(-np.inf, 0) +
          C['phi2'] * (exp1 - exp2) *
          np.log((y_ref + C['phi4']) / C['phi4']))
    return af


class CY14SiteTerm(GMPE):
    """
    Implements a modified GMPE class that can be used to account for local
    soil conditions in the estimation of ground motion using the site term
    from :class:`openquake.hazardlib.gsim.chiou_youngs_2014.ChiouYoungs2014`.
    The CY14SiteTerm can be applied to any GMPE that natively uses the vs30
    parameter or, if vs30 is not used, the GMPE must specify a reference
    velocity (i.e. DEFINED_FOR_REFERENCE_VELOCITY) between 1100 and 1160m/s.

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
        self.gmpe = registry[gmpe_name]()
        self.set_parameters()
        #
        # Check if this GMPE has the necessary requirements
        if not (hasattr(self.gmpe, 'DEFINED_FOR_REFERENCE_VELOCITY') or
                'vs30' in self.gmpe.REQUIRES_SITES_PARAMETERS):
            msg = '{:s} does not use vs30 nor a defined reference velocity'
            raise AttributeError(msg.format(str(self.gmpe)))
        if 'vs30' not in self.gmpe.REQUIRES_SITES_PARAMETERS:
            self.REQUIRES_SITES_PARAMETERS = frozenset(
                self.gmpe.REQUIRES_SITES_PARAMETERS | {'vs30'})
        #
        # Check compatibility of reference velocity
        if not hasattr(self.gmpe, 'DEFINED_FOR_REFERENCE_VELOCITY'):
            fmt = 'The original GMPE must have the {:s} parameter'
            msg = fmt.format('DEFINED_FOR_REFERENCE_VELOCITY')
            raise ValueError(msg)
        if not (self.gmpe.DEFINED_FOR_REFERENCE_VELOCITY >= 1100 and
                self.gmpe.DEFINED_FOR_REFERENCE_VELOCITY <= 1160):
            msg = 'DEFINED_FOR_REFERENCE_VELOCITY outside of range'
            raise ValueError(msg)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Prepare sites
        rup_rock = copy.copy(ctx)
        rup_rock.vs30 = np.full_like(ctx.vs30, 1130.)

        # Compute mean and standard deviation using the original GMM. These
        # values are used as ground-motion values on reference rock conditions.
        # CHECKED [MP]: The computed reference motion is equal to the one in
        # the CY14 model
        self.gmpe.compute(rup_rock, imts, mean, sig, tau, phi)

        # Compute the site term correction factor for each IMT
        vs30 = ctx.vs30.copy()
        for m, imt in enumerate(imts):
            C = ChiouYoungs2014.COEFFS[imt]
            mean[m] += _get_cy14_site_term(C, vs30, mean[m])
