# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4 \
#
# Copyright (C) 2019 GEM Foundation, Chung-Han Chan
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
Module exports :class:`Lin2011foot`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_mean(C, mag, rrup, mean, idx):
    """
    Compute mean value according to equations 10 and 11 page 226.
    """
    mean[idx] = (C['C1'] + C['C2'] * mag[idx] + C['C3'] * np.log(rrup[idx] +
                 C['C4'] * np.exp(C['C5'] * mag[idx])))


def _compute_std(C, stddev, idx):
    """
    Compute total standard deviation, see tables 3 and 4, pages 227 and 228.
    """
    stddev[idx] = C['sigma']


class Lin2011foot(GMPE):
    """
    Implements GMPE developed by Po-Shen Lin and others and published as
    "Response spectral attenuation relations for shallow crustal earthquakes
    in Taiwan", Engineering Geology, Volume 121, Issues 3–4, 10 August 2011,
    Pages 150-164.
    """

    #: Supported tectonic region type is active shallow crust.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see tables 3 and 4, pages 227 and 228.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components, see equation 10 page 226.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types is total, see equation 10 page 226.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and deep soil).
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, and focal depth, see
    #: equation 10 page 226.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is rrup distance, see equation 4
    #: page 154.
    REQUIRES_DISTANCES = {'rrup'}

    #: Vs30 threshold value between rock sites (B, C) and soil sites (C, D).
    ROCK_VS30 = 360

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        idx_rock = ctx.vs30 >= self.ROCK_VS30
        idx_soil = ctx.vs30 < self.ROCK_VS30

        for m, imt in enumerate(imts):

            if idx_rock.any():
                CR = self.COEFFS_ROCK[imt]
                _compute_mean(CR, ctx.mag, ctx.rrup, mean[m], idx_rock)
                _compute_std(CR, sig[m], idx_rock)

            if idx_soil.any():
                CS = self.COEFFS_SOIL[imt]
                _compute_mean(CS, ctx.mag, ctx.rrup, mean[m], idx_soil)
                _compute_std(CS, sig[m], idx_soil)

    #: Coefficient table for rock sites, see table 3 page 153.
    COEFFS_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT      C1       C2        C3         C4         C5         sigma
    pga     -3.2320    1.047    -1.66200    0.19200    0.63000   0.6520
    0.01    -3.1930    1.017    -1.61200    0.21000    0.59000   0.6480
    0.06    -2.6430    0.937    -1.60200    0.23000    0.55000   0.7090
    0.09    -2.0930    0.907    -1.64200    0.23000    0.55000   0.7550
    0.10    -1.9930    0.907    -1.65200    0.19000    0.59000   0.7560
    0.20    -2.6590    0.960    -1.51200    0.14800    0.61000   0.6990
    0.30    -4.3870    1.169    -1.42200    0.04400    0.79000   0.6860
    0.40    -5.6340    1.328    -1.39900    0.02200    0.90000   0.6820
    0.50    -6.3910    1.410    -1.34700    0.01800    0.95000   0.7340
    0.60    -7.6340    1.576    -1.34500    0.00430    1.19100   0.7210
    0.75    -8.8850    1.665    -1.25400    0.00090    1.39400   0.7010
    1.00   -10.0310    1.777    -1.24000    0.00070    1.41600   0.7170
    1.50   -11.6330    1.930    -1.21900    0.00050    1.46300   0.6780
    2.00   -12.5990    1.989    -1.17400    0.00050    1.46400   0.7030
    3.00   -13.3110    1.974    -1.14000    0.00090    1.30600   0.7010
    5.00   -13.9850    1.957    -1.14500    0.00130    1.20200   0.7260
    """)

    #: Coefficient table for soil sites, see table 4 page 153.
    COEFFS_SOIL = CoeffsTable(sa_damping=5, table="""\
    IMT      C1        C2         C3        C4         C5         sigma
    pga     -3.2180    0.935    -1.46400    0.12500    0.65000   0.6300
    0.01    -3.3060    0.937    -1.45400    0.10000    0.67000   0.6260
    0.06    -1.8960    0.977    -1.74400    0.14000    0.72000   0.6850
    0.09    -1.2560    0.907    -1.75400    0.15100    0.72000   0.7080
    0.10    -1.3060    0.907    -1.73400    0.15100    0.71000   0.7120
    0.20    -3.3100    0.957    -1.29100    0.10000    0.70000   0.6900
    0.30    -4.8800    1.219    -1.29400    0.03100    0.91000   0.6630
    0.40    -5.6280    1.239    -1.18100    0.01220    1.02000   0.6540
    0.50    -6.2840    1.311    -1.16000    0.00570    1.13000   0.6520
    0.60    -7.2520    1.429    -1.12800    0.00250    1.26000   0.6400
    0.75    -8.3550    1.536    -1.06500    0.00080    1.42000   0.6480
    1.00    -9.8600    1.692    -0.99500    0.00050    1.50400   0.6730
    1.50   -11.7500    1.919    -0.99700    0.00050    1.54400   0.7140
    2.00   -12.8270    2.025    -0.99600    0.00050    1.53600   0.7560
    3.00   -13.7950    2.069    -0.98900    0.00050    1.49000   0.7840
    5.00   -14.2560    2.120    -1.14400    0.00070    1.48000   0.8220
    """)
