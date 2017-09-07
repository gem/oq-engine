# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
Module exports :class:`AbrahamsonSilva1997`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class AbrahamsonSilva1997(GMPE):
    """
    Implements GMPE developed by N. A. Abrahamson and W. J. Silva and published
    as "Empirical Response Spectral Attenuation Relations for Shallow Crustal
    Earthquakes", Seismological Research Letters, v.68, no. 1, p. 94-127, 1997.

    The GMPE distinguishes between rock (vs30 >= 600) and deep soil
    (vs30 < 600). The rake angle is also taken into account to distinguish
    between 'reverse' (45 <= rake < 135) and 'other'. If an earthquake rupture
    is classified as 'reverse', then the hanging-wall term is included in the
    mean calculation.
    """
    #: Supported tectonic region type is 'active shallow crust' (see
    #: Introduction, page 94)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are PGA and SA. PGA is assumed to
    #: have same coefficients as SA(0.01)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components (see paragraph 'Regression Model', page 105)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is Total (see equations 13 pp. 106
    #: and table 4, page 109).
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: The only site parameter is vs30 used to distinguish between rock
    #: (vs30 > 600 m/s) and deep soil (see table 2, page 95)
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and rake (eq. 3, page 105).
    #: Rake is used to distinguish between 'reverse' (45 <= rake <= 135) and
    #: 'other' (i.e. strike-slip and normal). If an earthquake is classified
    #: as 'reverse' than the hanging-wall term is taken into account.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Required distance measure is RRup (eq. 3, page 105).
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        F, HW = self._get_fault_type_hanging_wall(rup.rake)
        S = self._get_site_class(sites.vs30)

        # compute pga on rock (used then to compute site amplification factor)
        C = self.COEFFS[PGA()]
        pga_rock = np.exp(
            self._compute_mean_on_rock(C, rup.mag, dists.rrup, F, HW)
        )

        # compute mean for the given imt (do not repeat the calculation if
        # imt is PGA, just add the site amplification term)
        if imt == PGA():
            mean = np.log(pga_rock) + S * self._compute_f5(C, pga_rock)
        else:
            C = self.COEFFS[imt]
            mean = (
                self._compute_mean_on_rock(C, rup.mag, dists.rrup, F, HW) +
                S * self._compute_f5(C, pga_rock)
            )

        C_STD = self.COEFFS_STD[imt]
        stddevs = self._get_stddevs(
            C_STD, rup.mag, stddev_types, sites.vs30.size
        )

        return mean, stddevs

    def _compute_mean_on_rock(self, C, mag, rrup, F, HW):
        """
        Compute mean value on rock (that is eq.1, page 105 with S = 0)
        """
        f1 = self._compute_f1(C, mag, rrup)
        f3 = self._compute_f3(C, mag)
        f4 = self._compute_f4(C, mag, rrup)

        return f1 + F * f3 + HW * f4

    def _get_stddevs(self, C, mag, stddev_types, num_sites):
        """
        Return standard deviation as defined in eq.13 page 106.
        """
        std = np.zeros(num_sites)

        if mag <= 5:
            std += C['b5']
        elif 5.0 < mag < 7.0:
            std += C['b5'] - C['b6'] * (mag - 5)
        else:
            std += C['b5'] - 2 * C['b6']

        # only the 'total' standard deviation is supported, therefore the
        # std is always the same for all types
        stddevs = [std for _ in stddev_types]

        return stddevs

    def _get_fault_type_hanging_wall(self, rake):
        """
        Return fault type (F) and hanging wall (HW) flags depending on rake
        angle.

        The method assumes 'reverse' (F = 1) if 45 <= rake <= 135, 'other'
        (F = 0) if otherwise. Hanging-wall flag is set to 1 if 'reverse',
        and 0 if 'other'.
        """
        F, HW = 0, 0

        if 45 <= rake <= 135:
            F, HW = 1, 1

        return F, HW

    def _get_site_class(self, vs30):
        """
        Return site class flag (0 if vs30 > 600, that is rock, or 1 if vs30 <
        600, that is deep soil)
        """
        S = np.zeros_like(vs30)
        S[vs30 < 600] = 1

        return S

    def _compute_f1(self, C, mag, rrup):
        """
        Compute f1 term (eq.4, page 105)
        """
        r = np.sqrt(rrup ** 2 + C['c4'] ** 2)

        f1 = (
            C['a1'] +
            C['a12'] * (8.5 - mag) ** C['n'] +
            (C['a3'] + C['a13'] * (mag - C['c1'])) * np.log(r)
        )

        if mag <= C['c1']:
            f1 += C['a2'] * (mag - C['c1'])
        else:
            f1 += C['a4'] * (mag - C['c1'])

        return f1

    def _compute_f3(self, C, mag):
        """
        Compute f3 term (eq.6, page 106)

        NOTE: In the original manuscript, for the case 5.8 < mag < c1,
        the term in the numerator '(mag - 5.8)' is missing, while is
        present in the software used for creating the verification tables
        """
        if mag <= 5.8:
            return C['a5']
        elif 5.8 < mag < C['c1']:
            return (
                C['a5'] +
                (C['a6'] - C['a5']) * (mag - 5.8) / (C['c1'] - 5.8)
            )
        else:
            return C['a6']

    def _compute_f4(self, C, mag, rrup):
        """
        Compute f4 term (eq. 7, 8, and 9, page 106)
        """
        fhw_m = 0
        fhw_r = np.zeros_like(rrup)

        if mag <= 5.5:
            fhw_m = 0
        elif 5.5 < mag < 6.5:
            fhw_m = mag - 5.5
        else:
            fhw_m = 1

        idx = (rrup > 4) & (rrup <= 8)
        fhw_r[idx] = C['a9'] * (rrup[idx] - 4.) / 4.

        idx = (rrup > 8) & (rrup <=18)
        fhw_r[idx] = C['a9']

        idx = (rrup > 18) & (rrup <= 24)
        fhw_r[idx] = C['a9'] * (1 - (rrup[idx] - 18.) / 7.)

        return fhw_m * fhw_r

    def _compute_f5(self, C, pga_rock):
        """
        Compute f5 term (non-linear soil response)
        """
        return C['a10'] + C['a11'] * np.log(pga_rock + C['c5'])

    #: Coefficient table (table 3, page 108)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt    c4     a1     a2      a3       a4     a5      a6     a9      a10     a11     a12     a13   c1   c5    n
    pga    5.60   1.640  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.417  -0.230   0.0000  0.17  6.4  0.03  2
    0.01   5.60   1.640  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.417  -0.230   0.0000  0.17  6.4  0.03  2
    0.02   5.60   1.640  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.417  -0.230   0.0000  0.17  6.4  0.03  2
    0.03   5.60   1.690  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.470  -0.230   0.0143  0.17  6.4  0.03  2
    0.04   5.60   1.780  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.555  -0.251   0.0245  0.17  6.4  0.03  2
    0.05   5.60   1.870  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.620  -0.267   0.0280  0.17  6.4  0.03  2
    0.06   5.60   1.940  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.665  -0.280   0.0300  0.17  6.4  0.03  2
    0.075  5.58   2.037  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.628  -0.280   0.0300  0.17  6.4  0.03  2
    0.09   5.54   2.100  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.609  -0.280   0.0300  0.17  6.4  0.03  2
    0.10   5.50   2.160  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.598  -0.280   0.0280  0.17  6.4  0.03  2
    0.12   5.39   2.272  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.591  -0.280   0.0180  0.17  6.4  0.03  2
    0.15   5.27   2.407  0.512  -1.1450  -0.144  0.610   0.260  0.370  -0.577  -0.280   0.0050  0.17  6.4  0.03  2
    0.17   5.19   2.430  0.512  -1.1350  -0.144  0.610   0.260  0.370  -0.522  -0.265  -0.0040  0.17  6.4  0.03  2
    0.20   5.10   2.406  0.512  -1.1150  -0.144  0.610   0.260  0.370  -0.445  -0.245  -0.0138  0.17  6.4  0.03  2
    0.24   4.97   2.293  0.512  -1.0790  -0.144  0.610   0.232  0.370  -0.350  -0.223  -0.0238  0.17  6.4  0.03  2
    0.30   4.80   2.114  0.512  -1.0350  -0.144  0.610   0.198  0.370  -0.219  -0.195  -0.0360  0.17  6.4  0.03  2
    0.36   4.62   1.955  0.512  -1.0052  -0.144  0.610   0.170  0.370  -0.123  -0.173  -0.0460  0.17  6.4  0.03  2
    0.40   4.52   1.860  0.512  -0.9880  -0.144  0.610   0.154  0.370  -0.065  -0.160  -0.0518  0.17  6.4  0.03  2
    0.46   4.38   1.717  0.512  -0.9652  -0.144  0.592   0.132  0.370   0.020  -0.136  -0.0594  0.17  6.4  0.03  2
    0.50   4.30   1.615  0.512  -0.9515  -0.144  0.581   0.119  0.370   0.085  -0.121  -0.0635  0.17  6.4  0.03  2
    0.60   4.12   1.428  0.512  -0.9218  -0.144  0.557   0.091  0.370   0.194  -0.089  -0.0740  0.17  6.4  0.03  2
    0.75   3.90   1.160  0.512  -0.8852  -0.144  0.528   0.057  0.331   0.320  -0.050  -0.0862  0.17  6.4  0.03  2
    0.85   3.81   1.020  0.512  -0.8648  -0.144  0.512   0.038  0.309   0.370  -0.028  -0.0927  0.17  6.4  0.03  2
    1.00   3.70   0.828  0.512  -0.8383  -0.144  0.490   0.013  0.281   0.423   0.000  -0.1020  0.17  6.4  0.03  2
    1.50   3.55   0.260  0.512  -0.7721  -0.144  0.438  -0.049  0.210   0.600   0.040  -0.1200  0.17  6.4  0.03  2
    2.00   3.50  -0.150  0.512  -0.7250  -0.144  0.400  -0.094  0.160   0.610   0.040  -0.1400  0.17  6.4  0.03  2
    3.00   3.50  -0.690  0.512  -0.7250  -0.144  0.400  -0.156  0.089   0.630   0.040  -0.1726  0.17  6.4  0.03  2
    4.00   3.50  -1.130  0.512  -0.7250  -0.144  0.400  -0.200  0.039   0.640   0.040  -0.1956  0.17  6.4  0.03  2
    5.00   3.50  -1.460  0.512  -0.7250  -0.144  0.400  -0.200  0.000   0.664   0.040  -0.2150  0.17  6.4  0.03  2
    """)

    #: Coefficient table for standard deviation calculation (table 4, page 109)
    COEFFS_STD = CoeffsTable(sa_damping=5, table="""\
    imt    b5    b6
    pga    0.70  0.135
    0.01   0.70  0.135
    0.02   0.70  0.135
    0.03   0.70  0.135
    0.04   0.71  0.135
    0.05   0.71  0.135
    0.06   0.72  0.135
    0.075  0.73  0.135
    0.09   0.74  0.135
    0.10   0.74  0.135
    0.12   0.75  0.135
    0.15   0.75  0.135
    0.17   0.76  0.135
    0.20   0.77  0.135
    0.24   0.77  0.135
    0.30   0.78  0.135
    0.36   0.79  0.135
    0.40   0.79  0.135
    0.46   0.80  0.132
    0.50   0.80  0.130
    0.60   0.81  0.127
    0.75   0.81  0.123
    0.85   0.82  0.121
    1.00   0.83  0.118
    1.50   0.84  0.110
    2.00   0.85  0.105
    3.00   0.87  0.097
    4.00   0.88  0.092
    5.00   0.89  0.087
    """)
