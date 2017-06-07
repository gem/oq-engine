# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.ceus2011` implements
:class:`CEUS2011`.
"""
from openquake.hazardlib.scalerel.base import BaseMSR
from openquake.baselib.slots import with_slots


@with_slots
class CEUS2011(BaseMSR):
    """
    Magnitude-Scaling Relationship used for calculations in the CEUS SSC
    project completed in 2011.

    References:
        - CEUS SSC Hazard Input Document - Appendix H, page H-3
        - CEUS SSC Final Report - Chapter 5, page 5-57

    """
    _slots_ = []

    def get_median_area(self, mag, rake):
        """
        Calculates median area as ``10 ** (mag - 4.366)``. Rake is ignored.
        """
        return 10 ** (mag - 4.366)
