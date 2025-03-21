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
Module :mod:`openquake.hazardlib.scalerel.base` defines abstract base
classes for :class:`ASR <BaseASR>`, :class:`MSR <BaseMSR>`,
:class:`ASRSigma <BaseASRSigma>`, and :class:`MSRSigma <BaseMSRSigma>`
"""
import abc
import inspect


def check_args(func, expected):
    got = inspect.getfullargspec(func).args
    if got != expected:
        raise SyntaxError('%s must must have signature (%s), got (%s)' %
                          (func.__name__, ', '.join(expected), ', '.join(got)))


class BaseASR(metaclass=abc.ABCMeta):
    """
    A base class for Area-Magnitude Scaling Relationship.
    Allows calculation of rupture magnitude from area.
    """
    def __init_subclass__(cls):
        for key, func in cls.__dict__.items():
            if key == 'get_std_dev_mag':
                check_args(func, ['self', 'area', 'rake'])
            elif key == 'get_median_area':
                check_args(func, ['self', 'mag', 'rake'])

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

    def __str__(self):
        """
        Returns a TOML representation of the instance
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Returns the name of the class in angular brackets
        """
        return "<%s>" % self.__class__.__name__


class BaseASRSigma(BaseASR, metaclass=abc.ABCMeta):
    """
    Extend :class:`BaseASR` and allows to include uncertainties (sigma) in
    rupture magnitude estimation.
    """

    @abc.abstractmethod
    def get_std_dev_mag(self, area, rake):
        """
        Return the standard deviation on the magnitude.

        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """


class BaseMSR(metaclass=abc.ABCMeta):
    """
    A base class for Magnitude-Area Scaling Relationship.
    Allows calculation of rupture area from magnitude.
    """

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

    def __eq__(self, other):
        """
        Two instances of the same class are considered equal
        """
        return self.__class__ is other.__class__

    def __str__(self):
        """
        Returns a TOML representation of the instance
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Returns the name of the class
        """
        return "<%s>" % self.__class__.__name__


class BaseMSRSigma(BaseMSR, metaclass=abc.ABCMeta):
    """
    Extends :class:`BaseMSR` and allows to include uncertainties (sigma) in
    rupture area estimation.
    """

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
