# The Hazard Library
# Copyright (C) 2026 GEM Foundation
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
import unittest
import numpy as np

from openquake.hazardlib.scalerel.bchydro_nva_msr import BCHydroNVAMSR


class BCHydroNVAMSRTestCase(unittest.TestCase):
    """
    Tests for the BC Hydro NVA magnitude-area scaling relationship.
    
    Expected values:
        Mw 5.0 ~= 13   km^2
        Mw 6.0 ~= 109  km^2
        Mw 7.0 ~= 882  km^2
        Mw 7.5 ~= 2514 km^2
        Mw 8.0 ~= 7165 km^2
    """

    def test_median_area(self):
        msr = BCHydroNVAMSR()
        mags = np.array([5.0, 6.0, 7.0, 7.5, 8.0])
        expected = np.exp(2.095 * mags - 7.883)
        got = np.array([msr.get_median_area(m, 90) for m in mags])
        np.testing.assert_allclose(got, expected, rtol=1e-10)
