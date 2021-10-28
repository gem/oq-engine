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

import os
import unittest
import numpy as np
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.tests.geo.surface.kite_fault_test import (
    _read_profiles)
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

aae = np.testing.assert_almost_equal


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
        expected = np.array([-3.48946183, -13.37945338])
        computed = self.msrf.get_rx_distance(self.mesh)
        print(computed)
        np.testing.assert_allclose(computed, expected)


class MultiSurfaceWithNaNsTestCase(unittest.TestCase):

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles08')

        hsmpl = 5
        vsmpl = 5
        idl = False
        alg = False

        prf, _ = _read_profiles(path, 'cs_50')
        srfc50 = KiteSurface.from_profiles(prf, vsmpl, hsmpl, idl, alg)

        prf, _ = _read_profiles(path, 'cs_51')
        srfc51 = KiteSurface.from_profiles(prf, vsmpl, hsmpl, idl, alg)

        coo = []
        step = 0.5
        for lo in np.arange(-74, -68, step):
            for la in np.arange(17, 20, step):
                coo.append([lo, la])
        coo = np.array(coo)
        mesh = Mesh(coo[:, 0], coo[:, 1])
        # Define multisurface and mesh of sites
        self.msrf = MultiSurface([srfc50, srfc51])
        self.mesh = mesh

    def test_get_edge_set(self):
        expected = [np.array([[-70.33000000, 19.70999225, 18.85470701],
                              [-70.37757843, 19.71499279, 18.80781578],
                              [-70.42469786, 19.71993234, 18.76092455],
                              [-70.47228216, 19.72490775, 18.71357360],
                              [-70.51940739, 19.72982240, 18.66668237],
                              [-70.56699755, 19.73477266, 18.61933142]]),
                    np.array([[-70.14910059, 19.72872782, 19.03202972],
                              [-70.19665495, 19.72535393, 18.92804926],
                              [-70.24420731, 19.72196743, 18.82406879],
                              [-70.29175767, 19.71856832, 18.72008833],
                              [-70.33930601, 19.7151566 , 18.61610787]])]

        # Note that method is executed when the object is initialized
        ess = self.msrf.edge_set
        for es, expct in zip(ess, expected):
            print(repr(es))
            np.testing.assert_array_almost_equal(es, expct)

    # TODO
    def test_get_cartesian_edge_set(self):
        es = self.msrf._get_cartesian_edge_set()

    # TODO
    def test_get_strike(self):
        strike = self.msrf.get_strike()

    def test_get_dip(self):
        dip = self.msrf.get_dip()
        expected = 69.93523808772397
        msg = 'Multi fault surface: dip is wrong'
        aae(dip, expected, err_msg=msg)

    # TODO
    def test_get_width(self):
        width = self.msrf.get_width()
        print(width)

    # TODO
    def test_get_area(self):
        area = self.msrf.get_area()

    # TODO
    def test_get_bounding_box(self):
        bb = self.msrf.get_bounding_box()

    # TODO
    def test_get_middle_point(self):
        midp = self.msrf.get_middle_point()

    # TODO remove NaNs
    def test_get_surface_boundaries(self):
        bnd = self.msrf.get_surface_boundaries()

    # TODO test the updated attributes
    def test_setup_gc2_framework(self):
        gc2f = self.msrf._setup_gc2_framework()

    # TODO
    def test_get_gc2_coordinates_for_rupture(self):
        es = self.msrf._get_cartesian_edge_set()
        gc2c = self.msrf._get_gc2_coordinates_for_rupture(es)

    # TODO
    def test_get_generalised_coordinates(self):
        gcoo = self.msrf.get_generalised_coordinates(self.mesh.lons,
                                                     self.mesh.lats)

    # TODO fix the error
    def test_get_rx(self):
        dsts = self.msrf.get_rx_distance(self.mesh)

    # TODO fix the error
    def test_get_ry0(self):
        dsts = self.msrf.get_ry0_distance(self.mesh)
