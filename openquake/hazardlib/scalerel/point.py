# The Hazard Library
# Copyright (C) 2013 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.point` implements :class:`PointMSR`.
"""
from openquake.hazardlib.scalerel.base import BaseMSR


class PointMSR(BaseMSR):
    """
    Implements magnitude-area scaling relationship to mimic point ruptures.
    Independently of the magnitude value, this scaling relationship returns
    always a very small value (1e-4 squared km, corresponding to a 10 by 10 m
    square) for the median area.
    """
    def get_median_area(self, mag, rake):
        """
        Returns a value equal to 1e-4 squared km independently of ``mag`` and
        ``rake`` values.

        >>> point_msr = PointMSR()
        >>> 1e-4 == point_msr.get_median_area(4.0, 50)
        True
        >>> 1e-4 == point_msr.get_median_area(9.0, 0)
        True
        """
        return 1e-4
