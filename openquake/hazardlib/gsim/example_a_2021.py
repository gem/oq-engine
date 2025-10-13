# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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

import numpy as np
from openquake.baselib.performance import jittable
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


@jittable
def _compute_term1(C, mag):
    mag_diff = mag - 6
    return C['c2'] * mag_diff + C['c3'] * mag_diff ** 2


@jittable
def _compute_term2(C, mag, rjb):
    RM = np.sqrt(rjb ** 2 + (C['c7'] ** 2) *
                 np.exp(-1.25 + 0.227 * mag) ** 2)
    res = (-C['c4'] * np.log(RM) - (C['c5'] - C['c4']) *
           np.maximum(np.log(RM / 100), 0) - C['c6'] * RM)
    return res


class ExampleA2021(GMPE):
    """
    Mimic ToroEtAl2002
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}
    #: Required distance rjb
    REQUIRES_DISTANCES = {'rjb'}

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

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        mag, rjb = ctx.mag, ctx.rjb
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (C['c1'] + _compute_term1(C, mag) +
                       _compute_term2(C, mag, rjb))
            if imt.period == 3.0:
                mean[m] /= 0.612
            elif imt.period == 4.0:
                mean[m] /= 0.559

            sigma_ale_m = np.interp(
                mag, [5.0, 5.5, 8.0],
                [C['m50'], C['m55'], C['m80']])
            sigma_ale_rjb = np.interp(
                rjb, [5.0, 20.0], [C['r5'], C['r20']])
            sigma_ale = np.sqrt(sigma_ale_m ** 2 + sigma_ale_rjb ** 2)
            sigma_epi = (0.36 + 0.07 * (mag - 6) if imt.period < 1
                         else 0.34 + 0.06 * (mag - 6))
            sig[m] = np.sqrt(sigma_ale ** 2 + sigma_epi ** 2)
