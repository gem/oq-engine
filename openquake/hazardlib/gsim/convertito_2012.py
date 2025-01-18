# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:'ConvertitoEtAl2012Geysers'
"""
import numpy as np
from scipy.constants import g


from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA


def _compute_magnitude_scaling(C, mag):
    """
    Returns the magnitude scaling term
    """
    return C["a"] + C["b"] * mag


def _compute_distance_scaling(C, rhypo):
    """
    Returns the distance scaling term accounting for geometric and
    anelastic attenuation
    """
    return C["c"] * np.log10(np.sqrt(rhypo ** 2 + C["h"] ** 2)) + (
        C["d"] * rhypo)


def _compute_site_scaling(C, vs30):
    """
    Returns the site scaling term as a simple coefficient
    """
    site_term = np.zeros(len(vs30), dtype=float)
    # For soil sites add on the site coefficient
    site_term[vs30 < 760.0] = C["e"]
    return site_term


class ConvertitoEtAl2012Geysers(GMPE):
    """
    Implements the PGA GMPE for Induced Seismicity in the Geysers Geothermal
    field, published in Convertito, V., Maercklin, N., Sharma, N., and Zollo,
    A. (2012) From Induced Seismicity to Direct Time-Dependent Seismic
    Hazard. Bulletin of the Seismological Society of America, 102(6),
    2563 - 2573
    """
    #: The GMPE is derived from induced earthquakes in the Geysers Geothermal
    #: field
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.GEOTHERMAL

    #: Supported intensity measure types are peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA}

    #: Supported intensity measure component is the larger of two components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = (
        const.IMC.GREATER_OF_TWO_HORIZONTAL)

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters. The GMPE was developed for two site conditions
    #: "with" and "without" site effect. No information is given regarding
    #: the soil conditions, so we assume "with site effect" to correspond
    #: to NEHRP Classes C, D or E (i.e. Vs30 < 760), and "without site effect"
    #: to corresponse to NEHRP Classes A and B (i.e. Vs30 >= 760)
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is hypocentral distance
    REQUIRES_DISTANCES = {'rhypo'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (_compute_magnitude_scaling(C, ctx.mag) +
                       _compute_distance_scaling(C, ctx.rhypo) +
                       _compute_site_scaling(C, ctx.vs30))
            # Original GMPE returns log acceleration in m/s/s
            # Converts to natural logarithm of g
            mean[m] = np.log((10.0 ** mean[m]) / g)
            sig[m] = np.log(10.0 ** C["sigma"])

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT        a      b       c      d    h      e  sigma
    pga   -2.268  1.276  -3.528  0.053  3.5  0.218  0.324
    """)
