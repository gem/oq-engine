# The Hazard Library
# Copyright (C) 2013-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module exports :class:`SiMidorikawa1999Asc`, class:`SiMidorikawa1999SInter`,
and class:`SiMidorikawaSSlab`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV
from openquake.hazardlib.geo import Point, Line, Mesh, SimpleFaultSurface


# Subduction trench axis (table 3.5.2-1) page 3-150
SUB_TRENCH = Line([
    Point(143.50, 24.00),
    Point(143.00, 29.00),
    Point(141.90, 33.80),
    Point(142.40, 35.80),
    Point(143.25, 36.55),
    Point(143.80, 37.70),
    Point(144.20, 39.20),
    Point(144.30, 40.10),
    Point(144.65, 41.00),
    Point(146.80, 42.00),
    Point(153.00, 45.50)
]).resample(10.)


# Volcanic front coordinates (table 3.5.2-2, page 3-150)
VOLCANIC_FRONT = Line([
    Point(122.00, 24.50),
    Point(124.00, 24.50),
    Point(128.30, 27.90),
    Point(129.70, 29.50),
    Point(130.80, 31.50),
    Point(131.60, 33.40),
    Point(132.00, 34.90),
    Point(133.70, 35.30),
    Point(134.90, 35.30),
    Point(136.90, 36.20)
])


def _get_min_distance_to_sub_trench(lons, lats):
    """
    Compute and return minimum distance between subduction trench line
    (defined by 'SUB_TRENCH') and points specified by 'lons' and 'lats'
    """
    trench = Mesh.from_points_list(SUB_TRENCH.points)
    sites = Mesh(lons, lats, None)

    return trench.get_min_distance(sites)


def _get_min_distance_to_volcanic_front(lons, lats):
    """
    Compute and return minimum distance between volcanic front line (defined by
    'VOLCANIC_FRONT') and points specified by 'lons' and 'lats'.

    Distance is negative if point is located east of the volcanic front,
    positive otherwise.
    """
    surf = SimpleFaultSurface.from_fault_data(
        VOLCANIC_FRONT,
        upper_seismogenic_depth=0.,
        lower_seismogenic_depth=10.,
        dip=90.,
        mesh_spacing=10.
    )
    sites = Mesh(lons, lats, None)

    return surf.get_rx_distance(sites)


def _apply_subduction_trench_correction(mean, x_tr, H, rrup):
    """
    Implement equation for subduction trench correction as described in
    equation 3.5.2-1, page 3-148 of "Technical Reports on National Seismic
    Hazard Maps for Japan"
    """
    V1 = 10 ** ((-4.021e-5 * x_tr + 9.905e-3) * (H - 30))
    V2 = np.maximum(1., (10 ** (-0.012)) * ((rrup / 300.) ** 2.064))

    corr = V2
    if H > 30:
        corr *= V1

    return np.log(np.exp(mean) * corr)


def _apply_volcanic_front_correction(mean, x_vf, H):
    """
    Implement equation for volcanic front correction as described in equation
    3.5.2.-2, page 3-149 of "Technical Reports on National Seismic
    Hazard Maps for Japan"
    """
    V1 = numpy.zeros_like(x_vf)

    idx = x_vf <= 75
    V1[idx] = 4.28e-5 * x_vf[idx] * (H - 30)

    idx = x_vf > 75
    V1[idx] = 3.21e-3 * (H - 30)

    V1 = 10 ** V1

    return np.log(np.exp(mean) * V1)


