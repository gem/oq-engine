# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
Module exports :class:`Geomatrix1993SSlabNSHMP2008`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_mean(C, mag, ztor, rrup):
    """
    Compute mean value as in ``subroutine getGeom`` in ``hazgridXnga2.f``
    """
    gc0 = 0.2418
    ci = 0.3846
    gch = 0.00607
    g4 = 1.7818
    ge = 0.554
    gm = 1.414

    mean = (
        gc0 + ci + ztor * gch + C['gc1'] +
        gm * mag + C['gc2'] * (10 - mag) ** 3 +
        C['gc3'] * np.log(rrup + g4 * np.exp(ge * mag)))

    return mean


class Geomatrix1993SSlabNSHMP2008(GMPE):
    """
    Implements GMPE for subduction intraslab events developed by Geomatrix
    Consultants, Inc., 1993, "Seismic margin earthquake for the Trojan site:
    Final unpublished report prepared for Portland General Electric Trojan
    Nuclear Plant", Ranier, Oregon.

    This class implements the equation as coded in the subroutine ``getGeom``
    in the ``hazgridXnga2.f`` Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/

    Coefficients are given for the B/C site conditions.
    """
    #: Supported tectonic region type is subduction intraslab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}

    #: Required distance measure is rrup (closest distance to rupture)
    REQUIRES_DISTANCES = {'rrup'}

    # Shear-wave velocity for reference soil conditions in [m s-1])
    REQUIRES_SITES_PARAMETERS = set()
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, ctx.mag, ctx.ztor, ctx.rrup)
            sig[m] =  C['gc4'] + C['gc5'] * np.minimum(8., ctx.mag)

    #: Coefficient table obtained from coefficient arrays and variables
    #: defined in subroutine getGeom in hazgridXnga2.f
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT   gc1      gc2      gc3      gc4    gc5
    pga   0.0      0.0     -2.556    1.45  -0.1
    0.1   1.1880  -0.0011  -2.6550   1.45  -0.1
    0.2   0.722   -0.0027  -2.528    1.45  -0.1
    0.3   0.246   -0.0036  -2.454    1.45  -0.1
    0.5  -0.4     -0.0048  -2.36     1.45  -0.1
    1.0  -1.736   -0.0064  -2.234    1.45  -0.1
    2.0  -3.3280  -0.0080  -2.107    1.55  -0.1
    3.0  -4.511   -0.0089  -2.033    1.65  -0.1
    """)
