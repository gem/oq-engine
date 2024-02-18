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

import os
import unittest
import numpy as np
import matplotlib.pyplot as plt
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.geo.geodetic import point_at
from openquake.hazardlib.geo.surface import (SimpleFaultSurface, MultiSurface,
                                             KiteSurface)
from openquake.hazardlib.tests.geo.line_test import get_mesh, plot_pattern
from openquake.hazardlib.tests.geo.surface.kite_fault_test import plot_mesh_2d

BASE_PATH = os.path.dirname(__file__)
BASE_DATA_PATH = os.path.join(BASE_PATH, 'data')
PLOTTING = False
OVERWRITE = os.environ.get('OQ_OVERWRITE')
SPC = 2
aae = np.testing.assert_almost_equal


class Ry0TestCase(unittest.TestCase):

    def _test_ry0(self, sfc):
        msurf = MultiSurface([sfc])
        mesh, mlons, mlats = get_mesh(-0.2, 0.6, -0.2, 0.3, 0.0025)
        ry0 = msurf.get_ry0_distance(mesh)

        if PLOTTING:
            lons = []
            lats = []
            for sfc in [sfc]:
                trace = sfc.get_tor()
                lons.append(trace[0])
                lats.append(trace[1])
            label = 'test_ry0'
            num = 10
            ax = plot_pattern(lons, lats, np.reshape(ry0, mlons.shape),
                              mlons, mlats, label, num, show=False)
            plot_mesh_2d(ax, msurf.surfaces[0])
            ax.plot(msurf.tor.olon, msurf.tor.olat, 'sg', mfc='none',
                    mec='green')
            plt.show()

        return ry0

    def test_ry0a(self):
        pro1 = Line([Point(0.2, 0.05, 0.0), Point(0.2, 0.0, 15.0)])
        pro2 = Line([Point(0.0, 0.05, 0.0), Point(0.0, 0.0, 15.0)])
        sfc = KiteSurface.from_profiles([pro1, pro2], SPC, SPC)
        ry0 = self._test_ry0(sfc)

        # Saving data
        fname = 'results_multi_simple_ry0a.npz'
        fname = os.path.join(BASE_PATH, 'results', fname)
        if OVERWRITE:
            np.savez_compressed(fname, ry0=ry0)

        # Load expected results and test
        er = np.load(fname)
        aae(er['ry0'], ry0, decimal=1)

    def test_ry0b(self):
        pro1 = Line([Point(0.2, 0.0, 0.0), Point(0.2, 0.05, 15.0)])
        pro2 = Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.05, 15.0)])
        sfc = KiteSurface.from_profiles([pro1, pro2], SPC, SPC)
        ry0 = self._test_ry0(sfc)

        # Saving data
        fname = 'results_multi_simple_ry0b.npz'
        fname = os.path.join(BASE_PATH, 'results', fname)
        if OVERWRITE:
            np.savez_compressed(fname, ry0=ry0)

        # Load expected results and test
        er = np.load(fname)
        aae(er['ry0'], ry0, decimal=1)

    def test_ry0c(self):
        pro1 = Line([Point(0.5, 0.05, 0.0), Point(0.5, 0.1, 15.0)])
        pro2 = Line([Point(0.4, 0.05, 0.0), Point(0.4, 0.1, 15.0)])
        pro3 = Line([Point(0.35, 0.0, 0.0), Point(0.3, 0.05, 15.0)])
        sfc = KiteSurface.from_profiles([pro1, pro2, pro3], SPC, SPC)
        ry0 = self._test_ry0(sfc)

        # Saving data
        fname = 'results_multi_simple_ry0c.npz'
        fname = os.path.join(BASE_PATH, 'results', fname)
        if OVERWRITE:
            np.savez_compressed(fname, ry0=ry0)

        # Load expected results and test
        er = np.load(fname)
        aae(er['ry0'], ry0, decimal=1)


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
        self.msfc = MultiSurface([sfc1, sfc2])

    def test_get_tor(self):
        aae(self.coo1, self.msfc.tor.lines[0].coo[:, 0:2], decimal=2)
        aae(self.coo2, self.msfc.tor.lines[1].coo[:, 0:2], decimal=2)
        aae(self.msfc.tor.soidx, [1, 0])  # there is inversion
        aae(self.msfc.tor.flipped, [False, False])  # but no flip
