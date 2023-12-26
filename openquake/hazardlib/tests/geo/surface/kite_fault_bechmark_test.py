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

import os
import unittest
import numpy as np

from openquake.hazardlib.geo.surface.kite_fault import KiteSurface
from openquake.hazardlib.tests.geo.surface.kite_fault_test import (
    _read_profiles, ppp)

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
PLOTTING = False
aae = np.testing.assert_almost_equal


class KiteSurfaceBenchmark(unittest.TestCase):
    """
    """

    def setUp(self):

        # Read the profiles and create the surface
        path = os.path.join(BASE_DATA_PATH, 'profiles_benchmark')
        self.prf, _ = _read_profiles(path)

        if PLOTTING:
            title = 'Profiles'
            #ppp(self.prf, title=title, ax_equal=True)

    def test_mesh(self):

        idl = False
        alg = False
        hsmpl = 4
        vsmpl = 2
        srfc = KiteSurface.from_profiles(self.prf, vsmpl, hsmpl, idl, alg)

        if PLOTTING:
            title = 'Test mesh creation'
            ppp(self.prf, srfc, title, ax_equal=True)
