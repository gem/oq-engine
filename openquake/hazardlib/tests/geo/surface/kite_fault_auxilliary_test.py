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
from openquake.hazardlib.geo.geodetic import npoints_towards
from openquake.hazardlib.geo.surface.kite_fault import (
    _get_dip_strike_directions, _angles_diff)


class PlaneTest(unittest.TestCase):

    def test_get_strike_dip(self):

        # Build the mesh of point
        strike = 43.0
        pnts = np.array(npoints_towards(10.0, 45.0, 0.0, strike, 40, 0, 3)).T
        coo = np.empty((len(pnts), 5, 3))
        for i_pnt, pnt in enumerate(pnts):
            dip_dir = strike + 90.0
            tmp = npoints_towards(pnt[0], pnt[1], 0.0, dip_dir, 20, 10, 5)
            coo[i_pnt, :, 0] = tmp[0]
            coo[i_pnt, :, 1] = tmp[1]
            coo[i_pnt, :, 2] = tmp[2]
        coo = coo.reshape(-1, 3)
        # msh = Mesh.from_points_list([Point(c[0], c[1], c[2]) for c in coo])

        # Dip angle
        # dip_angle = np.rad2deg(np.arctan(10.0 / 20.0))

        # Get strike and dip
        strike_dir_computed, dip_dir_computed = _get_dip_strike_directions(coo)

        # Test for strike
        msg = 'Strike value is wrong'
        dff = np.abs(_angles_diff(strike, strike_dir_computed))
        self.assertTrue(dff < 5, msg)


class AngleDifferenceTest(unittest.TestCase):

    def test_a(self):

        # Simple test
        angle_a = 30
        angle_b = 60
        computed = _angles_diff(angle_a, angle_b)
        expected = -30
        np.testing.assert_allclose(computed, expected)
