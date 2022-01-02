# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.geo.geodetic import point_at
from openquake.hazardlib.geo.surface import SimpleFaultSurface, MultiSurface


class MultiSurfaceSimpleFaultSurfaceTestCase(unittest.TestCase):
    """
    Test the construction and use of multi fault surfaces based on simple-fault
    surfaces
    """

    def setUp(self):

        mspc = 1.0
        usd = 0.0
        lsd = 15.0
        dip = 80.0
        ffd = SimpleFaultSurface.from_fault_data
        pnt = Point

        # Surface 1
        p1 = point_at(0.0, 0.0, 90.0, 20.0)
        self.coo1 = [[0, 0], [p1[0], p1[1]], [0.3, -0.05]]
        trace = Line([pnt(co[0], co[1]) for co in self.coo1])
        sfc1 = ffd(trace, usd, lsd, dip, mspc)

        # Surface 2
        self.coo2 = [[-0.15, 0.0], [-0.05, 0.0]]
        trace = Line([pnt(co[0], co[1]) for co in self.coo2])
        sfc2 = ffd(trace, usd, lsd, dip, mspc)

        # Multi surface
        self.msfc = MultiSurface([sfc1, sfc2], tol=2.)

    def test_get_tor(self):
        # Set the top of ruptures
        self.msfc._set_tor()

        # Testing
        aae = np.testing.assert_almost_equal
        aae(self.coo1, self.msfc.tors.lines[0].coo[:, 0:2], decimal=2)
        aae(self.coo2, self.msfc.tors.lines[1].coo[:, 0:2], decimal=2)

    def _set_tu(self):
        uut, tut = self.msfc.lines.get_tu

    def test_rx_calculation(self):
        dst = self.msfc.get_rx_distance(self.mesh)
