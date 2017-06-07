# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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
"""
Generalized coordinate systems require an additional level of testing under
a variety of fault conditions - we separate these out away from the main
fault surface testing modules
"""

import os
import unittest
import numpy

from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo import Mesh, Point, Line, PlanarSurface,\
    SimpleFaultSurface
from openquake.hazardlib.geo.surface.base import (downsample_mesh,
                                                  downsample_trace)

PNT1 = Point(-64.78365, -0.45236, 0.0)
PNT2 = Point(-64.80164, -0.45236, 0.0)
PNT3 = Point(-64.90498, -0.36564, 0.0)
PNT4 = Point(-65.00000, -0.16188, 0.0)
PNT5 = Point(-65.00000,  0.00000, 0.0)

AS_ARRAY = numpy.array([[pnt.longitude, pnt.latitude, pnt.depth]
                        for pnt in [PNT1, PNT2, PNT3, PNT4, PNT5]])


class CartesianTestingMultiSurface(MultiSurface):
    """
    This test surface is used to verify the values given by Spudich & Chiou
    in their report. Here, the fault is built directly from the cartesian
    points so we over-ride the call to the function to render the coordinates
    to cartesian
    """
    def _get_cartesian_edge_set(self):
        return None

    def _get_gc2_coordinates_for_rupture(self, edge_sets):
        pass


def _setup_peer_test_bending_fault_config():
    """
    The GC2 tests will be based on variations of the PEER bending fault
    test case:

    (Fault is dipping east north east
    Point 5 (-65.0, 0.0, 0.0)
        o
        |
        |
        |
        o Point 4 (-65.0, -0.16188, 0)
         \
          \
           \
            \
             \
              o Point 3 (-64.90498, -0.36564, 0.0)
               \__
                  \__
                     \__
                        \__
                           \__Point 2 (-64.80164, -0.45236, 0.0)
                              \o---o Point 1 (-64.78365, -0.45236, 0.0)
    """
    # Build separate faults
    # Get down-dip points - dipping east-noth-east
    strike1 = PNT1.azimuth(PNT2)
    dipdir1 = (strike1 + 90.) % 360.0

    strike2 = PNT2.azimuth(PNT3)
    dipdir2 = (strike2 + 90.) % 360.0

    strike3 = PNT3.azimuth(PNT4)
    dipdir3 = (strike3 + 90.) % 360.0

    strike4 = PNT4.azimuth(PNT5)
    dipdir4 = (strike4 + 90.) % 360.0

    global_strike = PNT1.azimuth(PNT5)
    global_dipdir = (global_strike + 90.) % 360.0
    # Get lower trace
    usd = 0.0
    lsd = 12.0
    dip = 60.0
    as_length = lsd / numpy.tan(numpy.radians(dip))
    PNT1b = PNT1.point_at(as_length, lsd, global_dipdir)
    PNT2b = PNT2.point_at(as_length, lsd, global_dipdir)
    PNT3b = PNT3.point_at(as_length, lsd, global_dipdir)
    PNT4b = PNT4.point_at(as_length, lsd, global_dipdir)
    PNT5b = PNT5.point_at(as_length, lsd, global_dipdir)
    # As simple fault dipping east
    mesh_spacing = 0.5
    simple_fault1 = SimpleFaultSurface.from_fault_data(
        Line([PNT1, PNT2, PNT3, PNT4, PNT5]), usd, lsd, dip, mesh_spacing)
    # As a set of planes describing a concordant "Stirling fault"
    stirling_planes = [
        PlanarSurface.from_corner_points(1.0, PNT1, PNT2, PNT2b, PNT1b),
        PlanarSurface.from_corner_points(1.0, PNT2, PNT3, PNT3b, PNT2b),
        PlanarSurface.from_corner_points(1.0, PNT3, PNT4, PNT4b, PNT3b),
        PlanarSurface.from_corner_points(1.0, PNT4, PNT5, PNT5b, PNT4b)
    ]
    stirling_fault1 = MultiSurface(stirling_planes)

    # As a set of planes describing a concordant "Frankel Fault"
    # In the Frankel fault each segment is projected to the local dip direction
    dipdir2b = (dipdir2 + 180.) % 360.0

    frankel_planes = [
        PlanarSurface.from_corner_points(
            1.0, PNT1, PNT2,
            PNT2.point_at(as_length, lsd, dipdir1),
            PNT1.point_at(as_length, lsd, dipdir1)
            ),
        PlanarSurface.from_corner_points(
            1.0, PNT2, PNT3,
            PNT3.point_at(as_length, lsd, dipdir2),
            PNT2.point_at(as_length, lsd, dipdir2)
            ),
        PlanarSurface.from_corner_points(
            1.0, PNT3, PNT4,
            PNT4.point_at(as_length, lsd, dipdir3),
            PNT3.point_at(as_length, lsd, dipdir3)
            ),
        PlanarSurface.from_corner_points(
            1.0, PNT4, PNT5,
            PNT5.point_at(as_length, lsd, dipdir4),
            PNT4.point_at(as_length, lsd, dipdir4)
            )
        ]
    frankel_fault1 = MultiSurface(frankel_planes)

    # Test the case of a discordant Frankel plane
    # Swapping the strike of the second segment to change the dip direction
    # Also increasing the dip from 60 degrees to 75 degrees
    as_length_alt = lsd / numpy.tan(numpy.radians(75.0))
    frankel_discordant = [
        PlanarSurface.from_corner_points(
            1.0, PNT1, PNT2,
            PNT2.point_at(as_length, lsd, dipdir1),
            PNT1.point_at(as_length, lsd, dipdir1)
            ),
        PlanarSurface.from_corner_points(
            1.0, PNT3, PNT2,
            PNT2.point_at(as_length_alt, lsd, dipdir2b),
            PNT3.point_at(as_length_alt, lsd, dipdir2b)
            ),
        PlanarSurface.from_corner_points(
            1.0, PNT3, PNT4,
            PNT4.point_at(as_length, lsd, dipdir3),
            PNT3.point_at(as_length, lsd, dipdir3)
            ),
        PlanarSurface.from_corner_points(
            1.0, PNT4, PNT5,
            PNT5.point_at(as_length, lsd, dipdir4),
            PNT4.point_at(as_length, lsd, dipdir4)
            )
        ]
    frankel_fault2 = MultiSurface(frankel_discordant)
    return simple_fault1, stirling_fault1, frankel_fault1, frankel_fault2

