# The Hazard Library
# Copyright (C) 2016-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.mfd.evenly_discretized` defines an evenly
discretized MFD.
"""
from openquake.hazardlib.mfd.base import BaseMFD
from openquake.baselib.slots import with_slots


@with_slots
class ArbitraryMFD(BaseMFD):
    """
    An arbitrary MFD is defined as a list of tuples of magnitude values and
    their corresponding rates

    :param magnitudes:
        List of magnitudes
    :param occurrence_rates:
        The list of non-negative float values representing the actual
        annual occurrence rates. The resulting histogram has as many bins
        as this list length.
    """
    MODIFICATIONS = set(('set_mfd',))
    _slots_ = 'magnitudes occurrence_rates'.split()

    def __init__(self, magnitudes, occurrence_rates):
        self.magnitudes = magnitudes
        self.occurrence_rates = occurrence_rates

        self.check_constraints()

    def check_constraints(self):
        """
        Checks the following constraints:

        * Magnitude list and occurrence rate lists are the same length
        * Occurrence rates list is not empty.
        * Each number in occurrence rates list is non-negative.
        * Minimum magnitude is positive.
        """
        if not self.occurrence_rates:
            raise ValueError('at least one bin must be specified')

        if not all(value >= 0 for value in self.occurrence_rates):
            raise ValueError('all occurrence rates must not be negative')

        if not any(value > 0 for value in self.occurrence_rates):
            raise ValueError('at least one occurrence rate must be positive')
        if not len(self.magnitudes) == len(self.occurrence_rates):
            raise ValueError(
                'lists of magnitudes and rates must have same length')

    def get_annual_occurrence_rates(self):
        """
        Returns the predefined annual occurrence rates.
        """
        return list(zip(self.magnitudes, self.occurrence_rates))

    def get_min_max_mag(self):
        """
        Returns the minumun and maximum magnitudes
        """
        return min(self.magnitudes), max(self.magnitudes)

    def modify_set_mfd(self, magnitudes, occurrence_rates):
        """
        Applies absolute modification of the MFD from the ``magnitudes``,
        ``occurrence_rates`` modification.

        :param magnitudes:
            List of magnitudes
        :param occurrence_rates:
            The list of non-negative float values representing the actual
            annual occurrence rates. The resulting histogram has as many bins
            as this list length.
        """
        self.magnitudes = magnitudes
        self.occurrence_rates = occurrence_rates
        self.check_constraints()
