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
Module exports :class:'DostEtAl2004'
"""
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV


def _compute_distance_term(C, rhypo):
    """
    Returns the distance scaling term
    """
    return (C["c2"] * rhypo) + (C["c3"] * np.log10(rhypo))


_compute_magnitude_term = CallableDict()


@_compute_magnitude_term.add("base")
def _compute_magnitude_term_1(kind, C, mag):
    """
    Returns the magnitude scaling term
    """
    return C["c0"] + (C["c1"] * mag)


@_compute_magnitude_term.add("bommer")
def _compute_magnitude_term_2(kind, C, mag):
    """
    Returns the magnitude scaling term
    """
    return C["c0"] + C["c1"] * mag + C["c1e"] * (mag - 4.5) ** 2


class DostEtAl2004(GMPE):
    """
    Implements the GMPE of Dost et al. (2004) for PGA and PGV from
    induced seismicity earthquakes in the Netherlands
    Dost, B., van Eck, T. and Haak, H. (2004) Scaling of peak ground
    acceleration and peak ground velocity recorded in the Netherlands.
    Bollettino di Geofisica Teorica ed Applicata. 45(3), 153 - 168
    """
    kind = "base"

    #: The GMPE is derived from induced earthquakes
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.INDUCED

    #: Supported intensity measure types are peak ground acceleration
    #: and peak ground velocity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV}

    #: Supported intensity measure component is the average horizontal
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotD100

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No required site parameters
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude (ML is used)
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
            imean = (_compute_magnitude_term(self.kind, C, ctx.mag) +
                     _compute_distance_term(C, ctx.rhypo))
            # Convert mean from cm/s and cm/s/s
            if imt.string == "PGA":
                mean[m] = np.log(10.0 ** imean / g)
            else:
                mean[m] = np.log(10.0 ** imean)

            sig[m] = np.log(10.0 ** C["sigma"])
            if self.kind == "bommer":
                tau[m] = np.log(10.0 ** C["tau"])
                phi[m] = np.log(10.0 ** C["phi"])

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     c0     c1        c2      c3   sigma
    pgv  -1.53   0.74  -0.00139   -1.33    0.33
    pga  -1.41   0.57  -0.00139   -1.33    0.33
    """)


class DostEtAl2004BommerAdaptation(DostEtAl2004):
    """
    Adaptation of the GMPE for application to higher magnitudes proposed
    by Bommer et al. (2013)
    """
    kind = "bommer"

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     c0         c1       c1e         c2      c3     tau     phi  sigma
    pgv  -1.3972   0.7105   -0.0829   -0.00139   -1.33  0.1476  0.2952   0.33
    pga  -1.6090   0.6140   -0.1116   -0.00139   -1.33  0.1476  0.2952   0.33
    """)
