# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.base` defines an abstract base
classes for :class:`ASR <BaseASR>` and :class:`MSR <BaseMSR>`.
"""
import abc
import math


class BaseASR(object):
    """
    A base class for Area-Magnitude Scaling Relationship.
    Allows calculation of rupture magnitude from area.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_median_mag(self, area, rake):
        """
        Return median magnitude (Mw) given the area and rake.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """


class BaseASRWithUncertainties(BaseASR):
    """
    Extend :class:`BaseASR` and allows to include uncertainties in
    rupture magnitude estimation.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_std_dev_mag(self, rake):
        """
        Return the standard deviation on the magnitude.

        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """

    def get_mag(self, area, rake, epsilon=0.0):
        """
        Return the Moment magnitude given the area, rake
        and uncertainty epsilon.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        :param epsilon:
            Uncertainty residual, which identifies the number
            of standard deviations from the median.
        """
        median_mag = self.get_median_mag(area, rake)
        std_dev = self.get_std_dev_mag(rake)
        return median_mag + epsilon * std_dev


class BaseMSR(object):
    """
    A base class for Magnitude-Area Scaling Relationship.
    Allows calculation of rupture area from magnitude.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_median_area(self, mag, rake):
        """
        Return median area (in square km) from magnitude ``mag`` and ``rake``.

        To be overridden by subclasses.

        :param mag:
            Moment magnitude (Mw).
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """


class BaseMSRWithUncertainties(BaseMSR):
    """
    Extends :class:`BaseMSR` and allows to include uncertainties in rupture
    area estimation.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_std_dev_area(self, mag, rake):
        """
        Return the standard deviation of the area distribution
        given magnitude ``mag`` and rake.

        To be overridden by subclasses.

        :param mag:
            Moment magnitude (Mw).
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """

    def get_area(self, mag, rake, epsilon=0.0):
        """
        Return the area (in square km) from magnitude ``mag``, ``rake``,
        and uncertainty ``epsilon``. Assumes area to be log-normally
        distributed (with logarithmic function of base 10).

        :param mag:
            Moment magnitude (Mw)
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        :param epsilon:
            Uncertainty residual, which identifies the number
            of standard deviations from the median.
        """
        median_area = self.get_median_area(mag, rake)
        std_dev = self.get_std_dev_area(mag, rake)
        return 10 ** (math.log10(median_area) + epsilon * std_dev)
