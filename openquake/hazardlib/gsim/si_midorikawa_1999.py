# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
Module exports :class:`SiMidorikawa1999Asc`, :class:`SiMidorikawa1999SInter`,
:class:`SiMidorikawaSSlab`, :class:`SiMidorikawa1999SInterNorthEastCorrection`,
:class:`SiMidorikawa1999SInterSouthWestCorrection`,
:class:`SiMidorikawa1999SSlabNorthEastCorrection` and
:class:`SiMidorikawa1999SSlabSouthWestCorrection`.
"""
import numpy as np

from scipy.constants import g
from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV, PGA
from openquake.hazardlib.geo import (
    Mesh, RectangularMesh, SimpleFaultSurface)


# Subduction trench coordinates (table 3.5.2-1) page 3-150
SUB_TRENCH_LONS = np.array([
    143.50, 143.00, 141.90, 142.40, 143.25, 143.80, 144.20, 144.30, 144.65,
    146.80, 153.00
])

SUB_TRENCH_LATS = np.array([
    24.00, 29.00, 33.80, 35.80, 36.55, 37.70, 39.20, 40.10, 41.00, 42.00, 45.50
])

# Volcanic front coordinates (table 3.5.2-2, page 3-150)
VOLCANIC_FRONT_LONS = np.array([
    122.00, 124.00, 128.30, 129.70, 130.80, 131.60, 132.00, 133.70, 134.90,
    136.90
])

VOLCANIC_FRONT_LATS = np.array([
    24.50, 24.50, 27.90, 29.50, 31.50, 33.40, 34.90, 35.30, 35.30, 36.20
])


def _construct_surface(lons, lats, upper_depth, lower_depth):
    """
    Utility method that constructs and return a simple fault surface with top
    edge specified by `lons` and `lats` and extending vertically from
    `upper_depth` to `lower_depth`.

    The underlying mesh is built by repeating the same coordinates
    (`lons` and `lats`) at the two specified depth levels.
    """
    depths = np.array([
        np.zeros_like(lons) + upper_depth,
        np.zeros_like(lats) + lower_depth
    ])

    mesh = RectangularMesh(
        np.tile(lons, (2, 1)), np.tile(lats, (2, 1)), depths
    )
    return SimpleFaultSurface(mesh)


def _get_min_distance_to_sub_trench(lons, lats):
    """
    Compute and return minimum distance between subduction trench
    and points specified by 'lon' and 'lat'

    The method creates an instance of
    :class:`openquake.hazardlib.geo.SimpleFaultSurface` to model the subduction
    trench. The surface is assumed vertical and extending from 0 to 10 km
    depth.
    The 10 km depth value is arbitrary given that distance calculation depend
    only on top edge depth. The method calls then
    :meth:`openquake.hazardlib.geo.base.BaseSurface.get_rx_distance`
    and return its absolute value.
    """
    trench = _construct_surface(SUB_TRENCH_LONS, SUB_TRENCH_LATS, 0., 10.)
    sites = Mesh(lons, lats, None)
    return np.abs(trench.get_rx_distance(sites))


def _get_min_distance_to_volcanic_front(lons, lats):
    """
    Compute and return minimum distance between volcanic front and points
    specified by 'lon' and 'lat'.

    Distance is negative if point is located east of the volcanic front,
    positive otherwise.

    The method uses the same approach as :meth:`_get_min_distance_to_sub_trench`
    but final distance is returned without taking the absolute value.
    """
    vf = _construct_surface(VOLCANIC_FRONT_LONS, VOLCANIC_FRONT_LATS, 0., 10.)
    sites = Mesh(lons, lats, None)
    return vf.get_rx_distance(sites)


def _apply_subduction_trench_correction(mean, x_tr, H, rrup, imt):
    """
    Implement equation for subduction trench correction as described in
    equation 3.5.2-1, page 3-148 of "Technical Reports on National Seismic
    Hazard Maps for Japan"
    """
    if imt.name == 'PGV':
        V1 = 10 ** ((-4.021e-5 * x_tr + 9.905e-3) * (H - 30))
        V2 = np.maximum(1., (10 ** (-0.012)) * ((rrup / 300.) ** 2.064))
        corr = V2
        if H > 30:
            corr *= V1
    else:
        V2 = np.maximum(1., (10 ** (+0.13)) * ((rrup / 300.) ** 3.2))
        corr = V2
        if H > 30:
            V1 = 10 ** ((-8.1e-5 * x_tr + 2.0e-2) * (H - 30))
            corr *= V1
    return np.log(np.exp(mean) * corr)


def _apply_volcanic_front_correction(mean, x_vf, H, imt):
    """
    Implement equation for volcanic front correction as described in equation
    3.5.2.-2, page 3-149 of "Technical Reports on National Seismic
    Hazard Maps for Japan"
    """
    V1 = np.zeros_like(x_vf)
    if imt.name == 'PGV':
        idx = x_vf <= 75
        V1[idx] = 4.28e-5 * x_vf[idx] * (H - 30)
        idx = x_vf > 75
        V1[idx] = 3.21e-3 * (H - 30)
        V1 = 10 ** V1
    else:
        idx = x_vf <= 75
        V1[idx] = 7.06e-5 * x_vf[idx] * (H - 30)
        idx = x_vf > 75
        V1[idx] = 5.30e-3 * (H - 30)
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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([PGV, PGA])

    #: Supported intensity measure component is greater of
    #: of two horizontal components :
    #: attr:`~openquake.hazardlib.const.IMC.GREATER_OF_TWO_HORIZONTAL`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
        const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No sites parameters are required
    # REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = set(('rrup', ))

    #: Amplification factor to scale PGV from 600 to 400 m/s vs30,
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
        mean = self._apply_amplification_factor(mean, sites.vs30)
        return mean, stddevs

    def _get_mean(self, imt, mag, hypo_depth, rrup, d):
        """
        Return mean value as defined in equation 3.5.1-1 page 148
        """
        # clip magnitude at 8.3 as per note at page 3-36 in table Table 3.3.2-6
        # in "Technical Reports on National Seismic Hazard Maps for Japan"
        mag = min(mag, 8.3)
        if imt.name == 'PGV':
            mean = (
                0.58 * mag +
                0.0038 * hypo_depth +
                d -
                1.29 -
                np.log10(rrup + 0.0028 * 10 ** (0.5 * mag)) -
                0.002 * rrup
            )
        else:
            mean = (
                0.50 * mag +
                0.0043 * hypo_depth +
                d +
                0.61 -
                np.log10(rrup + 0.0055 * 10 ** (0.5 * mag)) -
                0.003 * rrup
            )
            mean = np.log10(10**(mean)/(g*100))

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

    def _apply_amplification_factor(self, mean, vs30):
        """
        Apply amplification factor to scale PGV value from 600 to 400 m/s vs30
        and convert mean from base 10 to base e.

        The scaling factor from 600 m/s to 400 m/s was defined by NIED.

        The scaling factor from 600 m/s to 800m/s is valid just for the elastic
        case as no adjustment for kappa was considered.
        """
        assert np.all(vs30 == vs30[0])
        if abs(vs30[0]-600.) < 1e-10:
            return mean * np.log(10)
        elif abs(vs30[0]-400.) < 1e-10:
            return mean * np.log(10) + np.log(self.AMP_F)
        elif abs(vs30[0]-800.) < 1e-10:
            return mean * np.log(10) - np.log(1.25)
        else:
            raise ValueError('Si and Midorikawa 1999 do not support this Vs30 value')


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
        if imt.name == 'PGV':
            d = -0.02
        else:
            d = 0.01
        # 
        mean = self._get_mean(imt, rup.mag, rup.hypo_depth, dists.rrup, d)
        stddevs = self._get_stddevs(stddev_types, 10 ** mean)
        mean = self._apply_amplification_factor(mean, sites.vs30)
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


class SiMidorikawa1999SInterNorthEastCorrection(SiMidorikawa1999SInter):
    """
    Extend :class:`SiMidorikawa1999SInter` and takes into account
    correction for northeast Japan (i.e. proximity to subduction trench)
    """
    REQUIRES_SITES_PARAMETERS = set(('lon', 'lat', 'vs30'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Implements equation 3.5.1-1 page 148 for mean value and equation
        3.5.5-1 page 151 for total standard deviation.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)
        x_tr = _get_min_distance_to_sub_trench(sites.lon, sites.lat)
        mean = _apply_subduction_trench_correction(
            mean, x_tr, rup.hypo_depth, dists.rrup, imt)
        return mean, stddevs


class SiMidorikawa1999SInterSouthWestCorrection(SiMidorikawa1999SInter):
    """
    Extend :class:`SiMidorikawa1999SInter` and takes into account
    correction for southwest Japan (i.e. proximity with volcanic front)
    """
    REQUIRES_SITES_PARAMETERS = set(('lon', 'lat', 'vs30'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Implements equation 3.5.1-1 page 148 for mean value and equation
        3.5.5-1 page 151 for total standard deviation.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)
        x_vf = _get_min_distance_to_volcanic_front(sites.lon, sites.lat)
        mean = _apply_volcanic_front_correction(mean, x_vf, rup.hypo_depth, imt)
        return mean, stddevs


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
        if imt.name == 'PGV':
            d = 0.12
        else:
            d = 0.22
        mean = self._get_mean(imt, rup.mag, rup.hypo_depth, dists.rrup, d)
        stddevs = self._get_stddevs(stddev_types, 10 ** mean)
        mean = self._apply_amplification_factor(mean, sites.vs30)
        return mean, stddevs


class SiMidorikawa1999SSlabNorthEastCorrection(SiMidorikawa1999SSlab):
    """
    Extend :class:`SiMidorikawa1999SSlab` and takes into account
    correction for northeast Japan (i.e. proximity to subduction trench)
    """
    REQUIRES_SITES_PARAMETERS = set(('lon', 'lat', 'vs30'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Implements equation 3.5.1-1 page 148 for mean value and equation
        3.5.5-1 page 151 for total standard deviation.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)
        x_tr = _get_min_distance_to_sub_trench(sites.lon, sites.lat)
        mean = _apply_subduction_trench_correction(
            mean, x_tr, rup.hypo_depth, dists.rrup, imt)
        return mean, stddevs


class SiMidorikawa1999SSlabSouthWestCorrection(SiMidorikawa1999SSlab):
    """
    Extend :class:`SiMidorikawa1999SSlab` and takes into account
    correction for southwest Japan (i.e. proximity to volcanic front)
    """
    REQUIRES_SITES_PARAMETERS = set(('lon', 'lat', 'vs30'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Implements equation 3.5.1-1 page 148 for mean value and equation
        3.5.5-1 page 151 for total standard deviation.

        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)
        x_vf = _get_min_distance_to_volcanic_front(sites.lon, sites.lat)
        mean = _apply_volcanic_front_correction(mean, x_vf, rup.hypo_depth, imt)
        return mean, stddevs
