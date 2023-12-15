# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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
import unittest

import numpy

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface

from openquake.hazardlib.tests.geo.surface import _utils as utils


class ComplexFaultSurfaceCheckFaultDataTestCase(utils.SurfaceTestCase):
    def test_one_edge(self):
        edges = [Line([Point(0, 0), Point(0, 1)])]
        self.assertRaises(ValueError, ComplexFaultSurface.from_fault_data,
                          edges, mesh_spacing=1)

    def test_non_positive_mesh_spacing(self):
        edges = [Line([Point(0, 0), Point(0, 1)]),
                 Line([Point(0, 0, 1), Point(0, 1, 1)])]
        self.assertRaises(ValueError, ComplexFaultSurface.from_fault_data,
                          edges, mesh_spacing=0)
        self.assertRaises(ValueError, ComplexFaultSurface.from_fault_data,
                          edges, mesh_spacing=-1)

    def test_dip_left_of_fault_strike_case1(self):
        # checks that an error is raised when fault surface dips left of
        # fault strike (i.e. does not obey to Aki & Richards convention)
        # simple case of planar surface with strike 0 (pointing towards
        # north) but with surface dipping to the west
        edges = [Line([Point(0, 0), Point(0, 1)]),
                 Line([Point(-1, 0, 10), Point(-1, 1, 10)])]

        with self.assertRaises(ValueError) as cm:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=10)
        self.assertEqual(
            'Surface does not conform with Aki & Richards convention',
            str(cm.exception)
        )

    def test_dip_left_of_fault_strike_case2(self):
        # real example taken from wrong fault for japan model
        # ('Kanto earthquake')
        edges = [
            Line([
                Point(139.268, 35.3649682834, 10.6),
                Point(139.579014512, 35.1780000001, 10.6)
            ]),
            Line([
                Point(139.541937161, 35.378, 19.5999999911),
                Point(139.867999999, 35.2135133354, 19.6000000095)]
            )]

        with self.assertRaises(ValueError) as cm:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=10)
        self.assertEqual(
            'Surface does not conform with Aki & Richards convention',
            str(cm.exception)
        )

    def test_dip_left_of_fault_strike_topo(self):
        # when the fault is above sea level
        edges = [
            Line([
                Point(0, 1, -1),
                Point(0, 0, -1)
            ]),
            Line([
                Point(1, 1, 0),
                Point(1, 0, 0)]
            )]

        with self.assertRaises(ValueError) as cm:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=1)
        self.assertEqual(
            'Surface does not conform with Aki & Richards convention',
            str(cm.exception)
        )

    def test_invalid_surface_polygon_case1(self):
        # vertical complex fault with top and bottom edges inverted
        edges = [Line([Point(0, 0), Point(0, 2)]),
                 Line([Point(0, 2, 10), Point(0, 0, 10)])]

        with self.assertRaises(ValueError) as cm:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=10)
        self.assertEqual(
            'Edges points are not in the right order',
            str(cm.exception)
        )

    def test_invalid_surface_polygon_case2(self):
        # inclined complex fault with top and bottom edges inverted
        edges = [Line([Point(0, 0), Point(0, 2)]),
                 Line([Point(0.2, 2, 10), Point(0.6, 0, 10)])]

        with self.assertRaises(ValueError) as cm:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=10)
        self.assertEqual(
            'Edges points are not in the right order',
            str(cm.exception)
        )

    def test_invalid_surface_polygon_case3(self):
        # intermediate edge has opposite strike than top and bottom
        edges = [Line([Point(0, 0), Point(0, 2)]),
                 Line([Point(0.1, 2, 10), Point(0.1, 0, 10)]),
                 Line([Point(0.2, 0, 20), Point(0.2, 2, 20)])]

        with self.assertRaises(ValueError) as cm:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=10)
        self.assertEqual(
            'Edges points are not in the right order',
            str(cm.exception)
        )

    def test_invalid_surface_polygon_topo(self):
        # intermediate edge has opposite strike than top and bottom
        edges = [Line([Point(0, 0, -5), Point(0, 2, -5)]),
                 Line([Point(0, 2, 5), Point(0, 0, 5)])]

        with self.assertRaises(ValueError) as cm:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=1)
        self.assertEqual(
            'Edges points are not in the right order',
            str(cm.exception)
        )


