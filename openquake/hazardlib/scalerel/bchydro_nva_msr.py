# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.bchydro_nva_msr` implements
:class:`BCHydroNVAMSR`.
"""
import numpy as np
from openquake.hazardlib.scalerel.base import BaseMSR


class BCHydroNVAMSR(BaseMSR):
    """
    Magnitude-area scaling relationship for the BC Hydro Northern
    Volcanic Arc (NVA) source zone:

    A = exp(2.095 * Mw - 7.883)

    where A is rupture area in km^2.
    """

    def get_median_area(self, mag, rake):
        """
        Return median rupture area (km²) for the given magnitude.

        NOTE: Rake is not used because the relationship is
        style-of-faulting independent.
        """
        return np.exp(2.095 * mag - 7.883)
