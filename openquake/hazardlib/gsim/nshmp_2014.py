# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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
Module exports :class:`AtkinsonMacias2009NSHMP2014` and :class:`NSHMP2014`
"""
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim import base


def nga_west2_epistemic_adjustment(magnitude, distance):
    """
    Applies the "average" adjustment factor for epistemic uncertainty
    as defined in Table 17 of Petersen et al., (2014)::

                 |  R < 10.  | 10.0 <= R < 30.0  |    R >= 30.0
     -----------------------------------------------------------
       M < 6.0   |   0.37    |      0.22         |       0.22
     6 <= M <7.0 |   0.25    |      0.23         |       0.23
       M >= 7.0  |   0.40    |      0.36         |       0.33
    """
    if magnitude < 6.0:
        adjustment = 0.22 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.37
    elif magnitude >= 7.0:
        adjustment = 0.36 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.40
        adjustment[distance >= 30.0] = 0.33
    else:
        adjustment = 0.23 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.25
    return adjustment


class NSHMP2014(base.GMPE):
    """
    Implements the NSHMP adjustment factors for the NGA West GMPEs.
    Requires two parameters `gmpe_name` (one of Idriss2014, ChiouYoungs2014,
    CampbellBozorgnia2014, BooreEtAl2014, AbrahamsonEtAl2014) and `sgn`
    (one of -1, 0, +1).
    """
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = ()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ()
    REQUIRES_DISTANCES = ()
    REQUIRES_RUPTURE_PARAMETERS = ()
    REQUIRES_SITES_PARAMETERS = ()

    def __init__(self, **kwargs):
        self.gmpe_name = kwargs['gmpe_name']
        self.sgn = kwargs['sgn']
        if self.sgn == 0:
            # default weighting
            self.weights_signs = [(0.185, -1.), (0.63, 0.), (0.185, 1.)]
        cls = base.registry[self.gmpe_name]
        for name in vars(cls):
            if name.startswith(('DEFINED_FOR', 'REQUIRES_')):
                setattr(self, name, getattr(cls, name))
        # the gsim requires only Rjb, but the epistemic adjustment factors
        # are given in terms of Rrup, so both are required in the subclass
        self.REQUIRES_DISTANCES = frozenset(self.REQUIRES_DISTANCES | {'rrup'})
        self.gsim = cls()  # underlying gsim
        super().__init__(**kwargs)

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        self.gsim.compute(ctx, imts, mean, sig, tau, phi)
        ctx.adjustment = nga_west2_epistemic_adjustment(ctx.mag, ctx.rrup)
        mean[:] += self.sgn * ctx.adjustment


# populate gsim_aliases
# for instance "AbrahamsonEtAl2014NSHMPMean" is associated to the TOML string
# [NSHMP2014]
# gmpe_name = "AbrahamsonEtAl2014"
# sgn = 0
SUFFIX = {0: 'Mean', -1: 'Lower', 1: 'Upper'}
for name in ('Idriss2014', 'ChiouYoungs2014', 'CampbellBozorgnia2014',
             'BooreEtAl2014', 'AbrahamsonEtAl2014'):
    for sgn in (1, -1, 0):
        a = name + 'NSHMP' + SUFFIX[sgn]
        base.add_alias(a, NSHMP2014, gmpe_name=name, sgn=sgn)
