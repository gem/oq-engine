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
Module exports :class:`AtkinsonMacias2009NSHMP2014` and :class:`NSHMP2014`
"""
import numpy as np
import inspect
from openquake.hazardlib import const
from openquake.hazardlib.gsim import base


def nga_west2_epistemic_adjustment(mag, dist):
    """
    Applies the "average" adjustment factor for epistemic uncertainty
    as defined in Table 17 of Petersen et al., (2014)::

                 |  R < 10.  | 10.0 <= R < 30.0  |    R >= 30.0
     -----------------------------------------------------------
       M < 6.0   |   0.37    |      0.22         |       0.22
     6 <= M <7.0 |   0.25    |      0.23         |       0.23
       M >= 7.0  |   0.40    |      0.36         |       0.33
    """
    adjustment = 0.23 * np.ones_like(dist)
    adjustment[(mag < 6.) & (dist < 10.)] = .37
    adjustment[(mag < 6.) & (dist >= 10.)] = .22
    adjustment[(mag >= 6.) & (mag < 7.) & (dist < 10.)] = .25
    adjustment[(mag >= 7.) & (dist < 10.)] = .40
    adjustment[(mag >= 7.) & (dist >= 10.) & (dist < 30.)] = .36
    adjustment[(mag >= 7.) & (dist >= 30.)] = .33
    return adjustment


class NSHMP2014(base.GMPE):
    """
    Implements the NSHMP adjustment factors for the NGA West GMPEs.
    Requires two parameters `gmpe_name` (one of Idriss2014, ChiouYoungs2014,
    CampbellBozorgnia2014, BooreEtAl2014, AbrahamsonEtAl2014) and `sgn`
    (one of -1, 0, +1).
    """
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = ()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ()
    #: REQUIRES_DISTANCES is set at the instance level
    REQUIRES_DISTANCES = frozenset()
    REQUIRES_RUPTURE_PARAMETERS = ()
    REQUIRES_SITES_PARAMETERS = ()

    def __init__(self, gmpe_name, sgn, **kwargs):
        self.gmpe_name = gmpe_name
        self.sgn = sgn
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
        # Add any GMM specific inputs from kwargs
        exp_kwargs = inspect.signature(cls.__init__).parameters.keys()
        for kwarg in kwargs:
            if kwarg not in exp_kwargs: # Prevent silently passing incorrect argument
                raise ValueError(
                    f'{kwarg} is not a recognised argument for {cls.__name__}')
            # Add z1pt0 if basin variant of BSSA14 (usually added 
            # in BSSA14's init method but inherently omitted here)
            if (self.gmpe_name == 'BooreEtAl2014' and kwarg == 'region'
                and kwargs[kwarg] != "nobasin"):
                self.REQUIRES_SITES_PARAMETERS |= {'z1pt0'}
            setattr(self.gsim, kwarg, kwargs[kwarg])
            

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Compute mean, sig, tau, phi and returns the so called adjustment
        """
        self.gsim.compute(ctx, imts, mean, sig, tau, phi)
        adjustment = nga_west2_epistemic_adjustment(ctx.mag, ctx.rrup)
        mean[:] += self.sgn * adjustment
        return adjustment

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
