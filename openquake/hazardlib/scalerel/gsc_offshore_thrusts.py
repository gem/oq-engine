# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
Rupture scaling models as used for the 2015 Seismic Hazard Model of Canada, as
described in Adams, J., S. Halchuk, T. Allen, and G. Rogers (2015). Canada's
5th Generation seismic hazard model, as prepared for the 2015 National Building
Code of Canada, 11th Canadian Conference on Earthquake Engineering, Victoria,
Canada, Paper 93775.

Module :mod:`openquake.hazardlib.scalerel.gsc_offshore_thrusts` implements
:class:`GSCCascadia`
:class:`GSCEISO`
:class:`GSCEISB`
:class:`GSCEISI`
:class:`GSCOffshoreThrustsWIN`
:class:`GSCOffshoreThrustsHGT`.
"""
from openquake.hazardlib.scalerel.base import BaseMSRSigma
from math import sin, radians


class GSCCascadia(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for the Juan de Fuca segment
    of the Cascadia subduction zone.

    :param SEIS_WIDTH:
        Hard-wired seismogenic width of the CIS source (125 km)

    """
    SEIS_WIDTH = 125.0

    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse
        return (10.0 ** (3.01 + 0.001 * mag)) * self.SEIS_WIDTH

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01


class GSCEISO(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for the outboard estimate of
    rupture (16 km depth) for the Explorer segment of the Cascadia subduction
    zone with an upper seismogenic depth of 5 km and a dip of 18 degrees.
    """
    # Thickness between 16 km lower seismogenic depth and 5 km upper
    # seismogenic depth
    SEIS_WIDTH = 11. / sin(radians(18.0))

    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse
        return (10.0 ** (1.90 + 0.001 * mag)) * self.SEIS_WIDTH

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01


class GSCEISB(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for best estimate landward
    extent of rupture (22 km depth) for the Explorer segment of the Cascadia
    subduction zone with an upper seismogenic depth of 5 km and a dip of 18
    degrees.
    """
    # Thickness between 22 km lower seismogenic depth and 5 km upper
    # seismogenic depth
    SEIS_WIDTH = 17.0 / sin(radians(18.))

    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse
        return (10.0 ** (1.90 + 0.001 * mag)) * self.SEIS_WIDTH

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01


class GSCEISI(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for the inboard estimate of
    rupture (28 km depth) for the Explorer segment of the Cascadia subduction
    zone with an upper seismogenitc depth of 5 km and a dip of 18 degrees.
    """
    # Thickness between 28 km lower seismogenic depth and 5 km upper
    # seismogenic depth
    SEIS_WIDTH = 23.0 / sin(radians(18.))

    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse
        return (10.0 ** (1.90 + 0.001 * mag)) * self.SEIS_WIDTH

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01


class GSCOffshoreThrustsWIN(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for the Winona segment of
    the Jan de Fuca subduction zone that is approximately scaled to give a
    rupture length of 300 km for a MW 8 earthquake and fit the rupture length
    of the M7.8 2012 Haida Gwaii earthquake.  Ruptures assume an upper and
    lower seismogenic depth of 2 km and 5 km respectively, with a dip of 15
    degrees.
    """
    # Thickness between 5 km lower seismogenic depth and 2 km upper
    # seismogenic depth
    SEIS_WIDTH = 3.0 / sin(radians(15.0))

    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse for WIN
        return (10.0 ** (-2.943 + 0.677 * mag)) * self.SEIS_WIDTH

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCOffshoreThrustsWIN. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.2


class GSCOffshoreThrustsHGT(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship that is approximately scaled
    to give a rupture length of 300 km for a MW 8 earthquake and fit the
    rupture length of the M7.8 2012 Haida Gwaii earthquake. Ruptures assume an
    upper and lower seismogenitc depth of 3 km and 22 km, respectively, with a
    dip of 25 degrees.
    """
    # Thickness between 22 km lower seismogenic depth and 3 km upper
    # seismogenic depth
    SEIS_WIDTH = 19.0 / sin(radians(25.0))  # 19 = 22 - 3

    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse for HGT
        return (10.0 ** (-2.943 + 0.677 * mag)) * self.SEIS_WIDTH

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCOffshoreThrustsHGT. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.2
