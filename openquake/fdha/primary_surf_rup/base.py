# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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
Module :mod:`openquake.fdha.primary_surf_rup.base` defines the abstract
base class for primary surface rupture probability models.
"""

import abc


class BasePrimarySurfRup(metaclass=abc.ABCMeta):
    """
    Abstract base class for primary surface rupture probability models.
    """

    @abc.abstractmethod
    def get_prob(self, ctx):
        """
        Return the probability that the rupture will reach the surface.

        :param ctx:
            Context object with at least attribute ``mag`` (magnitude).
        :returns:
            Probability as float (scalar) or :class:`numpy.ndarray`.
        """
        pass

    def __str__(self):
        """
        Return a string representation of the instance (class name).

        :returns:
            The class name as string.
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Return a developer-oriented representation of the instance.

        :returns:
            The class name in angular brackets, e.g. ``<ClassName>``.
        """
        return "<%s>" % self.__class__.__name__

