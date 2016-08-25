# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# The Hazard Library
# Copyright (C) 2013-2016 GEM Foundation
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

import copy
import unittest
import numpy

from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo import Mesh, Point, Line, PlanarSurface

PNT1 = Point(-64.78365, -0.45236, 0.0)
PNT2 = Point(-64.80164, -0.45236, 0.0)
PNT3 = Point(-64.90498, -0.36564, 0.0)
PNT4 = Point(-65.00000, -0.16188, 0.0)
PNT5 = Point(-65.00000,  0.00000, 0.0)

AS_ARRAY = numpy.array([[pnt.longitude, pnt.latitude, pnt.depth]
                        for pnt in [PNT1, PNT2, PNT3, PNT4, PNT5]])

class CartesianTestingMultiSurface(MultiSurface):
    """
    For testing the Spudich & Chiou formulation the cartesian coordinates
    will be input manually - so this overwrites the _get_cartesian_edge_set
    method
    """
    def _get_cartesian_edge_set(self):
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
    as_length = lsd / np.tan(np.radians(dip))
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
    dipdir1b = (dipdir1 + 180.) % 360.0
    dipdir2b = (dipdir2 + 180.) % 360.0
    dipdir3b = (dipdir3 + 180.) % 360.0
    dipdir4b = (dipdir4 + 180.) % 360.0

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
    as_length_alt = lsd / np.tan(np.radians(75.0))
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
        PlanarSurface.from_corner_points(1.0, PNT4, PNT5,
            PNT5.point_at(as_length, lsd, dipdir4),
            PNT4.point_at(as_length, lsd, dipdir4)
            )
        ]
    frankel_fault2 = MultiSurface(frankel_discordant)
    return simple_fault1, stirling_fault1, frankel_fault1, frankel_fault2

SFLT1, STIRFLT1, FRANK1, FRANK2 = _setup_peer_test_bending_fault_config()

class MeshDownSamplingTestCase(unittest.TestCase):
    """
    Tests the downsampling algorithm for the Rectangular Mesh test case
    """
    def test_downsample_mesh(self):
        # Use the simple fault case with a tolerance of 1.0 degree
        downsampled_mesh = downsample_mesh(SFLT1.mesh, 1.0)
        # Top edge of downsampled mesh should correspond to the five
        # input points of the simple fault
        
        # Check longitudes
        np.testing.assert_array_almost_equal(downsampled_mesh.lons[0, :-1],
                                             AS_ARRAY[:-1, 0])
        # Check latitude
        np.testing.assert_array_almost_equal(downsampled_mesh.lats[0, :-1],
                                             expected_points[:-1, 1])
        # Check depths
        np.testing.assert_array_almost_equal(downsampled_mesh.depths[0, :-1],
                                             expected_points[:-1, 2])

class TraceDownSamplingTestCase(unittest.TestCase):
    def test_downsample_mesh(self):
        # Use the simple fault case with a tolerance of 1.0 degree
        np.testing.assert_array_almost_equal(
            downsample_trace(SFLT1.mesh, 1.0)[:-1, :],
            AS_ARRAY[:-1, :])


class GC2SetupTestCase(unittest.TestCase):
    def test_spudich_chiou_calculations(self):
        # Verify that the core unit vectors are being correctly calculated
        # and interpreted in the Spudich and Chiou test case



class MultiSurfaceTestCase(unittest.TestCase):
    """
    Tests the basic instantiaion of the MultiSurface Test case
    """
