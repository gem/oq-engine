# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module exports :class:`LinLee2008SInter`, class:`LinLee2008SSlab`
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class LinLee2008SInter(GMPE):
    """
    Implements GMPE developed by Po-Shen Lin and Chyi-Tyi Lee and published as
    "Ground-Motion Attenuation Relationships for Subduction-Zone Earthquakes
    in Northeastern Taiwan" (Bulletin of the Seismological Society of America,
    Volume 98, Number 1, pages 220-240, 2008).
    This class implements the equations for 'Subduction Interface' (that's why
    the class name ends with 'SInter').
    """

    #: Supported tectonic region type is subduction interface.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see tables 3 and 4, pages 227 and 228.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components, see equation 10 page 226.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types is total, see equation 10 page 226.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and deep soil).
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and focal depth, see
    #: equation 10 page 226.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is hypocentral distance, see equation 10
    #: page 226.
    REQUIRES_DISTANCES = set(('rhypo', ))

    #: Vs30 threshold value between rock sites (B, C) and soil sites (C, D).
    ROCK_VS30 = 360

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        mean = np.zeros_like(sites.vs30)
        stddevs = [np.zeros_like(sites.vs30) for _ in stddev_types]

        idx_rock = sites.vs30 >= self.ROCK_VS30
        idx_soil = sites.vs30 < self.ROCK_VS30

        if idx_rock.any():
            C = self.COEFFS_ROCK[imt]
            self._compute_mean(C, rup.mag, dists.rhypo, rup.hypo_depth, mean,
                               idx_rock)
            self._compute_std(C, stddevs, idx_rock)

        if idx_soil.any():
            C = self.COEFFS_SOIL[imt]
            self._compute_mean(C, rup.mag, dists.rhypo, rup.hypo_depth, mean,
                               idx_soil)
            self._compute_std(C, stddevs, idx_soil)

        return mean, stddevs

    def _compute_mean(self, C, mag, rhypo, hypo_depth, mean, idx):
        """
        Compute mean value according to equations 10 and 11 page 226.
        """
        mean[idx] = (C['C1'] + C['C2'] * mag + C['C3'] * np.log(rhypo[idx] +
                     C['C4'] * np.exp(C['C5'] * mag)) + C['C6'] * hypo_depth)

    def _compute_std(self, C, stddevs, idx):
        """
        Compute total standard deviation, see tables 3 and 4, pages 227 and
        228.
        """
        for stddev in stddevs:
            stddev[idx] += C['sigma']

    #: Coefficient table for rock sites, see table 3 page 227.
    COEFFS_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT      C1       C2        C3         C4         C5         C6        C7        sigma
    pga     -2.5000    1.205    -1.90499    0.51552    0.63255    0.0075    0.275    0.5268
    0.01    -2.5000    1.205    -1.89500    0.51552    0.63255    0.0075    0.275    0.5228
    0.02    -2.4900    1.200    -1.88000    0.51552    0.63255    0.0075    0.275    0.5199
    0.03    -2.2800    1.155    -1.87500    0.51552    0.63255    0.0075    0.275    0.5245
    0.04    -2.0000    1.100    -1.86000    0.51552    0.63255    0.0075    0.275    0.5363
    0.05    -1.9000    1.090    -1.85500    0.51552    0.63255    0.0075    0.275    0.5380
    0.06    -1.7250    1.065    -1.84000    0.51552    0.63255    0.0075    0.275    0.5555
    0.09    -1.2650    1.020    -1.81500    0.51552    0.63255    0.0075    0.275    0.5830
    0.10    -1.2199    1.000    -1.79500    0.51552    0.63255    0.0075    0.275    0.5818
    0.12    -1.4699    1.040    -1.77000    0.51552    0.63255    0.0075    0.275    0.5759
    0.15    -1.6749    1.045    -1.73000    0.51552    0.63255    0.0075    0.275    0.5828
    0.17    -1.8459    1.065    -1.71000    0.51552    0.63255    0.0075    0.275    0.5918
    0.20    -2.1699    1.085    -1.67500    0.51552    0.63255    0.0075    0.275    0.6071
    0.24    -2.5849    1.105    -1.63000    0.51552    0.63255    0.0075    0.275    0.6328
    0.30    -3.6149    1.215    -1.57000    0.51552    0.63255    0.0075    0.275    0.6669
    0.36    -4.1599    1.255    -1.53500    0.51552    0.63255    0.0075    0.275    0.7024
    0.40    -4.5949    1.285    -1.50000    0.51552    0.63255    0.0075    0.275    0.7119
    0.46    -5.0200    1.325    -1.49500    0.51552    0.63255    0.0075    0.275    0.7162
    0.50    -5.4700    1.365    -1.46500    0.51552    0.63255    0.0075    0.275    0.7159
    0.60    -6.0950    1.420    -1.45500    0.51552    0.63255    0.0075    0.275    0.7191
    0.75    -6.6750    1.465    -1.45000    0.51552    0.63255    0.0075    0.275    0.7704
    0.85    -7.3200    1.545    -1.45000    0.51552    0.63255    0.0075    0.275    0.7803
    1.00    -8.0000    1.620    -1.45000    0.51552    0.63255    0.0075    0.275    0.7999
    1.50    -9.2400    1.705    -1.44000    0.51552    0.63255    0.0075    0.275    0.8428
    2.00    -10.200    1.770    -1.43000    0.51550    0.63260    0.0075    0.275    0.8784
    3.00    -11.470    1.830    -1.37000    0.51550    0.63260    0.0075    0.275    0.8607
    4.00    -12.550    1.845    -1.26000    0.51550    0.63260    0.0075    0.275    0.8071
    5.00    -13.200    1.805    -1.13500    0.51550    0.63260    0.0075    0.275    0.7913
    """)

     #: Coefficient table for soil sites, see table 4 page 228.
    COEFFS_SOIL = CoeffsTable(sa_damping=5, table="""\
    IMT      C1        C2         C3        C4         C5         C6       C7      sigma
    pga     -0.9000    1.00000    -1.900    0.99178    0.52632    0.004    0.31    0.48763
    0.01    -2.2000    1.08500    -1.750    0.99178    0.52632    0.004    0.31    0.57200
    0.02    -2.2900    1.08500    -1.730    0.99178    0.52632    0.004    0.31    0.56720
    0.03    -2.3400    1.09500    -1.720    0.99178    0.52632    0.004    0.31    0.57246
    0.04    -2.2150    1.09000    -1.730    0.99178    0.52632    0.004    0.31    0.57663
    0.05    -1.8950    1.05500    -1.755    0.99178    0.52632    0.004    0.31    0.59221
    0.06    -1.1100    1.01000    -1.835    0.99178    0.52632    0.004    0.31    0.59351
    0.09    -0.2099    0.94500    -1.890    0.99178    0.52632    0.004    0.31    0.62718
    0.10    -0.0549    0.92000    -1.880    0.99178    0.52632    0.004    0.31    0.63322
    0.12    -0.0551    0.93500    -1.895    0.99178    0.52632    0.004    0.31    0.64289
    0.15    -0.0399    0.95500    -1.880    0.99178    0.52632    0.004    0.31    0.65238
    0.17    -0.3399    1.02000    -1.885    0.99178    0.52632    0.004    0.31    0.66732
    0.20    -0.7999    1.04500    -1.820    0.99178    0.52632    0.004    0.31    0.65718
    0.24    -1.5749    1.12000    -1.755    0.99178    0.52632    0.004    0.31    0.64040
    0.30    -3.0099    1.31500    -1.695    0.99178    0.52632    0.004    0.31    0.64856
    0.36    -3.6800    1.38000    -1.660    0.99178    0.52632    0.004    0.31    0.67233
    0.40    -4.2500    1.41500    -1.600    0.99178    0.52632    0.004    0.31    0.67986
    0.46    -4.7200    1.43000    -1.545    0.99178    0.52632    0.004    0.31    0.67889
    0.50    -5.2200    1.45500    -1.490    0.99178    0.52632    0.004    0.31    0.68034
    0.60    -5.7000    1.47000    -1.445    0.99178    0.52632    0.004    0.31    0.67322
    0.75    -6.4500    1.50000    -1.380    0.99178    0.52632    0.004    0.31    0.70085
    0.85    -7.3500    1.56500    -1.325    0.99178    0.52632    0.004    0.31    0.71854
    1.00    -8.1500    1.60500    -1.235    0.99178    0.52632    0.004    0.31    0.72217
    1.50    -10.300    1.80001    -1.165    0.99180    0.52630    0.004    0.31    0.72945
    2.00    -11.620    1.86002    -1.070    0.99180    0.52630    0.004    0.31    0.74782
    3.00    -12.630    1.89002    -1.060    0.99180    0.52630    0.004    0.31    0.73083
    4.00    -13.420    1.87001    -0.990    0.99180    0.52630    0.004    0.31    0.70625
    5.00    -13.750    1.83501    -0.975    0.99180    0.52630    0.004    0.31    0.65593
    """)


class LinLee2008SSlab(LinLee2008SInter):
    """
    Implements GMPE developed by Po-Shen Lin and Chyi-Tyi Lee and published as
    "Ground-Motion Attenuation Relationships for Subduction-Zone Earthquakes
    in Northeastern Taiwan" (Bulletin of the Seismological Society of America,
    Volume 98, Number 1, pages 220-240, 2008).
    This class implements the equations for 'Subduction IntraSlab' (that's why
    the class name ends with 'SSlab').
    """

    #: Supported tectonic region type is Subduction IntraSlab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean, stddevs = super(LinLee2008SSlab, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        idx_rock = sites.vs30 >= self.ROCK_VS30
        idx_soil = sites.vs30 < self.ROCK_VS30

        mean[idx_rock] += 0.275
        mean[idx_soil] += 0.31

        return mean, stddevs
