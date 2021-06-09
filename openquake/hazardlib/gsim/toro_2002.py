# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
Module exports :class:`ToroEtAl2002`, class:`ToroEtAl2002SHARE`.
"""
import numpy as np

from openquake.baselib.performance import jittable
from openquake.hazardlib.gsim.campbell_2003 import _compute_faulting_style_term
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


@jittable
def _compute_term1(C, mag):
    """
    Compute magnitude dependent terms (2nd and 3rd) in equation 3
    page 46.
    """
    mag_diff = mag - 6
    return C['c2'] * mag_diff + C['c3'] * mag_diff ** 2


@jittable
def _compute_term2(C, mag, rjb):
    """
    Compute distance dependent terms (4th, 5th and 6th) in equation 3
    page 46. The factor 'RM' is computed according to the 2002 model
    (equation 4-3).
    """
    RM = np.sqrt(rjb ** 2 + (C['c7'] ** 2) *
                 np.exp(-1.25 + 0.227 * mag) ** 2)

    return -C['c4'] * np.log(RM) - \
        (C['c5'] - C['c4']) * np.maximum(np.log(RM / 100), 0) - C['c6'] * RM


class ToroEtAl2002(GMPE):
    """
    Implements GMPE developed by G. R. Toro, N. A. Abrahamson, J. F. Schneider
    and published in "Model of Strong Ground Motions from Earthquakes in
    Central and Eastern North America: Best Estimates and Uncertainties"
    (Seismological Research Letters, Volume 68, Number 1, 1997) and
    "Modification of the Toro et al. 1997 Attenuation Equations for Large
    Magnitudes and Short Distances" (available at:
    http://www.riskeng.com/downloads/attenuation_equations)
    The class implements equations for Midcontinent, based on moment magnitude.
    SA at 3 and 4 s (not supported by the original equations) have been added
    in the context of the SHARE project and they are obtained from SA at 2 s
    scaled by specific factors for 3 and 4 s.
    """
    #: Supported tectonic region type is stable continental crust,
    #: given that the equations have been derived for central and eastern
    #: north America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see table 2 page 47.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two : horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is rjb, see equation 4, page 46.
    REQUIRES_DISTANCES = {'rjb'}

    #: Coefficient tables obtained by joining tables 2, 3, and 4, pages 47,
    #: 50, 51.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1    c2    c3    c4    c5    c6       c7   m50   m55   m80   r5    r20
    pga    2.20  0.81  0.00  1.27  1.16  0.0021   9.3  0.55  0.59  0.50  0.54  0.20
    0.03   4.00  0.79  0.00  1.57  1.83  0.0008  11.1  0.62  0.63  0.50  0.62  0.35
    0.04   3.68  0.80  0.00  1.46  1.77  0.0013  10.5  0.62  0.63  0.50  0.57  0.29
    0.10   2.37  0.81  0.00  1.10  1.02  0.0040   8.3  0.59  0.61  0.50  0.50  0.17
    0.20   1.73  0.84  0.00  0.98  0.66  0.0042   7.5  0.60  0.64  0.56  0.45  0.12
    0.40   1.07  1.05 -0.10  0.93  0.56  0.0033   7.1  0.63  0.68  0.64  0.45  0.12
    1.00   0.09  1.42 -0.20  0.90  0.49  0.0023   6.8  0.63  0.64  0.67  0.45  0.12
    2.00  -0.74  1.86 -0.31  0.92  0.46  0.0017   6.9  0.61  0.62  0.66  0.45  0.12
    3.00  -0.74  1.86 -0.31  0.92  0.46  0.0017   6.9  0.61  0.62  0.66  0.45  0.12
    4.00  -0.74  1.86 -0.31  0.92  0.46  0.0017   6.9  0.61  0.62  0.66  0.45  0.12
    """)

    @jittable
    def get_mean(param, sites, C):
        """
        Compute mean value according to equation 3, page 46.
        """
        mag, rjb = param['mag'], sites['rjb']
        mean = (C['c1'] + _compute_term1(C, mag) + _compute_term2(C, mag, rjb))

        # apply decay factor for 3 and 4 seconds (not originally supported
        # by the equations)
        if C['period'] == 3.0:
            mean /= 0.612
        if C['period'] == 4.0:
            mean /= 0.559
        return mean

    @jittable
    def get_stdt(param, sites, C):
        mag, rjb = param['mag'], sites['rjb']

        # aleatory uncertainty
        sigma_ale_m = np.interp(
            mag, [5.0, 5.5, 8.0],
            [C['m50'], C['m55'], C['m80']])
        sigma_ale_rjb = np.interp(
            rjb, [5.0, 20.0], [C['r5'], C['r20']])
        sigma_ale = np.sqrt(sigma_ale_m ** 2 + sigma_ale_rjb ** 2)

        # epistemic uncertainty
        sigma_epi = (0.36 + 0.07 * (mag - 6) if C["period"] < 1
                     else 0.34 + 0.06 * (mag - 6))
        sigma_total = np.sqrt(sigma_ale ** 2 + sigma_epi ** 2)
        return sigma_total

    @jittable
    def get_stds(param, sites, C):
        sigma_total = ToroEtAl2002.get_stdt(param, sites, C)
        return [sigma_total, sigma_total]


#: Constants for faulting style adjustment
CONSTS_FS = {'Fnss': 0.95, 'pN': 0.01, 'pR': 0.81}


class ToroEtAl2002SHARE(ToroEtAl2002):

    #: Required rupture parameters are magnitude and rake
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 800.

    #: Coefficients for faulting style and rock adjustment
    COEFFS_FS_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT    Frss      AFrock
    pga    1.220000  0.735106
    0.03   1.179400  0.423049
    0.04   1.164000  0.477379
    0.10   1.080000  0.888509
    0.20   1.190000  1.197291
    0.40   1.230000  1.308267
    1.00   1.196667  1.265762
    2.00   1.140000  1.215779
    3.00   1.140000  1.215779
    4.00   1.140000  1.215779
    """)

    @jittable
    def get_mean(param, sites, C, C_ADJ):
        mean = ToroEtAl2002.get_mean(param, sites, C)
        # apply faulting style and rock adjustment factor for mean
        mean[:] = np.log(np.exp(mean) * _compute_faulting_style_term(
            C_ADJ['Frss'], CONSTS_FS['pR'], CONSTS_FS['Fnss'],
            CONSTS_FS['pN'], param['rake']) * C_ADJ['AFrock'])
        return mean
