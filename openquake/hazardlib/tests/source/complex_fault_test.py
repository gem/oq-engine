# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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

from openquake.hazardlib.source.complex_fault import (ComplexFaultSource,
                                                      _float_ruptures)
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.tom import PoissonTOM

from openquake.hazardlib.tests.source import simple_fault_test
from openquake.hazardlib.tests.source import \
    _complex_fault_test_data as test_data
from openquake.hazardlib.tests import assert_pickleable


class ComplexFaultSourceSimpleGeometryIterRupturesTestCase(
        simple_fault_test.SimpleFaultIterRupturesTestCase):
    # test that complex fault sources of simple geometry behave
    # exactly the same as simple fault sources of the same geometry
    def _make_source(self, *args, **kwargs):
        source = super(ComplexFaultSourceSimpleGeometryIterRupturesTestCase,
                       self)._make_source(*args, **kwargs)
        surface = SimpleFaultSurface.from_fault_data(
            source.fault_trace, source.upper_seismogenic_depth,
            source.lower_seismogenic_depth, source.dip,
            source.rupture_mesh_spacing
        )
        mesh = surface.get_mesh()
        top_edge = Line(list(mesh[0:1]))
        bottom_edge = Line(list(mesh[-1:]))

        cfs = ComplexFaultSource(
            source.source_id, source.name, source.tectonic_region_type,
            source.mfd, source.rupture_mesh_spacing,
            source.magnitude_scaling_relationship, source.rupture_aspect_ratio,
            source.temporal_occurrence_model, [top_edge, bottom_edge],
            source.rake
        )
        assert_pickleable(cfs)
        return cfs


