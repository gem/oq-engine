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
Module exports :class:`ToroEtAl1997MblgNSHMP2008`,
:class:`ToroEtAl1997MwNSHMP2008`
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_johnston_96, mblg_to_mw_atkinson_boore_87, clip_mean)
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.baselib.general import CallableDict

_compute_finite_fault_correction = CallableDict()


@_compute_finite_fault_correction.add("Mblg")
def _compute_finite_fault_correction_Mblg(kind, mag):
    """
    Compute finite fault correction term as geometric mean of correction
    terms obtained from Mw values calculated with Johnston 1996 and
    Atkinson and Boore 1987 conversion equations.

    Implement equations as in lines 1653 - 1658 in hazgridXnga2.f
    """
    mw_j96 = mblg_to_mw_johnston_96(mag)
    mw_ab87 = mblg_to_mw_atkinson_boore_87(mag)

    t1 = np.exp(-1.25 + 0.227 * mw_j96)
    t2 = np.exp(-1.25 + 0.227 * mw_ab87)

    return np.sqrt(t1 * t2)


@_compute_finite_fault_correction.add("Mw")
def _compute_finite_fault_correction_Mw(kind, mag):
    """
    Compute finite fault correction term.
    """
    return np.exp(-1.25 + 0.227 * mag)


def _compute_mean(kind, C, mag, rjb):
    """
    Compute ground motion mean value.
    """
    # line 1686 in hazgridXnga2.f
    ffc = _compute_finite_fault_correction(kind, mag)
    d = np.sqrt(rjb ** 2 + (C['c7'] ** 2) * (ffc ** 2))

    # lines 1663, 1694-1696 in hazgridXnga2.f
    mean = (C['c1'] + C['c2'] * (mag - 6.) +
            C['c3'] * ((mag - 6.) ** 2) -
            C['c4'] * np.log(d) - C['c6'] * d)

    factor = np.log(rjb / 100.)
    idx = factor > 0
    mean[idx] -= (C['c5'] - C['c4']) * factor[idx]

    return mean


class ToroEtAl1997MblgNSHMP2008(GMPE):
    """
    Implements GMPE developed by G. R. Toro, N. A. Abrahamson, J. F. Schneider
    and published in "Model of Strong Ground Motions from Earthquakes in
    Central and Eastern North America: Best Estimates and Uncertainties"
    (Seismological Research Letters, Volume 68, Number 1, 1997) as utilized
    by the National Seismic Hazard Mapping Project (NSHMP) for the 2008 US
    hazard model.

    This class replicates the algorithm for the Toro et. al. 1997 GMPE as
    coded in the subroutine ``getToro`` in the ``hazgridXnga2.f``
    Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/

    The class assumes rupture magnitude to be in Mblg scale (given that
    MFDs for central and eastern US are given in this scale).
    The equation implements also the finite-fault correction as given in
    "Modification of the Toro et al. 1997 Attenuation Equations for Large
    Magnitudes and Short Distances" (available at:
    http://www.riskeng.com/downloads/attenuation_equations). The correction
    uses Mw. Therefore Mblg is converted to Mw using both the Atkinson & Boore
    1987 and Johnston 1996 conversion equations and an average correction term
    is computed.

    Coefficients are given for the B/C site conditions.
    """
    kind = "Mblg"

    #: Supported tectonic region type is stable continental crust,
    #: given that the equations have been derived for central and eastern
    #: north America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude (Mblg).
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
            mean[m] = clip_mean(
                imt, _compute_mean(self.kind, C, ctx.mag, ctx.rjb))
            sig[m] = C['sigma']

    #: Coefficient table obtained from coefficient arrays (tb1, tb2, tb3, tb4,
    #: tb5, tb6, tbh) defined from line 1596 - 1614 in hazgridXnga2.f
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1      c2      c3      c4    c5      c6       c7   sigma
    pga    2.489   1.20    0.0     1.28  1.23    0.0018   9.3  0.7506
    0.1    2.91    1.23    0.0     1.12  1.05    0.0043   8.5  0.7506
    0.2    2.165   1.24    0.0     0.98  0.74    0.0039   7.5  0.7506
    0.3    1.7323  1.51   -0.11    0.96  0.6881  0.0034   7.35 0.7506
    0.5    1.109   1.785  -0.2795  0.93  0.6354  0.002732 7.05 0.7506
    1.0    0.173   2.05   -0.34    0.90  0.59    0.0019   6.8  0.799
    2.0   -0.788   2.52   -0.47    0.93  0.6     0.0012   7.0  0.799
    """)


class ToroEtAl1997MwNSHMP2008(ToroEtAl1997MblgNSHMP2008):
    """
    Extend :class:`ToroEtAl1997MblgNSHMP2008` but assumes magnitude to be in
    Mw scale.

    Coefficients are Mw-specific and no magnitude conversion is considered to
    take into account finite-fault correction.
    """
    kind = "Mw"

    #: Coefficient table obtained from coefficient arrays (tc1, tc2, tc3, tc4,
    #: tc5, tc6, th) defined in subroutine getToro in hazgridXnga2.f
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1      c2      c3      c4      c5      c6       c7     sigma
    pga    2.619   0.81    0.0     1.27    1.16    0.0021   9.3    0.7506
    0.1    2.92    0.81    0.0     1.1     1.02    0.004    8.3    0.7506
    0.2    2.295   0.84    0.0     0.98    0.66    0.0042   7.5    0.7506
    0.3    1.8823  0.964  -0.059   0.951   0.601   0.00367  7.26   0.7506
    0.5    1.2887  1.14   -0.1244  0.9227  0.5429  0.00306  7.027  0.7506
    1.0    0.383   1.42   -0.2     0.90    0.49    0.0023   6.8    0.799
    2.0   -0.558   1.86   -0.31    0.92    0.46    0.0017   6.9    0.799
    """)
