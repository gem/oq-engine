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
Module exports :class:`SomervilleEtAl2001NSHMP2008`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.utils import clip_mean
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_mean(C, mag, rjb):
    """
    Compute and return mean value (table 8, page 8)
    """
    d1 = np.sqrt(50. ** 2 + 6. ** 2)
    d = np.sqrt(rjb ** 2 + 6 ** 2)

    mean = np.zeros_like(rjb)

    mean += (
        C['a1'] + C['a2'] * (mag - 6.4) +
        C['a7'] * (8.5 - mag) ** 2
    )

    idx = rjb < 50.
    mean[idx] += (
        C['a3'] * np.log(d[idx]) +
        C['a4'] * (mag[idx] - 6.4) * np.log(d[idx]) +
        C['a5'] * rjb[idx]
    )

    idx = rjb >= 50.
    mean[idx] += (
        C['a3'] * np.log(d1) +
        C['a4'] * (mag[idx] - 6.4) * np.log(d[idx]) +
        C['a5'] * rjb[idx] + C['a6'] * (np.log(d[idx]) - np.log(d1))
    )

    return mean


class SomervilleEtAl2001NSHMP2008(GMPE):
    """
    Implements GMPE developed by P. Somerville, N. Collins, N. Abrahamson,
    R. Graves, and C. Saika and documented in "GROUND MOTION ATTENUATION
    RELATIONS FOR THE CENTRAL AND EASTERN UNITED STATES" (Final report, June
    30, 2001: Report to U.S. Geological Survey for award 99HQGR0098). This GMPE
    is used by the National Seismic Hazard Mapping Project (NSHMP) for the 2008
    US hazard model.

    Document available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2002/99HQGR0098.pdf

    This class replicates the algorithm for the Somerville et. al. 2001 GMPE as
    coded in the subroutine ``getSomer`` in the ``hazgridXnga2.f``
    Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/

    Coefficients are given for the B/C site conditions.
    """
    #: Supported tectonic region type is stable continental crust,
    #: given that the equations have been derived for central and eastern
    #: north America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two : horizontal components
    #: attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude (Mw).
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is rjb
    REQUIRES_DISTANCES = {'rjb'}

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = clip_mean(imt, _compute_mean(C, ctx.mag, ctx.rjb))
            sig[m] = C['sigma']

    #: Coefficient table obtained from coefficient arrays (a1, a2, a3, a4,
    #: a5, a6, a7, sig0) defined in subroutine getSomer in hazgridXnga2.f
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    a1      a2      a3        a4       a5           a6         a7         sigma
    pga    0.658   0.805  -0.679     0.0861  -0.00498     -0.477      0.0        0.587
    0.1    1.442   0.805  -0.679     0.0861  -0.00498     -0.477      0.0        0.595
    0.2    1.358   0.805  -0.679     0.0861  -0.00498     -0.477      0.0        0.611
    0.3    1.2353  0.805  -0.67023   0.0861  -0.0048045   -0.523792  -0.030298   0.6057
    0.5    0.8532  0.805  -0.671792  0.0861  -0.00442189  -0.605213  -0.0640237  0.6242
    1.0   -0.0143  0.805  -0.696     0.0861  -0.00362     -0.755     -0.102      0.693
    2.0   -0.9497  0.805  -0.728     0.0861  -0.00221     -0.946     -0.140      0.824
    """)