def plot(edges, mesh=None):
    import matplotlib.pyplot as plt
    ax = plt.figure().add_subplot(projection='3d')
    for edge in edges:
        coo = edge.coo
        plt.plot(coo[:, 0], coo[:, 1], coo[:, 2], '-r')

    if mesh is not None:
        coo = mesh.array
        plt.plot(coo[0].flatten(), coo[1].flatten(), coo[2].flatten(), '.b')

    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel('lon')
    ax.set_ylabel('lat')
    plt.show()


class ComplexFaultFromFaultDataTestCase(utils.SurfaceTestCase):

    def test_1(self):
        edge1 = Line([Point(0, 0), Point(0.03, 0)])
        edge2 = Line([Point(0, 0, 2.224), Point(0.03, 0, 2.224)])
        surface = ComplexFaultSurface.from_fault_data([edge1, edge2],
                                                      mesh_spacing=1.112)
        self.assertIsInstance(surface, ComplexFaultSurface)
        self.assert_mesh_is(surface=surface, expected_mesh=[
            [(0, 0, 0), (0.01, 0, 0), (0.02, 0, 0), (0.03, 0, 0)],
            [(0, 0, 1.112), (0.01, 0, 1.112),
             (0.02, 0, 1.112), (0.03, 0, 1.112)],
            [(0, 0, 2.224), (0.01, 0, 2.224),
             (0.02, 0, 2.224), (0.03, 0, 2.224)],
        ], delta=40)
        # plot([edge1, edge2], mesh=surface.mesh)

    def test_2(self):
        # this is a regression test. Reference values have been obtained
        # by extracting mesh from complex surface.
        edge1 = Line([Point(0, 0, 1), Point(0, 0.02, 1)])
        edge2 = Line([Point(0.02, 0, 1.5), Point(0.02, 0.01, 1.5)])
        edge3 = Line([Point(0, 0, 2), Point(0, 0.02, 2)])
        # plot([edge1, edge2, edge3])

        surface = ComplexFaultSurface.from_fault_data([edge1, edge2, edge3],
                                                      mesh_spacing=1.0)
        expected = numpy.array([
            [[0.00000000e+00, 0.00000000e+00, 0.00000000e+00],
             [8.00000005e-03, 8.00000011e-03, 8.00000028e-03],
             [1.60000001e-02, 1.60000001e-02, 1.60000002e-02],
             [8.57028427e-03, 8.53924247e-03, 8.46354157e-03],
             [5.70284230e-04, 5.39242373e-04, 4.63541314e-04]],
            [[0.00000000e+00, 9.90000005e-03, 1.98000001e-02],
             [-2.68595095e-26, 7.92000013e-03, 1.58400003e-02],
             [-1.79063396e-26, 5.94000007e-03, 1.18800001e-02],
             [-2.74067477e-26, 7.78653765e-03, 1.56105473e-02],
             [-3.10016364e-27, 9.76653758e-03, 1.95705472e-02]],
            [[1.00000000e+00, 1.00000000e+00, 1.00000000e+00],
             [1.20000000e+00, 1.20000000e+00, 1.20000000e+00],
             [1.40000000e+00, 1.40000000e+00, 1.40000000e+00],
             [1.78574289e+00, 1.78651894e+00, 1.78841147e+00],
             [1.98574289e+00, 1.98651894e+00, 1.98841147e+00]]])

        numpy.testing.assert_almost_equal(surface.mesh.array, expected)

    def test_mesh_spacing_more_than_two_lengths(self):
        edge1 = Line([Point(0, 0, 0), Point(0, 0.1, 0)])
        edge2 = Line([Point(0, 0, 10), Point(0, 0.1, 20)])
        with self.assertRaises(ValueError) as ar:
            ComplexFaultSurface.from_fault_data([edge1, edge2],
                                                mesh_spacing=27)
        self.assertEqual(
            str(ar.exception),
            'mesh spacing 27.0 km is too big for mean length 13.0 km'
        )

    def test_mesh_spacing_more_than_two_widthss(self):
        edge1 = Line([Point(0, 0, 0), Point(0, 0.2, 0)])
        edge2 = Line([Point(0, 0, 10), Point(0, 0.2, 20)])
        with self.assertRaises(ValueError) as ar:
            ComplexFaultSurface.from_fault_data([edge1, edge2],
                                                mesh_spacing=30.1)
        self.assertEqual(
            str(ar.exception),
            'mesh spacing 30.1 km is too big for mean width 15.0 km'
        )

    def test_surface_crossing_international_date_line(self):
        edge1 = Line([Point(179.95, 0., 0.), Point(-179.95, 0., 0.)])
        edge2 = Line([Point(179.95, 0., 10.), Point(-179.95, 0., 10.)])
        surface = ComplexFaultSurface.from_fault_data([edge1, edge2],
                                                      mesh_spacing=10.)
        self.assert_mesh_is(surface=surface, expected_mesh=[
            [(179.95, 0., 0.), (-179.95, 0., 0.)],
            [(179.95, 0., 10.), (-179.95, 0., 10.)]
        ], delta=150)


