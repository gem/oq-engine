# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module exports :class:`VanHoutteEtAl2018RSD`
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import RSD575


def get_magnitude_term(C, mag):
    """
    Returns linear magnitude scaling term
    """
    return C["b0"] + C["b1"] * (mag - 6) + C["b2"] * (mag - 6) ** 2


def get_distance_term(C, rrup, mag):
    """
    Returns distance scaling term
    """
    fac = rrup > 100
    rmax100 = rrup.copy()
    rmax100[rmax100 > 100] = 100
    fr = C["b3"] * np.log(np.sqrt(
        rmax100 ** 2 + (np.exp(C["b4"] + C["b5"] * (mag - 6))) ** 2)) + \
        fac * (
        C["b6"] * np.log(np.sqrt(
             rrup ** 2 + (np.exp(C["b4"] + C["b5"] * (mag - 6))) ** 2)) -
        C["b6"] * np.log(np.sqrt(
            100 ** 2 + (np.exp(C["b4"] + C["b5"] * (mag - 6))) ** 2))
        )
    return fr


def get_site_amplification(C, vs30):
    """
    Returns linear site amplification term
    """
    return C["b7"] * np.log(vs30 / 1000)


class VanHoutteEtAl2018RSD(GMPE):
    """
    Implements the GMPE of Van Houtte et al. (2018) for significant duration
    with 5 - 75 % Arias Intensity. doi:10.1785/0120170076. The oscillator
    duration model has not yet been implemented.
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([RSD575])

    #: Supported intensity measure component is RotD50
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are total, inter and intra-event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (get_magnitude_term(C, ctx.mag) +
                       get_distance_term(C, ctx.rrup, ctx.mag) +
                       get_site_amplification(C, ctx.vs30))
            sig[m] = np.sqrt(C["tau"] ** 2. + C["phi"] ** 2.)
            tau[m] = C["tau"]
            phi[m] = C["phi"]

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          b0       b1      b2       b3      b4       b5       b6      b7     tau     phi
    rsd575  -1.7204   0.2272  0.0967   0.8870  2.7641   0.5777   1.1700 -0.1413  0.2270  0.4163
    """)