SFLT1, STIRFLT1, FRANK1, FRANK2 = _setup_peer_test_bending_fault_config()


class TraceDownSamplingTestCase(unittest.TestCase):
    """
    Tests the downsampling algorithm for the Rectangular Mesh test case
    """
    def test_downsample_trace(self):
        # Use the simple fault case with a tolerance of 1.0 degree
        downsampled_trace = downsample_trace(SFLT1.mesh, 1.0)
        # Top edge of downsampled mesh should correspond to the five
        # points of the simple fault
        # Check longitudes
        numpy.testing.assert_array_almost_equal(downsampled_trace[:, 0],
                                                AS_ARRAY[:, 0],
                                                5)
        # Check latitude
        numpy.testing.assert_array_almost_equal(downsampled_trace[:, 1],
                                                AS_ARRAY[:, 1],
                                                5)
        # Check depths
        numpy.testing.assert_array_almost_equal(downsampled_trace[:, 2],
                                                AS_ARRAY[:, 2],
                                                5)


class MeshDownSamplingTestCase(unittest.TestCase):
    """
    Tests the downsample algorithm for the mesh
    """
    def test_downsample_mesh(self):
        # Use the simple fault case with a tolerance of 1.0 degree
        numpy.testing.assert_array_almost_equal(
            downsample_mesh(SFLT1.mesh, 1.0).lons[0, :],
            AS_ARRAY[:, 0],
            5)
        numpy.testing.assert_array_almost_equal(
            downsample_mesh(SFLT1.mesh, 1.0).lats[0, :],
            AS_ARRAY[:, 1],
            5)
        numpy.testing.assert_array_almost_equal(
            downsample_mesh(SFLT1.mesh, 1.0).depths[0, :],
            AS_ARRAY[:, 2],
            5)