class ComplexFaultSurfaceProjectionTestCase(unittest.TestCase):
    def test(self):
        edges = [Line([Point(-3.4, 5.5, 0), Point(-3.9, 5.3, 0)]),
                 Line([Point(-2.4, 4.6, 10), Point(-3.6, 4.9, 20)])]
        polygon = ComplexFaultSurface.surface_projection_from_fault_data(edges)
        elons = [-2.4, -3.6, -3.9, -3.4]
        elats = [4.6,  4.9,  5.3,  5.5]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    # next three tests are ported from simple fault surface tests
    def test_dip_90_three_points(self):
        edges = [Line([Point(1, -20, 30), Point(1, -20.2, 30),
                       Point(2, -19.7, 30)]),
                 Line([Point(1, -20, 50), Point(1, -20.2, 50),
                       Point(2, -19.7, 50)])]
        polygon = ComplexFaultSurface.surface_projection_from_fault_data(edges)
        elons = [1, 1, 2]
        elats = [-20.2, -20., -19.7]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dip_90_two_points(self):
        edges = [Line([Point(2, 2, 10), Point(1, 1, 10)]),
                 Line([Point(2, 2, 20), Point(1, 1, 20)])]
        polygon = ComplexFaultSurface.surface_projection_from_fault_data(edges)
        elons = [1.00003181, 0.99996821, 0.99996819, 1.99996819, 2.00003182,
                 2.00003181]
        elats = [0.99996822, 0.99996819, 1.00003178, 2.0000318, 2.0000318,
                 1.9999682]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dip_90_self_intersection(self):
        edges = [Line([Point(1, -2, 10), Point(2, -1.9, 10),
                       Point(3, -2.1, 10), Point(4, -2, 10)]),
                 Line([Point(1, -2, 20), Point(2, -1.9, 20),
                       Point(3, -2.1, 20), Point(4, -2, 20)])]
        polygon = ComplexFaultSurface.surface_projection_from_fault_data(edges)
        elons = [3., 1., 2., 4.]
        elats = [-2.1, -2., -1.9, -2.]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_edges_with_nonuniform_length(self):
        edges = [Line([Point(1, -20, 30), Point(1, -20.2, 30),
                       Point(2, -19.7, 30), Point(3, -19.5, 30)]),
                 Line([Point(1, -20, 50), Point(1, -20.2, 50),
                       Point(2, -19.7, 50)])]
        polygon = ComplexFaultSurface.surface_projection_from_fault_data(edges)
        elons = [1, 1, 2, 3]
        elats = [-20.2, -20., -19.7, -19.5]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)


class ComplexFaultSurfaceGetWidthTestCase(unittest.TestCase):
    def test_surface_with_variable_width(self):
        edges = [Line([Point(0.1, 0.1, 0),
                       Point(0.459729190252, 0.0999980290582, 0.0),
                       Point(0.819458380482, 0.0999960581553, 0.0)]),
                 Line([Point(0.1, 0.1, 20.0),
                       Point(0.459729190252, 0.0999980290582, 20.0),
                       Point(0.819458380482, 0.0999960581553, 43.0940107676)])]
        surface = ComplexFaultSurface.from_fault_data(edges, mesh_spacing=5.0)
        self.assertAlmostEqual(surface.get_width(), 26.0, places=0)
