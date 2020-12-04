# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy as np
from openquake.hazardlib.geo import Point, Line, Mesh
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface


class MultiSurfaceTestCase(unittest.TestCase):

    def setUp(self):

        # First surface
        prf1 = Line([Point(0, 0, 0), Point(0, -0.001, 20.)])
        prf2 = Line([Point(0.15, 0, 0), Point(0.15, -0.001, 20.)])
        prf3 = Line([Point(0.3, 0, 0), Point(0.3, -0.001, 20.)])
        sfcA = KiteSurface.from_profiles([prf1, prf2, prf3], 5., 5.)

        # Second surface
        prf3 = Line([Point(0.32, 0, 0), Point(0.32, 0.001, 20.)])
        prf4 = Line([Point(0.45, 0.15, 0), Point(0.45, 0.1501, 20.)])
        sfcB = KiteSurface.from_profiles([prf3, prf4], 5., 5.)

        self.msrf = MultiSurface([sfcA, sfcB])

        coo = np.array([[-0.1, 0.0], [0.0, 0.1]])
        self.mesh = Mesh(coo[:, 0], coo[:, 1])

    def test_rx(self):
        # Test Rx
        expected = np.array([-3.829952, -13.55452])
        computed = self.msrf.get_rx_distance(self.mesh)
        np.testing.assert_allclose(computed, expected)
