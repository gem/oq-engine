# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.point` implements :class:`PointMSR`.
"""
import numpy
from openquake.hazardlib.scalerel.base import BaseMSR


class PointMSR(BaseMSR):
    """
    Implements magnitude-area scaling relationship to mimic point ruptures.
    Independently of the magnitude value, this scaling relationship returns
    always a very small value (1e-4 squared km, corresponding to a 10 by 10 m
    square) for the median area.

    NOTE: This scaling-relationship is meant to be used in area and point
    sources to mimic point ruptures. Is not intended to be used in fault
    sources, as it would require a fault surface discretization step to small
    (less than 10 m, using an aspect ratio equal to 1) which is unfeasible for
    realistic applications.
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
        return numpy.full_like(mag, 1e-4)