class ComplexFaultSourceIterRupturesTestCase(
        simple_fault_test._BaseFaultSourceTestCase):

    def _make_source(self, mfd, aspect_ratio, rupture_mesh_spacing, edges):
        source_id = name = 'test-source'
        trt = self.TRT
        rake = self.RAKE
        tom = self.TOM
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = aspect_ratio
        edges = [Line([Point(*coords) for coords in edge])
                 for edge in edges]
        cfs = ComplexFaultSource(
            source_id, name, trt, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio, tom,
            edges, rake
        )
        assert_pickleable(cfs)
        return cfs

    def test_1(self):
        # Complex fault source equivalent to Simple fault source defined
        # by only the top and bottom edges. That is the complex fault surface
        # is equivalent to a simple fault surface defined in the following way:

        # fault_trace = [Point(0.0,0.0,0.0),
        #                Point(0.0,0.0359728811758,0.0),
        #                Point(0.0190775080917,0.0550503815181,0.0),
        #                Point(0.03974514139,0.0723925718855,0.0)]
        # upper_seismo_depth = 0.0
        # lower_seismo_depth = 4.2426406871192848
        # dip = 45.0
        # mesh_spacing = 1.0

        # Being a regular surface and with points in the top and bottom edges
        # with a spacing that is a multiple of the given mesh spacing, the
        # expected mesh spacing is uniform and equal to the mesh_spacing given
        # in the constructor, that is 1 km. Each mesh cell has an area of
        # 1 squared km.

        # In this case the fmd contains only one magnitude (3.5),
        # and this originates ruptures with area equal to 0.3162277660168 km**2
        # (according to PeerTestMagAreaScalingRel area = 10**(3.5-4))
        # given an aspect ratio of 1, the rupture dimensions are:
        # rup_length = sqrt(0.31622776601683794 * 1) = 0.56234132519034907
        # rup_width = 0.56234132519034907
        # Rupture lenght corresponds therefore to two nodes along length, and
        # two nodes along width provides the closest area value, so each
        # rupture extends for two nodes along lenght and 2 nodes along width.
        # Given 11 nodes along lenght, and 7 along width, and assuming the
        # rupture offset to be equal to mesh_spacing, the total number of
        # ruptures along lenght is 10 and along width is 6. So the total number
        # is 60. the rate associated to a magnitude 3.5 from the truncated GR
        # (with bin width = 1.0) is 10**(0.5 -3.0) - 10**(0.5-4.0) =
        # 0.0028460498941515417 the rate associated to each rupture is
        # 0.0028460498941515417 / 60 = 4.7434164902525696e-05
        # for each rupture the probability of one or more occurrences is
        # 1-exp(- 4.7434164902525696e-05 * 50.0) = 0.0023688979672850108
        source = self._make_source(test_data.TEST1_MFD,
                                   test_data.TEST1_RUPTURE_ASPECT_RATIO,
                                   test_data.TEST1_MESH_SPACING,
                                   test_data.TEST1_EDGES)
        self._test_ruptures(test_data.TEST1_RUPTURES, source)

    def test_2(self):
        # Complex fault source equivalent to Simple fault source defined by
        # top, bottom and intermediate edges. That is the complex fault surface
        # is equivalent to a simple fault surface defined in the following way:

        # fault_trace = [Point(0.0,0.0,0.0),
        #                Point(0.0,0.0359728811758,0.0),
        #                Point(0.0190775080917,0.0550503815181,0.0),
        #                Point(0.03974514139,0.0723925718855,0.0)]
        # upper_seismo_depth = 0.0
        # lower_seismo_depth = 4.2426406871192848
        # dip = 45.0
        # mesh_spacing = 1.0

        # Being a regular surface and with points in the top and bottom edges
        # with a spacing that is a multiple of the given mesh spacing, the
        # expected mesh spacing is uniform and equal to the mesh_spacing given
        # in the constructor, that is 1 km. Each mesh cell has an area of
        # 1 squared km.

        # In this case the fmd contains only one magnitude (3.5), and this
        # originates ruptures with area equal to 0.31622776601683794 km**2
        # (according to PeerTestMagAreaScalingRel area = 10**(3.5-4))
        # given an aspect ratio of 1, the rupture dimensions are:
        # rup_length = sqrt(0.31622776601683794 * 1) = 0.56234132519034907
        # rup_width = 0.56234132519034907
        # Rupture lenght corresponds therefore to two nodes along length, and
        # two nodes along width provides the closest area value, so each
        # rupture extends for two nodes along lenght and 2 nodes along width.
        # Given 11 nodes along lenght, and 7 along width, and assuming the
        # rupture offset to be equal to mesh_spacing, the total number
        # of ruptures along lenght is 10 and along width is 6. So the total
        # number is 60. the rate associated to a magnitude 3.5 from the
        # truncated GR (with bin width = 1.0) is 10**(0.5 -3.0) - 10**(0.5-4.0)
        # = 0.0028460498941515417. the rate associated to each rupture is
        # 0.0028460498941515417 / 60 = 4.7434164902525696e-05
        # for each rupture the probability of one or more occurrences is
        # 1-exp(- 4.7434164902525696e-05 * 50.0) = 0.0023688979672850108

        source = self._make_source(test_data.TEST2_MFD,
                                   test_data.TEST2_RUPTURE_ASPECT_RATIO,
                                   test_data.TEST2_MESH_SPACING,
                                   test_data.TEST2_EDGES)
        self._test_ruptures(test_data.TEST2_RUPTURES, source)

    def test_3(self):
        # Complex fault source equivalent to Simple fault source defined by
        # top, bottom and intermediate edges. That is the complex fault surface
        # is equivalent to a simple fault surface defined in the following way:

        # fault_trace = [Point(0.0,0.0,0.0),
        #                Point(0.0,0.0359728811758,0.0),
        #                Point(0.0190775080917,0.0550503815181,0.0),
        #                Point(0.03974514139,0.0723925718855,0.0)]
        # upper_seismo_depth = 0.0
        # lower_seismo_depth = 4.2426406871192848
        # dip = 45.0
        # mesh_spacing = 1.0

        # Being a regular surface and with points in the top and bottom edges
        # with a spacing that is a multiple of the given mesh spacing, the
        # expected mesh spacing is uniform and equal to the mesh_spacing given
        # in the constructor, that is 1 km. Each mesh cell has an area of
        # 1 squared km.

        # In this case the fmd contains only one magnitude (6.5), and this
        # originates ruptures with area equal to 316.22776601683796 km**2
        # (according to PeerTestMagAreaScalingRel area = 10**(6.5-4))
        # assuming an aspect ratio of 1.0, the rupture dimensions are:
        # rup_length = sqrt(316.22776601683796 * 1.0) = 17.782794100389228
        # rup_width = 17.782794100389228
        # rupture dimensions are clipped to fault dimensions In this case each
        # rupture extends for 11 nodes along lenght and 7 nodes along width.
        # The total number of ruptures is 1. the rate associated to a magnitude
        # 6.5 from the truncated GR (bin width = 1) is
        # 10**(0.5 - 6.0) - 10**(0.5 - 7.0) = 2.8460498941515413e-06
        # the rate associated to each rupture is
        # 2.8460498941515413e-06 / 1 = 2.8460498941515413e-06
        # for each rupture the probability of one or more occurrences is
        # 1-exp(- 2.8460498941515413e-06 * 50.0) = 0.00014229237018781316
        source = self._make_source(test_data.TEST3_MFD,
                                   test_data.TEST3_RUPTURE_ASPECT_RATIO,
                                   test_data.TEST3_MESH_SPACING,
                                   test_data.TEST3_EDGES)
        self._test_ruptures(test_data.TEST3_RUPTURES, source)

    def test_4(self):
        # test 4 (Complex fault with top, bottom and intermediate edges with
        # variable length)

        # top edge length = 3 km
        # intermediate edge = 6 km
        # bottom edge = 9 km

        # the spacing between edges along depth is of 1 km. Average lenght is
        # 6 km. Assuming a mesh spacing = 2 km, the number of points per edge
        # is 6 / 2 + 1 = 4. Consequently, top edge has a spacing of 1km,
        # intermediate edge of 2 km, and bottom edge 3km. each cell area is
        # a vertical trapezoid.
        # cells area in the first row is ((1 + 2) / 2) * 1) = 1.5 km**2
        # cells area in the second row is ((2 + 3) / 2 * 1) = 2.5 km**2

        # In this case the fmd contains only one magnitude (4.0),
        # and this originates ruptures with area equal to 1 km**2 (according to
        # PeerTestMagAreaScalingRel area = 10**(4.0-4)). assuming an aspect
        # ratio of 1.0, the rupture dimensions are:
        # rup_length = sqrt(1.0 * 1.0) = 1.0
        # rup_width = 1.0
        #
        # With these setting, 3 ruptures will be generated in the first row,
        # and 3 ruptures in the second row. so the expected total number
        # of rupture is 6. each rupture consists of 4 points.
        #
        # the rate associated to a magnitude 4.0 from the truncated GR (bin
        # width = 0.1) is 10**(0.5 - 3.95) - 10**(0.5 - 4.05) = 7.29750961e-5
        # the rate associated to each rupture is therefore 7.29750961e-5 / 6
        # = 1.216251602e-05
        source = self._make_source(test_data.TEST4_MFD,
                                   test_data.TEST4_RUPTURE_ASPECT_RATIO,
                                   test_data.TEST4_MESH_SPACING,
                                   test_data.TEST4_EDGES)
        self._test_ruptures(test_data.TEST4_RUPTURES, source)


