# The Hazard Library
# Copyright (C) 2021 GEM Foundation
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

import numpy as np
import unittest
from openquake.hazardlib.geo.surface.kite_fault import _angles_diff


class AngleDifferenceTest(unittest.TestCase):

    def test_a(self):

        # Simple test
        angle_a = 30
        angle_b = 60
        computed = _angles_diff(angle_a, angle_b)
        expected = -30
        np.testing.assert_allclose(computed, expected)
