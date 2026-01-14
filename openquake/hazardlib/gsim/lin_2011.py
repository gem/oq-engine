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
Module exports :class:`Lin2011foot`, :class:`Lin2011hanging`
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
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

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


class Lin2011hanging(Lin2011foot):
    """
    Implements GMPE developed by Po-Shen Lin and others and published as
    "Response spectral attenuation relations for shallow crustal earthquakes
    in Taiwan", Engineering Geology, Vol. 121, Issues 3–4, 10 August 2011,
    Pages 150-164.
    """

    #: Coefficient table for rock sites, see table 3 page 153.
    COEFFS_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT      C1       C2        C3         C4         C5         sigma
    pga     -3.2790    1.035    -1.65100    0.15200    0.62300   0.6510
    0.01    -3.2530    1.018    -1.62900    0.15900    0.61200   0.6470
    0.06    -1.7380    0.908    -1.76900    0.32700    0.50200   0.7020
    0.09    -1.2370    0.841    -1.75000    0.47800    0.40200   0.7480
    0.10    -1.1030    0.841    -1.76500    0.45500    0.41700   0.7500
    0.20    -2.7670    0.980    -1.52200    0.09700    0.62700   0.6970
    0.30    -4.4400    1.186    -1.43800    0.02700    0.82300   0.6850
    0.40    -5.6300    1.335    -1.41400    0.01400    0.93200   0.6830
    0.50    -6.7460    1.456    -1.36500    0.00600    1.05700   0.6780
    0.60    -7.6370    1.557    -1.34800    0.00330    1.14700   0.6660
    0.75    -8.6410    1.653    -1.31300    0.00150    1.25700   0.6520
    1.00    -9.9780    1.800    -1.28600    0.00080    1.37700   0.6710
    1.50   -11.6170    1.976    -1.28400    0.00040    1.50800   0.6830
    2.00   -12.6110    2.058    -1.26100    0.00050    1.49700   0.7060
    3.00   -13.3030    2.036    -1.23400    0.00130    1.30200   0.7020
    5.00   -13.9140    1.958    -1.15600    0.00120    1.24100   0.7260
    """)

    #: Coefficient table for soil sites, see table 4 page 153.
    COEFFS_SOIL = CoeffsTable(sa_damping=5, table="""\
    IMT      C1        C2         C3        C4         C5         sigma
    pga     -3.2480    0.943    -1.47100    0.10000    0.64800   0.6280
    0.01    -3.0080    0.905    -1.45100    0.11000    0.63800   0.6230
    0.06    -1.9940    0.809    -1.50000    0.25100    0.51800   0.6860
    0.09    -1.4080    0.765    -1.55100    0.28000    0.51000   0.7090
    0.10    -1.5080    0.785    -1.55100    0.28000    0.50000   0.7130
    0.20    -3.2260    0.870    -1.21100    0.04500    0.70800   0.6870
    0.30    -4.0500    0.999    -1.20500    0.03000    0.78800   0.6570
    0.40    -5.2930    1.165    -1.16700    0.01100    0.95800   0.6550
    0.50    -6.3070    1.291    -1.13400    0.00420    1.11800   0.6530
    0.60    -7.2090    1.395    -1.09900    0.00160    1.25800   0.6420
    0.75    -8.3090    1.509    -1.04400    0.00060    1.40800   0.6510
    1.00    -9.8680    1.691    -1.00400    0.00040    1.48500   0.6770
    1.50   -11.2160    1.798    -0.96500    0.00030    1.52200   0.7220
    2.00   -12.8060    2.005    -0.97500    0.00050    1.52800   0.7590
    3.00   -13.8860    2.099    -1.07700    0.00040    1.54800   0.7870
    5.00   -14.6060    2.160    -1.11400    0.00040    1.56200   0.8200
    """)