class GC2SetupTestCase(unittest.TestCase):
    """
    Tests the basic setup of the GC2 system for a fault by verifying the
    against the formulation example in the Spudich & Chiou (2015) report
    """
    def setUp(self):
        p1 = numpy.array([2., 2., 0.])
        p2 = numpy.array([3.00, 3.732, 0.])
        p3 = numpy.array([6.654, 3.328, 0.])
        p4 = numpy.array([7.939, 4.860, 0.])
        p5 = numpy.array([4.000, 4.165, 0.])
        p6 = numpy.array([0.0, 0.0, 0.])
        p7 = numpy.array([1.0, 0.0, 0.])
        p8 = numpy.array([1.0, 1.0, 0.])
        p9 = numpy.array([2.0, 1.0, 0.])
        # Defines three traces
        trace1 = numpy.vstack([p1, p2])
        trace2 = numpy.vstack([p3, p4, p5])
        trace3 = numpy.vstack([p6, p7, p8, p9])
        self.model = CartesianTestingMultiSurface(STIRFLT1.surfaces)
        self.model.cartesian_edges = [trace1, trace2, trace3]
        self.model.cartesian_endpoints = [numpy.vstack([p1, p2]),
                                          numpy.vstack([p3, p5]),
                                          numpy.vstack([p6, p9])]

    def test_spudich_chiou_calculations(self):
        """
        Verify that the core unit vectors are being correctly calculated
        and interpreted in the Spudich and Chiou test case - presented in
        page 6 of Spudich & Chiou
        """
        self.model._setup_gc2_framework()
        # Test GC2 configuration params
        numpy.testing.assert_array_almost_equal(
            self.model.gc2_config["b_hat"], numpy.array([0.948, 0.318]), 3)
        numpy.testing.assert_array_almost_equal(
            self.model.gc2_config["a_hat"], numpy.array([0.894, 0.447]), 3)
        numpy.testing.assert_array_almost_equal(
            self.model.gc2_config["ejs"],
            numpy.array([1.669, -1.999, 2.236]),
            3)
        self.assertAlmostEqual(self.model.gc2_config["e_tot"], 1.9059, 4)
        numpy.testing.assert_array_almost_equal(self.model.p0,
                                                numpy.array([0., 0.]))


CONCORDANT_FILE = os.path.join(os.path.dirname(__file__),
                               "GC2Test_Concordant.csv")


DISCORDANT_FILE = os.path.join(os.path.dirname(__file__),
                               "GC2Test_Discordant.csv")


class ConcordantSurfaceTestCase(unittest.TestCase):
    """
    Tests the verification of the GC2 module for the Concordant Test case
    """
    def setUp(self):
        self.data = numpy.genfromtxt(CONCORDANT_FILE, delimiter=",")
        self.mesh = Mesh(self.data[:, 0], self.data[:, 1], self.data[:, 2])
        self.model = MultiSurface(FRANK1.surfaces)

    def test_gc2_coords(self):
        """
        Verifies the GC2U, GC2T coordinate for the concordant case
        """
        expected_t = self.data[:, 3]
        expected_u = self.data[:, 4]
        gc2t, gc2u = self.model.get_generalised_coordinates(self.mesh.lons,
                                                            self.mesh.lats)
        numpy.testing.assert_array_almost_equal(expected_t, gc2t)
        numpy.testing.assert_array_almost_equal(expected_u, gc2u)

    def test_gc2_rx(self):
        """
        Verifies Rx for the concordant case
        """
        expected_rx = self.data[:, 5]
        r_x = self.model.get_rx_distance(self.mesh)
        numpy.testing.assert_array_almost_equal(expected_rx, r_x)

    def test_gc2_ry0(self):
        """
        Verifies Ry0 for the concordant case
        """
        expected_ry0 = self.data[:, 6]
        ry0 = self.model.get_ry0_distance(self.mesh)
        numpy.testing.assert_array_almost_equal(expected_ry0, ry0)


class DiscordantSurfaceTestCase(unittest.TestCase):
    """
    Tests the verification of the GC2 module for the Concordant Test case
    """
    def setUp(self):
        self.data = numpy.genfromtxt(DISCORDANT_FILE, delimiter=",")
        self.mesh = Mesh(self.data[:, 0], self.data[:, 1], self.data[:, 2])
        self.model = MultiSurface(FRANK2.surfaces)
