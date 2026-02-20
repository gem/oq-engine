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
Module :mod:`openquake.fdha.primary_surf_displ.base` defines the abstract
base class for primary surface fault displacement exceedance models.
"""

import abc


class BasePrimarySurfDispl(metaclass=abc.ABCMeta):
    """
    Abstract base class for models that compute the conditional
    probability of exceeding a given primary surface fault displacement.
    """

    @abc.abstractmethod
    def get_prob(self, d, x_l, mag, rake=0.0):
        """
        Return the conditional probability that primary fault displacement
        exceeds *d* metres, given magnitude and position along the rupture.

        :param d:
            Target displacement(s) in metres, scalar or array-like.
        :param x_l:
            Relative along-strike position x/L (0 = end, 0.5 = centre),
            scalar or array-like.
        :param mag:
            Earthquake moment magnitude (scalar).
        :param rake:
            Rake angle in degrees (scalar), in [-180, 180]. See
            :mod:`openquake.hazardlib.valid` for ``rake_range``.
        :returns:
            Exceedance probability array, shape
            ``(n_displacements, n_sites)``.
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
