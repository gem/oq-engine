# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2024 GEM Foundation
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
Module :mod:`openquake.hazardlib.fdha.base` defines abstract base
classes for :class:`PrimarySurfRup <BasePrimarySurfRup>`   
"""

import abc


class BasePrimarySurfRup(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_prob(self):
        """
        Return the probability that the rupture will reach the surface
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


class BaseSecondarySurfDispl(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_prob(self):
        """
        Return the probability that the secondary displacement will exceed 
        a certain value [m]
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