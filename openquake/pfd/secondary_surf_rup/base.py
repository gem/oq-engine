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
Module :mod:`openquake.pfd.secondary_surf_rup.base` defines abstract base
classes for :class:`BaseSecondarySurfRup` and :class:`BaseSecondarySurfDispl`
"""

import abc


class BaseSecondarySurfRup(metaclass=abc.ABCMeta):
    """Abstract base class for distributed (secondary) surface-rupture models.

    Subclasses implement :meth:`get_prob`, returning the probability of
    distributed (off-fault) surface rupture at a site.
    """

    #: Reference-line treatment this model needs when the source has no
    #: continuous fault trace (multiFaultSource / kite sections); one of
    #: 'lcp', 'ecs', 'segments'. Mirrors hazardlib's REQUIRES_DISTANCES
    #: declarative pattern. Irrelevant for single-strand sources.
    MULTIFAULT_REFERENCE_LINE = "lcp"

    #: Distributed-contribution pipeline the hazard kernel must route this
    #: model through. ``"generic"`` (default) = the standard adapter path
    #: ``P(SR) x P(FD)``; ``"visini"`` = the combined A/B/C combination +
    #: rank-2 Monte Carlo path in :class:`~openquake.pfd.calc.visini.
    #: VisiniSecondaryCalculator`, which needs site coordinates and rank-1.5
    #: traces the generic interface does not carry. Declared on the model
    #: class so the kernel never matches class names; a Visini subclass or
    #: renamed variant keeps the correct routing automatically.
    SECONDARY_PIPELINE = "generic"

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

    #: See BaseSecondarySurfRup.MULTIFAULT_REFERENCE_LINE.
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