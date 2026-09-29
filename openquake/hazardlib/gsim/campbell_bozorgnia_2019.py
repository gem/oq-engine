# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
Campbell & Bozorgnia (2019) ground-motion model.
"""
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import add_alias
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014, coeffs_high, coeffs_low)


G_UNIT = 9.80665


class CampbellBozorgnia2019(CampbellBozorgnia2014):
    """
    Campbell & Bozorgnia (2019) model for Arias intensity and CAV.

    Published as "Ground motion models for the horizontal components of
    Arias intensity (AI) and cumulative absolute velocity (CAV) using the
    NGA-West2 database" (Earthquake Spectra, 35(3), 1289-1310, 2019).
    Arias intensity (IA) is in m/s; CAV is in g-sec.
    """
    # Defomed fpr geometric mean so overwrite this on CB14 base class
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        super().compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            if imt.name == 'CAV':
                # Convert from m/s to g-sec
                mean[m] -= np.log(G_UNIT)


add_alias('CampbellBozorgnia2019HighQ', CampbellBozorgnia2019,
          coeffs=coeffs_high)
add_alias('CampbellBozorgnia2019LowQ', CampbellBozorgnia2019,
          coeffs=coeffs_low)
add_alias('CampbellBozorgnia2019JapanSite', CampbellBozorgnia2019,
          SJ=True)
add_alias('CampbellBozorgnia2019HighQJapanSite', CampbellBozorgnia2019,
          coeffs=coeffs_high, SJ=True)
add_alias('CampbellBozorgnia2019LowQJapanSite', CampbellBozorgnia2019,
          coeffs=coeffs_low, SJ=True)