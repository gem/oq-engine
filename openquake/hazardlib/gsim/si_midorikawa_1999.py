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

    #: No site parameters are needed
    REQUIRES_SITES_PARAMETERS = set()

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
