# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.primary_surf_rup.base` defines abstract base
classes for :class:`BasePrimarySurfRup` and :class:`BaseSecondarySurfDispl`
"""

import abc


class BasePrimarySurfRup(metaclass=abc.ABCMeta):
    """Abstract base class for principal (primary) surface-rupture models.

    Subclasses implement :meth:`get_prob`, returning the probability that a
    rupture reaches the surface as the principal fault trace.
    """

    #: Reference-line treatment this model needs when the source has no
    #: continuous fault trace (multiFaultSource / kite sections); one of
    #: 'lcp', 'ecs', 'segments'. Mirrors hazardlib's REQUIRES_DISTANCES
    #: declarative pattern. Irrelevant for single-strand sources.
    MULTIFAULT_REFERENCE_LINE = "lcp"

    @abc.abstractmethod
    def get_prob(self):
        """
        Return the probability that the rupture will reach the surface
        """

    def __str__(self):
        """
        Returns the name of the class
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Returns the name of the class in angular brackets
        """
        return "<%s>" % self.__class__.__name__


class BaseSecondarySurfDispl(metaclass=abc.ABCMeta):
    """Abstract base class for distributed (secondary) surface-displacement models.

    Subclasses implement :meth:`get_prob`, returning the probability that the
    distributed displacement exceeds a given value (in metres).
    """

    #: See BasePrimarySurfRup.MULTIFAULT_REFERENCE_LINE.
    MULTIFAULT_REFERENCE_LINE = "lcp"

    @abc.abstractmethod
    def get_prob(self):
        """
        Return the probability that the secondary displacement will exceed
        a certain value [m]
        """

    def __str__(self):
        """
        Returns the name of the class
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Returns the name of the class in angular brackets
        """
        return "<%s>" % self.__class__.__name__