class ComplexFaultSourceRupEnclPolyTestCase(
        simple_fault_test.SimpleFaultRupEncPolyTestCase):
    # test that complex fault sources of simple geometry behave
    # exactly the same as simple fault sources of the same geometry
    def _make_source(self, mfd, aspect_ratio, fault_trace, dip):
        sf = super(ComplexFaultSourceRupEnclPolyTestCase, self)._make_source(
            mfd, aspect_ratio, fault_trace, dip
        )
        # create an equivalent top and bottom edges
        vdist_top = sf.upper_seismogenic_depth
        vdist_bottom = sf.lower_seismogenic_depth

        hdist_top = vdist_top / numpy.tan(numpy.radians(dip))
        hdist_bottom = vdist_bottom / numpy.tan(numpy.radians(dip))

        strike = fault_trace[0].azimuth(fault_trace[-1])
        azimuth = (strike + 90.0) % 360

        top_edge = []
        bottom_edge = []
        for point in fault_trace.points:
            top_edge.append(point.point_at(hdist_top, vdist_top, azimuth))
            bottom_edge.append(point.point_at(hdist_bottom, vdist_bottom,
                                              azimuth))
        edges = [Line(top_edge), Line(bottom_edge)]

        return ComplexFaultSource(
            sf.source_id, sf.name, sf.tectonic_region_type,
            sf.mfd, sf.rupture_mesh_spacing,
            sf.magnitude_scaling_relationship, sf.rupture_aspect_ratio,
            sf.temporal_occurrence_model, edges, sf.rake
        )


