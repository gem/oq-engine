# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`BooreAtkinson2011`,
               :class:`Atkinson2008prime`
"""
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib import const


class BooreAtkinson2011(BooreAtkinson2008):
    """
    Implements GMPE based on the corrections proposed by Gail M. Atkinson
    and D. Boore in 2011 and published as "Modifications to Existing
    Ground-Motion Prediction Equations in Light of New Data " (2011,
    Bulletin of the Seismological Society of America, Volume 101, No. 3,
    pages 1121-1135).
    """
    kind = '2011'


class Atkinson2008prime(BooreAtkinson2008):
    """
    Implements the Boore & Atkinson (2011) adjustment to the Atkinson (2008)
    GMPE (not itself implemented in OpenQuake)
    """
    # GMPE is defined for application to Eastern North America (Stable Crust)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    kind = 'prime'