class SiMidorikawa1999Asc(GMPE):
    """
    Implements GMPE developed by Hongjun Si and Saburoh Midorikawa (1999) as
    described in "Technical Reports on National Seismic Hazard Maps for Japan"
    (2009, National Research Institute for Earth Science and Disaster
    Prevention, Japan, pages 148-151).
    This class implements the equations for 'Active Shallow Crust'
    (that's why the class name ends with 'Asc').
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure type is PGV
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGV
    ])

    #: Supported intensity measure component is greater of
    #: of two horizontal components :
    #: attr:`~openquake.hazardlib.const.IMC.GREATER_OF_TWO_HORIZONTAL`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
        const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameters are geographical coordinates, used to
    #: compute volcanic front and subduction trench corrections
    REQUIRES_SITES_PARAMETERS = set(('lons', 'lats'))

    #: Required rupture parameters are magnitude, and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = set(('rrup', ))

    #: Amplification factor to scale PGV at 400 km vs30,
    #: see equation 3.5.1-1 page 148
    AMP_F = 1.41

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Implements equation 3.5.1-1 page 148 for mean value and equation
        3.5.5-2 page 151 for total standard deviation.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean = self._get_mean(imt, rup.mag, rup.hypo_depth, dists.rrup, d=0)
        stddevs = self._get_stddevs(stddev_types, dists.rrup)

        return mean, stddevs

    def _get_mean(self, imt, mag, hypo_depth, rrup, d):
        """
        Return mean value as defined in equation 3.5.1-1 page 148
        """
        assert imt.__class__ in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES

        # clip magnitude at 8.3 as per note at page 3-36 in table Table 3.3.2-6
        # in "Technical Reports on National Seismic Hazard Maps for Japan"
        mag = min(mag, 8.3)

        mean = (
            0.58 * mag +
            0.0038 * hypo_depth +
            d -
            1.29 -
            np.log10(rrup + 0.0028 * 10 ** (0.5 * mag)) -
            0.002 * rrup
        )

        # convert from log10 to ln
        # and apply amplification function
        mean = np.log(10 ** mean * self.AMP_F)

        return mean

    def _get_stddevs(self, stddev_types, rrup):
        """
        Return standard deviations as defined in equation 3.5.5-2 page 151
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        std = np.zeros_like(rrup)

        std[rrup <= 20] = 0.23

        idx = (rrup > 20) & (rrup <= 30)
        std[idx] = 0.23 - 0.03 * np.log10(rrup[idx] / 20) / np.log10(30. / 20.)

        std[rrup > 30] = 0.20

        # convert from log10 to ln
        std = np.log(10 ** std)

        return [std for stddev_type in stddev_types]


class SiMidorikawa1999SInter(SiMidorikawa1999Asc):
    """
    Implements GMPE developed by Hongjun Si and Saburoh Midorikawa (1999) as
    described in "Technical Reports on National Seismic Hazard Maps for Japan"
    (2009, National Research Institute for Earth Science and Disaster
    Prevention, Japan, pages 148-151).
    This class implements the equations for 'Subduction Interface'
    (that's why the class name ends with 'SInter').
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Implements equation 3.5.1-1 page 148 for mean value and equation
        3.5.5-1 page 151 for total standard deviation.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean = self._get_mean(imt, rup.mag, rup.hypo_depth, dists.rrup,
                              d=-0.02)
        stddevs = self._get_stddevs(stddev_types, np.exp(mean))

        return mean, stddevs

    def _get_stddevs(self, stddev_types, pgv):
        """
        Return standard deviations as defined in equation 3.5.5-1 page 151
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        std = np.zeros_like(pgv)

        std[pgv <= 25] = 0.20

        idx = (pgv > 25) & (pgv <= 50)
        std[idx] = 0.20 - 0.05 * (pgv[idx] - 25) / 25

        std[pgv > 50] = 0.15

        # convert from log10 to ln
        std = np.log(10 ** std)

        return [std for stddev_type in stddev_types]


class SiMidorikawa1999SSlab(SiMidorikawa1999SInter):
    """
    Implements GMPE developed by Hongjun Si and Saburoh Midorikawa (1999) as
    described in "Technical Reports on National Seismic Hazard Maps for Japan"
    (2009, National Research Institute for Earth Science and Disaster
    Prevention, Japan, pages 148-151).
    This class implements the equations for 'Subduction IntraSlab'
    (that's why the class name ends with 'SSlab').
    """
    #: Supported tectonic region type is subduction intraslab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Implements equation 3.5.1-1 page 148 for mean value and equation
        3.5.5-1 page 151 for total standard deviation.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean = self._get_mean(imt, rup.mag, rup.hypo_depth, dists.rrup, d=0.12)
        stddevs = self._get_stddevs(stddev_types, np.exp(mean))

        return mean, stddevs