class FloatRupturesTestCase(unittest.TestCase):
    def test_reshaping_along_length(self):
        cell_area = numpy.array([[1, 1, 1],
                                 [1, 1, 1]], dtype=float)
        cell_length = numpy.array([[1, 1, 1],
                                   [1, 1, 1]], dtype=float)
        rupture_area = 3.1
        rupture_length = 1.0

        slices = _float_ruptures(rupture_area, rupture_length,
                                 cell_area, cell_length)
        self.assertEqual(len(slices), 2)
        s1, s2 = slices
        self.assertEqual(s1, (slice(0, 3), slice(0, 3)))
        self.assertEqual(s2, (slice(0, 3), slice(1, 4)))

        rupture_area = 4.2
        slices = _float_ruptures(rupture_area, rupture_length,
                                 cell_area, cell_length)
        self.assertEqual(len(slices), 1)
        self.assertEqual(slices, [s1])

    def test_reshaping_along_width(self):
        cell_area = numpy.array([[4, 4],
                                 [4, 4],
                                 [2, 2]], dtype=float)
        cell_length = numpy.array([[2, 2], [2, 2], [2, 2]], dtype=float)
        rupture_area = 13.0
        rupture_length = 12.0

        slices = _float_ruptures(rupture_area, rupture_length,
                                 cell_area, cell_length)
        self.assertEqual(len(slices), 2)
        s1, s2 = slices
        self.assertEqual(s1, (slice(0, 3), slice(0, 3)))
        self.assertEqual(s2, (slice(1, 4), slice(0, 3)))

    def test_varying_width(self):
        cell_area = numpy.array([[1, 1, 1],
                                 [1, 0.1, 1],
                                 [1, 0.1, 1]], dtype=float)
        cell_length = numpy.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]],
                                  dtype=float)
        rupture_area = 2.1
        rupture_length = 1.0

        slices = _float_ruptures(rupture_area, rupture_length,
                                 cell_area, cell_length)
        self.assertEqual(len(slices), 6)
        tl, tm, tr, bl, bm, br = slices
        self.assertEqual(tl, (slice(0, 3), slice(0, 2)))
        self.assertEqual(tm, (slice(0, 4), slice(1, 3)))
        self.assertEqual(tr, (slice(0, 3), slice(2, 4)))
        self.assertEqual(bl, (slice(1, 4), slice(0, 2)))
        self.assertEqual(bm, (slice(1, 4), slice(1, 3)))
        self.assertEqual(br, (slice(1, 4), slice(2, 4)))


class ModifyComplexFaultGeometryTestCase(unittest.TestCase):
    """

    """
    def setUp(self):
        top_edge_1 = Line([Point(30.0, 30.0, 1.0), Point(31.0, 30.0, 1.0)])
        bottom_edge_1 = Line([Point(29.7, 29.9, 30.0),
                              Point(31.3, 29.9, 32.0)])
        self.edges = [top_edge_1, bottom_edge_1]
        self.mfd = EvenlyDiscretizedMFD(7.0, 0.1, [1.0])
        self.aspect = 1.0
        self.spacing = 5.0
        self.rake = 90.

    def _make_source(self, edges):
        source_id = name = 'test-source'
        trt = "Subduction Interface"
        tom = PoissonTOM(50.0)
        magnitude_scaling_relationship = PeerMSR()
        cfs = ComplexFaultSource(
            source_id, name, trt, self.mfd, self.spacing,
            magnitude_scaling_relationship, self.aspect, tom,
            edges, self.rake
        )
        return cfs

    def test_modify_geometry(self):
        fault = self._make_source(self.edges)
        # Modify the edges
        top_edge_2 = Line([Point(29.9, 30.0, 2.0), Point(31.1, 30.0, 2.1)])
        bottom_edge_2 = Line([Point(29.6, 29.9, 29.0),
                              Point(31.4, 29.9, 33.0)])
        fault.modify_set_geometry([top_edge_2, bottom_edge_2], self.spacing)
        exp_lons_top = [29.9, 31.1]
        exp_lats_top = [30.0, 30.0]
        exp_depths_top = [2.0, 2.1]
        exp_lons_bot = [29.6, 31.4]
        exp_lats_bot = [29.9, 29.9]
        exp_depths_bot = [29.0, 33.0]
        for iloc in range(len(fault.edges[0])):
            self.assertAlmostEqual(fault.edges[0].points[iloc].longitude,
                                   exp_lons_top[iloc])
            self.assertAlmostEqual(fault.edges[0].points[iloc].latitude,
                                   exp_lats_top[iloc])
            self.assertAlmostEqual(fault.edges[0].points[iloc].depth,
                                   exp_depths_top[iloc])
        for iloc in range(len(fault.edges[1])):
            self.assertAlmostEqual(fault.edges[1].points[iloc].longitude,
                                   exp_lons_bot[iloc])
            self.assertAlmostEqual(fault.edges[1].points[iloc].latitude,
                                   exp_lats_bot[iloc])
            self.assertAlmostEqual(fault.edges[1].points[iloc].depth,
                                   exp_depths_bot[iloc])
