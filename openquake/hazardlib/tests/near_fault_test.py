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
import numpy as np

from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point

from openquake.hazardlib.near_fault import get_xyz_from_ll
from openquake.hazardlib.near_fault import get_plane_equation
from openquake.hazardlib.near_fault import projection_pp
from openquake.hazardlib.near_fault import directp
from openquake.hazardlib.near_fault import vectors2angle
from openquake.hazardlib.near_fault import average_s_rad
from openquake.hazardlib.near_fault import isochone_ratio
from openquake.hazardlib.near_fault import _intersection
from openquake.hazardlib.geo.surface import SimpleFaultSurface


class CoordinateConversionTest(unittest.TestCase):

    def test_get_xyz_from_ll(self):

        projected = Point(5., 6., 0.)
        reference = Point(4., 6., 0.)
        xs, ys, zs = get_xyz_from_ll(projected, reference)
        # The value used for this test is computed using this website
        # http://www.movable-type.co.uk/scripts/latlong.html
        self.assertAlmostEqual(xs, 111.2, delta=2.0)
        self.assertAlmostEqual(ys, 0.1, delta=2.0)
        self.assertAlmostEqual(zs, 0.0, delta=2.0)


class PlaneEquationTest(unittest.TestCase):

    def test_get_plane_equation(self):

        point1 = Point(1, 0, 0)
        point2 = Point(1, 1, 2)
        point3 = Point(2, 1, 3)
        hypo = Point(0, 0, 0)
        nrm, dst = get_plane_equation(point1, point2, point3, hypo)
        # The value used for this test is computed using this website
        # http://keisan.casio.com/exec/system/1223596129 (first,
        # coverted to xyz coordinate)

        self.assertAlmostEqual(dst, -12361.172665611, delta=1)
        self.assertAlmostEqual(nrm[0], -111.16669652676, delta=0.1)
        self.assertAlmostEqual(nrm[1], -222.37855646024, delta=0.1)
        self.assertAlmostEqual(nrm[2], -12363.683697019, delta=0.1)


class ProjectionPpTest(unittest.TestCase):

    def test_projectionpp(self):

        site = Point(1., 0.5, 1.)
        normal = np.array([3., -2., 1.])
        dist_to_plane = 2.
        hypo = Point(0, 0, 0)
        pp = projection_pp(site, normal, dist_to_plane, hypo)
        # The value used for this test is computed using this website
        # http://www.nabla.hr/CG-LinesPlanesIn3DB5.htm#Projection
        self.assertAlmostEqual(pp[0], 64.19, delta=0.1)
        self.assertAlmostEqual(pp[1], 86.94, delta=0.1)
        self.assertAlmostEqual(pp[2], -16.67, delta=0.1)


class IntersectionTest(unittest.TestCase):

    def test_two_segment(self):

        a1 = np.array([0., 0., 0.])
        a2 = np.array([4., 4., 4.])
        b1 = np.array([4., 0., 0.])
        b2 = np.array([0., 4., 4.])

        p_intersect, vector1, vector2, vector3, vector4 = _intersection(a1, a2,
                                                                        b1, b2)
        # The value used for this test is computed by hand.
        self.assertTrue(np.allclose(p_intersect.flatten(), [2., 2., 2.],
                                    atol=0.1))
        self.assertTrue(np.allclose(vector1, [0.58, -0.58, -0.58],
                                    atol=0.1))
        self.assertTrue(np.allclose(vector2, [0.58, -0.58, -0.58],
                                    atol=0.1))
        self.assertTrue(np.allclose(vector3, [0.58, 0.58, 0.58],
                                    atol=0.1))
        self.assertTrue(np.allclose(vector4, [0.58, 0.58, 0.58],
                                    atol=0.1))


class VectorTest(unittest.TestCase):

    def test_angle_two_vectors(self):
        v1 = np.array([3., 4., 0.])
        v2 = np.array([-8., 6., 0.])
        angle = vectors2angle(v1, v2)
        # The value used for this test is computed using this website
        # http://www.vitutor.com/geometry/vec/angle_vectors.html
        # we take the value and convert to radian.
        self.assertAlmostEqual(angle, 1.5708, delta=0.1)


class DppParameterTest(unittest.TestCase):

    def setUp(self):
        upper_seismogenic_depth = 0.
        lower_seismogenic_depth = 15.
        self.hypocentre = Point(10., 45.334898, 10.)
        dip = 90.
        self.delta_slip = 0.
        index_patch = 1
        self.origin = Point(10., 45.2, 0.)
        fault_trace_start = Point(10., 45.2)
        fault_trace_end = Point(10., 45.919457)
        fault_trace = Line([fault_trace_start, fault_trace_end])

        # E Plane Calculation
        self.p0, self.p1, self.p2, self.p3 = SimpleFaultSurface.get_fault_patch_vertices(
            fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
            dip=dip, index_patch=index_patch)

        [self.normal, self.dist_to_plane] = get_plane_equation(
            self.p0, self.p1, self.p2, self.origin)

    def test_dpp_parameter_ss3case_site_a(self):
        site_a = Point(10., 44.57, 0.)
        self.pp = projection_pp(site_a, self.normal, self.dist_to_plane,
                                self.origin)
        pd, e, idx_nxtp = directp(self.p0, self.p1, self.p2, self.p3,
                                  self.hypocentre, self.origin, self.pp)
        fs, rd, r_hyp = average_s_rad(site_a, self.hypocentre, self.origin,
                                      self.pp, self.normal, self.dist_to_plane,
                                      e, self.p0, self.p1, self.delta_slip)
        c_prime = isochone_ratio(e, rd, r_hyp)
        # The value used for this test is from the DPP author Dr. Chiou
        # for the case, ss3, pure strike slip
        self.assertAlmostEqual(fs, 0.9931506, delta=0.1)
        self.assertAlmostEqual(rd, 70.4828, delta=0.1)
        self.assertAlmostEqual(r_hyp, 85.5862, delta=0.1)
        self.assertAlmostEqual(e, 15.1034495, delta=0.1)
        self.assertAlmostEqual(idx_nxtp, 0., delta=0.1)
        self.assertAlmostEqual(c_prime, 4., delta=0.1)

    def test_dpp_parameter_ss3case_site_b(self):
        site_b = Point(10.639652, 45.333116, 0.)
        self.pp = projection_pp(site_b, self.normal, self.dist_to_plane,
                                self.origin)
        pd, e, idx_nxtp = directp(self.p0, self.p1, self.p2, self.p3,
                                  self.hypocentre, self.origin, self.pp)
        fs, rd, r_hyp = average_s_rad(site_b, self.hypocentre, self.origin,
                                      self.pp, self.normal, self.dist_to_plane,
                                      e, self.p0, self.p1, self.delta_slip)
        c_prime = isochone_ratio(e, rd, r_hyp)
        # The value used for this test is from the DPP author Dr. Chiou
        # for the case, ss3, pure strike slip.
        self.assertAlmostEqual(fs, 0.9982396, delta=0.1)
        self.assertAlmostEqual(rd, 50., delta=0.1)
        self.assertAlmostEqual(r_hyp, 50.99, delta=0.1)
        self.assertAlmostEqual(e, 10., delta=0.1)
        self.assertAlmostEqual(c_prime, 0.8688245, delta=0.1)
