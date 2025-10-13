# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.mfd.base` defines base class for MFD --
:class:`BaseMFD`.
"""
import abc


class BaseMFD(metaclass=abc.ABCMeta):
    """
    Abstract base class for Magnitude-Frequency Distribution function.
    """

    #: The set of modification type names that are supported by an MFD.
    #: Each modification should have a corresponding method named
    #: ``modify_modificationname()`` where the actual modification
    #: logic resides.
    MODIFICATIONS = abc.abstractproperty()

    def modify(self, modification, parameters):
        """
        Apply a single modification to an MFD parameters.

        Reflects the modification method and calls it passing ``parameters``
        as keyword arguments. See also :attr:`MODIFICATIONS`.

        Modifications can be applied one on top of another. The logic
        of stacking modifications is up to a specific MFD implementation.

        :param modification:
            String name representing the type of modification.
        :param parameters:
            Dictionary of parameters needed for modification.
        :raises ValueError:
            If ``modification`` is missing from :attr:`MODIFICATIONS`.
        """
        if modification not in self.MODIFICATIONS:
            raise ValueError('Modification %s is not supported by %s' %
                             (modification, type(self).__name__))
        meth = getattr(self, 'modify_%s' % modification)
        meth(**parameters)
        self.check_constraints()

    @abc.abstractmethod
    def check_constraints(self):
        """
        Check MFD-specific constraints and raise :exc:`ValueError`
        in case of violation.

        This method must be implemented by subclasses.
        """

    @abc.abstractmethod
    def get_annual_occurrence_rates(self):
        """
        Return an MFD annual occurrence rates histogram.

        This method must be implemented by subclasses.

        :return:
            The list of tuples, each tuple containing a pair
            ``(magnitude, occurrence_rate)``. Each pair represents
            a single bin of the histogram with ``magnitude`` being
            the center of the bin. Magnitude values are monotonically
            increasing by value of bin width. ``occurence_rate``
            represents the number of events per year with magnitude
            that falls in between bin's boundaries.
        """

    @abc.abstractmethod
    def get_min_max_mag(self):
        """
        Return the minimum and maximum magnitudes this MFD is defined for.

        This method must be implemented by subclasses.

        :return:
            Magnitude value, float number.
        """

    def __repr__(self):
        """
        Returns the name of the magnitude frequency distribution class
        """
        return "<%s>" % self.__class__.__name__
