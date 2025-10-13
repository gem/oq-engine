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

"""
Module exports :class:`SadighEtAl1997`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

#: IMT-independent coefficients for deep soil ctx (table 4).
COEFFS_SOIL_IMT_INDEPENDENT = {
    'c1ss': -2.17,
    'c1r': -1.92,
    'c2': 1.0,
    'c3': 1.7,
    'c4lowmag': 2.1863,
    'c5lowmag': 0.32,
    'c4himag': 0.3825,
    'c5himag': 0.5882
}

#: If site vs30 is more than 750 m/s -- treat the soil as rock.
#: See page 180.
ROCK_VS30 = 750

#: Magnitude value to separate coefficients table because of near field
#: saturation effect is 6.5. See page 184.
NEAR_FIELD_SATURATION_MAG = 6.5


def get_mean_deep_soil(mag, rrup, is_reverse, C):
    """
    Calculate and return the mean intensity for deep soil ctx.

    Implements an equation from table 4.
    """
    c1 = np.where(is_reverse,
                     COEFFS_SOIL_IMT_INDEPENDENT['c1r'],
                     COEFFS_SOIL_IMT_INDEPENDENT['c1ss'])
    c2 = COEFFS_SOIL_IMT_INDEPENDENT['c2']
    c3 = COEFFS_SOIL_IMT_INDEPENDENT['c3']
    c4 = np.where(mag <= NEAR_FIELD_SATURATION_MAG,
                     COEFFS_SOIL_IMT_INDEPENDENT['c4lowmag'],
                     COEFFS_SOIL_IMT_INDEPENDENT['c4himag'])
    c5 = np.where(mag <= NEAR_FIELD_SATURATION_MAG,
                     COEFFS_SOIL_IMT_INDEPENDENT['c5lowmag'],
                     COEFFS_SOIL_IMT_INDEPENDENT['c5himag'])
    c6 = np.where(is_reverse, C['c6r'], C['c6ss'])
    # clip mag if greater than 8.5. This is to avoid
    # ValueError: negative number cannot be raised to a fractional power
    mag = np.clip(mag, None, 8.5)
    return (c1 + c2 * mag + c6 + C['c7'] * ((8.5 - mag) ** 2.5)
            - c3 * np.log(rrup + c4 * np.exp(c5 * mag)))


def get_mean_rock(mag, rrup, is_reverse, low_coeffs, hi_coeffs):
    """
    Calculate and return the mean intensity for rock ctx.

    Implements an equation from table 2.
    """
    # clip mag if greater than 8.5. This is to avoid
    # ValueError: negative number cannot be raised to a fractional power
    mag = np.clip(mag, None, 8.5)

    # determine the coefficients to use depending on the mag
    C = np.where(mag <= NEAR_FIELD_SATURATION_MAG, low_coeffs, hi_coeffs)

    # compute the mean
    mean = (C['c1'] + C['c2'] * mag + C['c3'] * ((8.5 - mag) ** 2.5)
            + C['c4'] * np.log(rrup + np.exp(C['c5'] + C['c6'] * mag))
            + C['c7'] * np.log(rrup + 2))
    # footnote in table 2 says that for reverse ruptures
    # the mean amplitude value should be multiplied by 1.2
    mean[is_reverse] += 0.1823215567939546  # == log(1.2)
    return mean


def get_stddev_rock(mag, C):
    """
    Calculate and return total standard deviation for rock ctx.

    Implements formulae from table 3.
    """
    return np.where(
        mag > C['maxmag'], C['maxsigma'], C['sigma0'] + C['magfactor'] * mag)


def get_stddev_deep_soil(mag, C):
    """
    Calculate and return total standard deviation for deep soil ctx.

    Implements formulae from the last column of table 4.
    """
    # footnote from table 4 says that stderr for magnitudes over 7
    # is equal to one of magnitude 7.
    return C['sigma0'] + C['magfactor'] * np.clip(mag, None, 7)


class SadighEtAl1997(GMPE):
    """
    Implements GMPE developed by Sadigh, K., C. -Y. Chang, J. A. Egan,
    F. Makdisi, and R. R. Youngs (1997) and published as "Attenuation
    relationships for shallow crustal earthquakes based on California
    strong motion data", Seismological Research Letters, 68(1), 180-189.
    """
    #: Supported tectonic region type is active shallow crust,
    #: since data consists of California earthquakes mainly.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see page 180.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two : horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`, : see
    #: page 180.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is only total, see table 3.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and deep soil).
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is RRup (eq. 1).
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # GMPE differentiates strike-slip, reverse and normal ruptures,
        # but combines normal and strike-slip into one category. See page 180.
        reverse = (45 <= ctx.rake) & (ctx.rake <= 135)
        is_rock = ctx.vs30 > ROCK_VS30
        is_soil = ctx.vs30 <= ROCK_VS30
        mag_r = ctx.mag[is_rock]
        mag_s = ctx.mag[is_soil]
        rrup_r = ctx.rrup[is_rock]
        rrup_s = ctx.rrup[is_soil]
        reverse_r = reverse[is_rock]
        reverse_s = reverse[is_soil]
        for m, imt in enumerate(imts):
            mean[m, is_rock] = get_mean_rock(
                mag_r, rrup_r, reverse_r,
                self.COEFFS_ROCK_LOWMAG[imt],
                self.COEFFS_ROCK_HIMAG[imt])
            sig[m, is_rock] = get_stddev_rock(
                mag_r, self.COEFFS_ROCK_STDDERR[imt])

            mean[m, is_soil] = get_mean_deep_soil(
                mag_s, rrup_s, reverse_s, self.COEFFS_SOIL[imt])
            sig[m, is_soil] = get_stddev_deep_soil(
                mag_s, self.COEFFS_SOIL[imt])

    #: Coefficients tables for rock ctx (table 2), for magnitude
    #: values of :attr:`NEAR_FIELD_SATURATION_MAG` and below. Damping
    #: for spectral acceleration here and in other SA-tables is 5%,
    #: see "introduction" section.
    COEFFS_ROCK_LOWMAG = CoeffsTable(sa_damping=5, table="""\
    IMT    c1     c2    c3      c4      c5       c6      c7
    PGA   -0.624  1.0   0.000  -2.100   1.29649  0.250   0.0
    0.07   0.110  1.0   0.006  -2.128   1.29649  0.250  -0.082
    0.10   0.275  1.0   0.006  -2.148   1.29649  0.250  -0.041
    0.20   0.153  1.0  -0.004  -2.080   1.29649  0.250   0.0
    0.30  -0.057  1.0  -0.017  -2.028   1.29649  0.250   0.0
    0.40  -0.298  1.0  -0.028  -1.990   1.29649  0.250   0.0
    0.50  -0.588  1.0  -0.040  -1.945   1.29649  0.250   0.0
    0.75  -1.208  1.0  -0.050  -1.865   1.29649  0.250   0.0
    1.0   -1.705  1.0  -0.055  -1.800   1.29649  0.250   0.0
    1.5   -2.407  1.0  -0.065  -1.725   1.29649  0.250   0.0
    2.0   -2.945  1.0  -0.070  -1.670   1.29649  0.250   0.0
    3.0   -3.700  1.0  -0.080  -1.610   1.29649  0.250   0.0
    4.0   -4.230  1.0  -0.100  -1.570   1.29649  0.250   0.0
    """)

    #: Coefficients tables for rock ctx (table 2), for magnitude
    #: values above :attr:`NEAR_FIELD_SATURATION_MAG`.
    COEFFS_ROCK_HIMAG = CoeffsTable(sa_damping=5, table="""\
    IMT    c1     c2    c3      c4      c5       c6      c7
    PGA   -1.274  1.1   0.000  -2.100  -0.48451  0.524   0.0
    0.07  -0.540  1.1   0.006  -2.128  -0.48451  0.524  -0.082
    0.10  -0.375  1.1   0.006  -2.148  -0.48451  0.524  -0.041
    0.20  -0.497  1.1  -0.004  -2.080  -0.48451  0.524   0.0
    0.30  -0.707  1.1  -0.017  -2.028  -0.48451  0.524   0.0
    0.40  -0.948  1.1  -0.028  -1.990  -0.48451  0.524   0.0
    0.50  -1.238  1.1  -0.040  -1.945  -0.48451  0.524   0.0
    0.75  -1.858  1.1  -0.050  -1.865  -0.48451  0.524   0.0
    1.0   -2.355  1.1  -0.055  -1.800  -0.48451  0.524   0.0
    1.5   -3.057  1.1  -0.065  -1.725  -0.48451  0.524   0.0
    2.0   -3.595  1.1  -0.070  -1.670  -0.48451  0.524   0.0
    3.0   -4.350  1.1  -0.080  -1.610  -0.48451  0.524   0.0
    4.0   -4.880  1.1  -0.100  -1.570  -0.48451  0.524   0.0
    """)

    #: Coefficient tables for standard error on rock ctx (table 3).
    COEFFS_ROCK_STDDERR = CoeffsTable(sa_damping=5, table="""\
    IMT    sigma0  magfactor maxsigma maxmag
    PGA    1.39   -0.14      0.38     7.21
    0.07   1.40   -0.14      0.39     7.21
    0.10   1.41   -0.14      0.40     7.21
    0.20   1.43   -0.14      0.42     7.21
    0.30   1.45   -0.14      0.44     7.21
    0.40   1.48   -0.14      0.47     7.21
    0.50   1.50   -0.14      0.49     7.21
    0.75   1.52   -0.14      0.51     7.21
    1.0    1.53   -0.14      0.52     7.21
    4.0    1.53   -0.14      0.52     7.21
    """)

    #: Coefficient tables for deep soil ctx (table 4).
    COEFFS_SOIL = CoeffsTable(sa_damping=5, table="""\
    IMT    c6ss     c6r      c7     sigma0  magfactor maxmag
    PGA    0.0000   0.0000   0.0    1.52   -0.16      7
    0.075  0.4572   0.4572   0.005  1.54   -0.16      7
    0.1    0.6395   0.6395   0.005  1.54   -0.16      7
    0.2    0.9187   0.9187  -0.004  1.565  -0.16      7
    0.3    0.9547   0.9547  -0.014  1.58   -0.16      7
    0.4    0.9251   0.9005  -0.024  1.595  -0.16      7
    0.5    0.8494   0.8285  -0.033  1.61   -0.16      7
    0.75   0.7010   0.6802  -0.051  1.635  -0.16      7
    1.0    0.5665   0.5075  -0.065  1.66   -0.16      7
    1.5    0.3235   0.2215  -0.090  1.69   -0.16      7
    2.0    0.1001  -0.0526  -0.108  1.70   -0.16      7
    3.0   -0.2801  -0.4905  -0.139  1.71   -0.16      7
    4.0   -0.6274  -0.8907  -0.160  1.71   -0.16      7
    """)
