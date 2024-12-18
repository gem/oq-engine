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
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo.surface.kite_fault import (
    _angles_diff, _get_resampled_profs)


class AngleDifferenceTest(unittest.TestCase):

    def test_a(self):

        # Simple test
        angle_a = 30
        angle_b = 60
        computed = _angles_diff(angle_a, angle_b)
        expected = -30
        np.testing.assert_allclose(computed, expected)


class ResampledProfile(unittest.TestCase):

    def test_long_running(self):

        # Profiles
        npr = []
        profs = [np.array([[174.8284, -37.2605, 0.],
                           [174.82162199, -37.24227909, 4.53157019],
                           [174.81484726, -37.2240578, 9.06314038],
                           [174.8080758, -37.20583613,  13.59471058],
                           [174.80130762, -37.18761406,  18.12628077]]),
                 np.array([[174.8494, -37.2555, 0.],
                           [174.842622, -37.23727911,   4.53156587],
                           [174.83584728, -37.21905784,   9.06313174],
                           [174.82907583, -37.20083618,  13.59469761],
                           [174.82230764, -37.18261413,  18.12626348]]),
                 np.array([[174.8688, -37.2523, 0.],
                           [174.862022, -37.23407912, 4.5315631],
                           [174.85524729, -37.21585786, 9.06312621],
                           [174.84847584, -37.19763621, 13.59468931],
                           [174.84170766, -37.17941418, 18.12625242]]),
                 np.array([[174.87485, -37.25035, 0.],
                           [174.86807201, -37.23212913, 4.53156142],
                           [174.86129729, -37.21390787, 9.06312284],
                           [174.85452585, -37.19568623, 13.59468426],
                           [174.84775767, -37.17746421, 18.12624568]])]

        # Projection
        west = 174.8013076160937
        east = 174.8748
        north = -37.17746420575008
        south = -37.2605
        proj = geo_utils.OrthographicProjection(west, east, north, south)

        # Sampling distance
        sd = 5.0

        # Run resampling
        idl = False
        ref_idx = 0
        _get_resampled_profs(npr, profs, sd, proj, idl, ref_idx)

