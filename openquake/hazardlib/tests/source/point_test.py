from __future__ import division
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
from decimal import Decimal

import numpy

from openquake.hazardlib.const import TRT
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.geo import Point, PlanarSurface, NodalPlane, Polygon
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc import filters
from openquake.hazardlib.site import \
    Site, SiteCollection, FilteredSiteCollection

from openquake.hazardlib.tests.geo.surface import \
    _planar_test_data as planar_surface_test_data
from openquake.hazardlib.tests import assert_pickleable


def make_point_source(lon=1.2, lat=3.4, **kwargs):
    default_arguments = {
        'source_id': 'source_id', 'name': 'source name',
        'tectonic_region_type': TRT.SUBDUCTION_INTRASLAB,
        'mfd': TruncatedGRMFD(a_val=1, b_val=2, min_mag=3,
                              max_mag=5, bin_width=1),
        'location': Point(lon, lat, 5.6),
        'nodal_plane_distribution': PMF([(1, NodalPlane(1, 2, 3))]),
        'hypocenter_distribution': PMF([(1, 4)]),
        'upper_seismogenic_depth': 1.3,
        'lower_seismogenic_depth': 4.9,
        'magnitude_scaling_relationship': PeerMSR(),
        'rupture_aspect_ratio': 1.333,
        'rupture_mesh_spacing': 1.234,
        'temporal_occurrence_model': PoissonTOM(50.)
    }
    default_arguments.update(kwargs)
    kwargs = default_arguments
    ps = PointSource(**kwargs)
    assert_pickleable(ps)
    return ps


class PointSourceCreationTestCase(unittest.TestCase):
    def make_point_source(self, **kwargs):
        source = make_point_source(**kwargs)
        for key in kwargs:
            self.assertIs(getattr(source, key), kwargs[key])

    def assert_failed_creation(self, exc, msg, **kwargs):
        with self.assertRaises(exc) as ae:
            self.make_point_source(**kwargs)
        self.assertEqual(str(ae.exception), msg)

    def test_non_positive_rupture_mesh_spacing(self):
        msg = 'rupture mesh spacing must be positive'
        self.assert_failed_creation(ValueError, msg, rupture_mesh_spacing=-0.1)
        self.assert_failed_creation(ValueError, msg, rupture_mesh_spacing=0)

    def test_lower_depth_above_upper_depth(self):
        self.assert_failed_creation(
            ValueError,
            'lower seismogenic depth must be below upper seismogenic depth',
            upper_seismogenic_depth=10, lower_seismogenic_depth=8
        )

    def test_lower_depth_equal_to_upper_depth(self):
        self.assert_failed_creation(
            ValueError,
            'lower seismogenic depth must be below upper seismogenic depth',
            upper_seismogenic_depth=10, lower_seismogenic_depth=10
        )

    def test_upper_depth_inside_topo_range(self):
        self.assert_failed_creation(
            ValueError,
            "Upper seismogenic depth must be greater than the maximum "
            "elevation on Earth's surface (-8.848 km)",
            upper_seismogenic_depth=-10
        )

    def test_hypocenter_depth_out_of_seismogenic_layer(self):
        self.assert_failed_creation(
            ValueError,
            'depths of all hypocenters must be in between '
            'lower and upper seismogenic depths',
            upper_seismogenic_depth=3, lower_seismogenic_depth=8,
            hypocenter_distribution=PMF([(Decimal('0.3'), 4),
                                         (Decimal('0.7'), 8.001)])
        )

    def test_negative_aspect_ratio(self):
        self.assert_failed_creation(
            ValueError,
            'rupture aspect ratio must be positive',
            rupture_aspect_ratio=-1
        )

    def test_zero_aspect_ratio(self):
        self.assert_failed_creation(
            ValueError,
            'rupture aspect ratio must be positive',
            rupture_aspect_ratio=0
        )

    def test_successfull_creation(self):
        self.make_point_source()

    def test_upper_depth_topo(self):
        self.make_point_source(upper_seismogenic_depth=-2)


class PointSourceIterRupturesTestCase(unittest.TestCase):
    def _get_rupture(self, min_mag, max_mag, hypocenter_depth,
                     aspect_ratio, dip, rupture_mesh_spacing,
                     upper_seismogenic_depth=2,
                     lower_seismogenic_depth=16):
        source_id = name = 'test-source'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        mfd = TruncatedGRMFD(a_val=2, b_val=1, min_mag=min_mag,
                             max_mag=max_mag, bin_width=1)
        location = Point(0, 0)
        nodal_plane = NodalPlane(strike=45, dip=dip, rake=-123.23)
        nodal_plane_distribution = PMF([(1, nodal_plane)])
        hypocenter_distribution = PMF([(1, hypocenter_depth)])
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = aspect_ratio
        tom = PoissonTOM(time_span=50)
        point_source = PointSource(
            source_id, name, trt, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio, tom,
            upper_seismogenic_depth, lower_seismogenic_depth,
            location, nodal_plane_distribution, hypocenter_distribution
        )
        ruptures = list(point_source.iter_ruptures())
        self.assertEqual(len(ruptures), 1)
        [rupture] = ruptures
        self.assertIs(rupture.temporal_occurrence_model, tom)
        self.assertIs(rupture.tectonic_region_type, trt)
        self.assertEqual(rupture.rake, nodal_plane.rake)
        self.assertIsInstance(rupture.surface, PlanarSurface)
        self.assertEqual(rupture.surface.mesh_spacing, rupture_mesh_spacing)
        return rupture

    def _check_dimensions(self, surface, length, width, delta=1e-3):
        length_top = surface.top_left.distance(surface.top_right)
        length_bottom = surface.bottom_left.distance(surface.bottom_right)
        self.assertAlmostEqual(length_top, length_bottom, delta=delta)
        self.assertAlmostEqual(length_top, length, delta=delta)

        width_left = surface.top_left.distance(surface.bottom_left)
        width_right = surface.top_right.distance(surface.bottom_right)
        self.assertAlmostEqual(width_left, width_right, delta=delta)
        self.assertAlmostEqual(width_right, width, delta=delta)
        self.assertAlmostEqual(width, surface.width, delta=delta)
        self.assertAlmostEqual(length, surface.length, delta=delta)

    def test_1_rupture_is_inside(self):
        rupture = self._get_rupture(min_mag=5, max_mag=6, hypocenter_depth=8,
                                    aspect_ratio=1, dip=30,
                                    rupture_mesh_spacing=1)
        self.assertEqual(rupture.mag, 5.5)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 8))
        self.assertAlmostEqual(rupture.occurrence_rate, 0.0009)

        surface = rupture.surface
        self._check_dimensions(surface, 5.623413252, 5.623413252, delta=0.01)
        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0333647435005, -0.00239548066924, 6.59414668702
        )), places=5)
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            0.00239548107539, 0.0333647434713, 6.59414668702
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            -0.00239548107539, -0.0333647434713, 9.40585331298
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0333647435005, 0.00239548066924, 9.40585331298
        )), places=5)

    def test_2_rupture_shallower_than_upper_seismogenic_depth(self):
        rupture = self._get_rupture(min_mag=5, max_mag=6, hypocenter_depth=3,
                                    aspect_ratio=1, dip=30,
                                    rupture_mesh_spacing=10)
        self.assertEqual(rupture.mag, 5.5)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 3))
        self.assertAlmostEqual(rupture.occurrence_rate, 0.0009)

        surface = rupture.surface
        self._check_dimensions(surface, 5.623413252, 5.623413252, delta=0.01)
        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0288945127134, -0.0068657114195, 2.0
        )), places=5)
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            0.00686571229256, 0.028894512506, 2.0
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            0.00207475040284, -0.0378349743787, 4.81170662595
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0378349744035, -0.00207474995049, 4.81170662595
        )), places=5)

    def test_3_rupture_deeper_than_lower_seismogenic_depth(self):
        rupture = self._get_rupture(min_mag=5, max_mag=6, hypocenter_depth=15,
                                    aspect_ratio=1, dip=30,
                                    rupture_mesh_spacing=10)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 15))

        surface = rupture.surface
        self._check_dimensions(surface, 5.623413252, 5.623413252, delta=0.02)
        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0378349744035, 0.00207474995049, 13.188293374
        )), places=5)
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            -0.00207475040284, 0.0378349743787, 13.188293374
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            -0.00686571229256, -0.028894512506, 16.0
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0288945127134, 0.0068657114195, 16.0
        )), places=5)

    def test_4_rupture_wider_than_seismogenic_layer(self):
        rupture = self._get_rupture(min_mag=7, max_mag=8, hypocenter_depth=9,
                                    aspect_ratio=1, dip=30,
                                    rupture_mesh_spacing=10)
        self.assertEqual(rupture.mag, 7.5)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 9))

        surface = rupture.surface
        # in this test we need to increase the tolerance because the rupture
        # created is rather big and float imprecision starts to be noticeable
        self._check_dimensions(surface, 112.93848786315641, 28, delta=0.2)

        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.436201680751, -0.281993828512, 2.0
        )), delta=0.003)  # actual to expected distance is 296 cm
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            0.282002000777, 0.43619639753, 2.0
        )), delta=0.003)  # 52 cm
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            -0.282002000777, -0.43619639753, 16.0
        )), delta=0.003)  # 133 cm
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.436201680751, 0.281993828512, 16.0
        )), delta=0.003)  # 23 cm

    def test_5_vertical_rupture(self):
        rupture = self._get_rupture(min_mag=5, max_mag=6, hypocenter_depth=9,
                                    aspect_ratio=2, dip=90,
                                    rupture_mesh_spacing=4)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 9))

        surface = rupture.surface
        self._check_dimensions(surface, 7.9527072876705063, 3.9763536438352536,
                               delta=0.02)

        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0252862987308, -0.0252862962683, 7.01182317808
        )), places=5)
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            0.0252862987308, 0.0252862962683, 7.01182317808
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            -0.0252862987308, -0.0252862962683, 10.9881768219
        )), places=5)
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0252862987308, 0.0252862962683, 10.9881768219
        )), places=5)

    def test_7_many_ruptures(self):
        source_id = name = 'test7-source'
        trt = TRT.VOLCANIC
        mag1 = 4.5
        mag2 = 5.5
        mag1_rate = 9e-3
        mag2_rate = 9e-4
        hypocenter1 = 9.0
        hypocenter2 = 10.0
        hypocenter1_weight = Decimal('0.8')
        hypocenter2_weight = Decimal('0.2')
        nodalplane1 = NodalPlane(strike=45, dip=90, rake=0)
        nodalplane2 = NodalPlane(strike=0, dip=45, rake=10)
        nodalplane1_weight = Decimal('0.3')
        nodalplane2_weight = Decimal('0.7')
        upper_seismogenic_depth = 2
        lower_seismogenic_depth = 16
        rupture_aspect_ratio = 2
        rupture_mesh_spacing = 0.5
        location = Point(0, 0)
        magnitude_scaling_relationship = PeerMSR()
        tom = PoissonTOM(time_span=50)

        mfd = EvenlyDiscretizedMFD(min_mag=mag1, bin_width=(mag2 - mag1),
                                   occurrence_rates=[mag1_rate, mag2_rate])
        nodal_plane_distribution = PMF([(nodalplane1_weight, nodalplane1),
                                        (nodalplane2_weight, nodalplane2)])
        hypocenter_distribution = PMF([(hypocenter1_weight, hypocenter1),
                                       (hypocenter2_weight, hypocenter2)])
        point_source = PointSource(
            source_id, name, trt, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio, tom,
            upper_seismogenic_depth, lower_seismogenic_depth,
            location, nodal_plane_distribution, hypocenter_distribution
        )
        actual_ruptures = list(point_source.iter_ruptures())
        self.assertEqual(len(actual_ruptures),
                         point_source.count_ruptures())
        expected_ruptures = {
            (mag1, nodalplane1.rake, hypocenter1): (
                # probabilistic rupture's occurrence rate
                9e-3 * 0.3 * 0.8,
                # rupture surface corners
                planar_surface_test_data.TEST_7_RUPTURE_1_CORNERS
            ),
            (mag2, nodalplane1.rake, hypocenter1): (
                9e-4 * 0.3 * 0.8,
                planar_surface_test_data.TEST_7_RUPTURE_2_CORNERS
            ),
            (mag1, nodalplane2.rake, hypocenter1): (
                9e-3 * 0.7 * 0.8,
                planar_surface_test_data.TEST_7_RUPTURE_3_CORNERS
            ),
            (mag2, nodalplane2.rake, hypocenter1): (
                9e-4 * 0.7 * 0.8,
                planar_surface_test_data.TEST_7_RUPTURE_4_CORNERS
            ),
            (mag1, nodalplane1.rake, hypocenter2): (
                9e-3 * 0.3 * 0.2,
                planar_surface_test_data.TEST_7_RUPTURE_5_CORNERS
            ),
            (mag2, nodalplane1.rake, hypocenter2): (
                9e-4 * 0.3 * 0.2,
                planar_surface_test_data.TEST_7_RUPTURE_6_CORNERS
            ),
            (mag1, nodalplane2.rake, hypocenter2): (
                9e-3 * 0.7 * 0.2,
                planar_surface_test_data.TEST_7_RUPTURE_7_CORNERS
            ),
            (mag2, nodalplane2.rake, hypocenter2): (
                9e-4 * 0.7 * 0.2,
                planar_surface_test_data.TEST_7_RUPTURE_8_CORNERS
            )
        }
        for actual_rupture in actual_ruptures:
            expected_occurrence_rate, expected_corners = expected_ruptures[
                (actual_rupture.mag, actual_rupture.rake,
                 actual_rupture.hypocenter.depth)
            ]
            self.assertTrue(isinstance(actual_rupture,
                ParametricProbabilisticRupture))
            self.assertEqual(actual_rupture.occurrence_rate,
                             expected_occurrence_rate)
            self.assertIs(actual_rupture.temporal_occurrence_model, tom)
            self.assertEqual(actual_rupture.tectonic_region_type, trt)
            surface = actual_rupture.surface

            tl, tr, br, bl = expected_corners
            self.assertEqual(tl, surface.top_left)
            self.assertEqual(tr, surface.top_right)
            self.assertEqual(bl, surface.bottom_left)
            self.assertEqual(br, surface.bottom_right)

    def test_high_magnitude(self):
        rupture = self._get_rupture(min_mag=9, max_mag=10, hypocenter_depth=8,
                                    aspect_ratio=1, dip=90,
                                    rupture_mesh_spacing=1)
        self.assertEqual(rupture.mag, 9.5)
        rupture = self._get_rupture(min_mag=9, max_mag=10, hypocenter_depth=40,
                                    aspect_ratio=1, dip=90,
                                    rupture_mesh_spacing=1,
                                    upper_seismogenic_depth=0,
                                    lower_seismogenic_depth=150)
        self.assertEqual(rupture.mag, 9.5)

    def test_rupture_close_to_south_pole(self):
        # data taken from real example and causing "surface's angles are not
        # right" error
        mfd = EvenlyDiscretizedMFD(
            min_mag=5., bin_width=0.1, occurrence_rates=[2.180e-07]
        )
        nodal_plane_dist = PMF([(1., NodalPlane(135., 20., 90.))])
        src = PointSource(source_id='1', name='pnt', tectonic_region_type='asc',
                 mfd=mfd, rupture_mesh_spacing=1,
                 magnitude_scaling_relationship=WC1994(),
                 rupture_aspect_ratio=1.,
                 temporal_occurrence_model=PoissonTOM(50.),
                 upper_seismogenic_depth=0, lower_seismogenic_depth=26,
                 location=Point(-165.125, -83.600),
                 nodal_plane_distribution=nodal_plane_dist,
                 hypocenter_distribution=PMF([(1., 9.)]))
        ruptures = list(src.iter_ruptures())
        self.assertEqual(len(ruptures), 1)


class PointSourceMaxRupProjRadiusTestCase(unittest.TestCase):
    def test(self):
        mfd = TruncatedGRMFD(a_val=1, b_val=2, min_mag=3,
                             max_mag=5, bin_width=1)
        np_dist = PMF([(0.5, NodalPlane(1, 20, 3)),
                       (0.5, NodalPlane(2, 2, 4))])
        source = make_point_source(nodal_plane_distribution=np_dist, mfd=mfd)
        radius = source._get_max_rupture_projection_radius()
        self.assertAlmostEqual(radius, 1.2830362)

        mfd = TruncatedGRMFD(a_val=1, b_val=2, min_mag=5,
                             max_mag=6, bin_width=1)
        np_dist = PMF([(0.5, NodalPlane(1, 40, 3)),
                       (0.5, NodalPlane(2, 30, 4))])
        source = make_point_source(nodal_plane_distribution=np_dist, mfd=mfd)
        radius = source._get_max_rupture_projection_radius()
        self.assertAlmostEqual(radius, 3.8712214)


class PointSourceRupEncPolygon(unittest.TestCase):
    def test_no_dilation(self):
        mfd = TruncatedGRMFD(a_val=1, b_val=2, min_mag=3,
                             max_mag=5, bin_width=1)
        np_dist = PMF([(1, NodalPlane(0, 2, 4))])
        source = make_point_source(nodal_plane_distribution=np_dist, mfd=mfd)
        polygon = source.get_rupture_enclosing_polygon()
        self.assertIsInstance(polygon, Polygon)
        elons = [
            1.2115590, 1.2115033, 1.2113368, 1.2110612, 1.2106790, 1.2101940,
            1.2096109, 1.2089351, 1.2081734, 1.2073329, 1.2064218, 1.2054488,
            1.2044234, 1.2033554, 1.2022550, 1.2011330, 1.2000000, 1.1988670,
            1.1977450, 1.1966446, 1.1955766, 1.1945512, 1.1935782, 1.1926671,
            1.1918266, 1.1910649, 1.1903891, 1.1898060, 1.1893210, 1.1889388,
            1.1886632, 1.1884967, 1.1884410, 1.1884967, 1.1886631, 1.1889387,
            1.1893209, 1.1898058, 1.1903890, 1.1910647, 1.1918265, 1.1926670,
            1.1935781, 1.1945511, 1.1955765, 1.1966446, 1.1977449, 1.1988670,
            1.2000000, 1.2011330, 1.2022551, 1.2033554, 1.2044235, 1.2054489,
            1.2064219, 1.2073330, 1.2081735, 1.2089353, 1.2096110, 1.2101942,
            1.2106791, 1.2110613, 1.2113369, 1.2115033, 1.2115590
        ]
        elats = [
            3.3999999, 3.3988689, 3.3977489, 3.3966505, 3.3955843, 3.3945607,
            3.3935894, 3.3926799, 3.3918409, 3.3910805, 3.3904060, 3.3898238,
            3.3893397, 3.3889582, 3.3886831, 3.3885169, 3.3884614, 3.3885169,
            3.3886831, 3.3889582, 3.3893397, 3.3898238, 3.3904060, 3.3910805,
            3.3918409, 3.3926799, 3.3935894, 3.3945607, 3.3955843, 3.3966505,
            3.3977489, 3.3988689, 3.3999999, 3.4011309, 3.4022510, 3.4033494,
            3.4044156, 3.4054392, 3.4064105, 3.4073200, 3.4081590, 3.4089194,
            3.4095940, 3.4101761, 3.4106603, 3.4110418, 3.4113169, 3.4114831,
            3.4115386, 3.4114831, 3.4113169, 3.4110418, 3.4106603, 3.4101761,
            3.4095940, 3.4089194, 3.4081590, 3.4073200, 3.4064105, 3.4054392,
            3.4044156, 3.4033494, 3.4022510, 3.4011309, 3.3999999
        ]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dilated(self):
        mfd = TruncatedGRMFD(a_val=1, b_val=2, min_mag=3,
                             max_mag=5, bin_width=1)
        np_dist = PMF([(1, NodalPlane(0, 2, 4))])
        source = make_point_source(nodal_plane_distribution=np_dist, mfd=mfd)
        polygon = source.get_rupture_enclosing_polygon(dilation=20)
        self.assertIsInstance(polygon, Polygon)
        elons = [
            1.3917408, 1.3908138, 1.3880493, 1.3834740, 1.3771320, 1.3690846,
            1.3594093, 1.3481992, 1.3355624, 1.3216207, 1.3065082, 1.2903704,
            1.2733628, 1.2556490, 1.2373996, 1.2187902, 1.2000000, 1.1812098,
            1.1626004, 1.1443510, 1.1266372, 1.1096296, 1.0934918, 1.0783793,
            1.0644376, 1.0518008, 1.0405907, 1.0309154, 1.0228680, 1.0165260,
            1.0119507, 1.0091862, 1.0082592, 1.0091788, 1.0119361, 1.0165049,
            1.0228411, 1.0308838, 1.0405556, 1.0517635, 1.0643995, 1.0783420,
            1.0934567, 1.1095979, 1.1266103, 1.1443298, 1.1625858, 1.1812023,
            1.2000000, 1.2187977, 1.2374142, 1.2556702, 1.2733897, 1.2904021,
            1.3065433, 1.3216580, 1.3356005, 1.3482365, 1.3594444, 1.3691162,
            1.3771589, 1.3834951, 1.3880639, 1.3908212, 1.3917408
        ]
        elats = [
            3.3999810, 3.3812204, 3.3626409, 3.3444213, 3.3267370, 3.3097585,
            3.2936490, 3.2785638, 3.2646481, 3.2520357, 3.2408482, 3.2311932,
            3.2231637, 3.2168369, 3.2122738, 3.2095182, 3.2085967, 3.2095182,
            3.2122738, 3.2168369, 3.2231637, 3.2311932, 3.2408482, 3.2520357,
            3.2646481, 3.2785638, 3.2936490, 3.3097585, 3.3267370, 3.3444213,
            3.3626409, 3.3812204, 3.3999810, 3.4187420, 3.4373226, 3.4555440,
            3.4732305, 3.4902120, 3.5063247, 3.5214135, 3.5353329, 3.5479490,
            3.5591401, 3.5687983, 3.5768308, 3.5831599, 3.5877248, 3.5904815,
            3.5914033, 3.5904815, 3.5877248, 3.5831599, 3.5768308, 3.5687983,
            3.5591401, 3.5479490, 3.5353329, 3.5214135, 3.5063247, 3.4902120,
            3.4732305, 3.4555440, 3.4373226, 3.4187420, 3.3999810
        ]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)


class PointSourceSourceFilterTestCase(unittest.TestCase):
    SITES = [
        Site(Point(2.0, 0.0), 0.1, True, 3, 4),  # on epicenter
        Site(Point(2.1, 0.0), 1, True, 3, 4),  # 11.1 km away
        Site(Point(2.0, -0.15), 2, True, 3, 4),  # 16.7 km away
        Site(Point(2.0, 4.49), 3, True, 3, 4),  # 499.3 km away
        Site(Point(2.0, -4.5), 4, True, 3, 4),  # 500.3 km away
    ]

    def setUp(self):
        super(PointSourceSourceFilterTestCase, self).setUp()
        self.sitecol = SiteCollection(self.SITES)

        self.source1 = make_point_source(
            mfd=EvenlyDiscretizedMFD(min_mag=5, bin_width=1,
                                     occurrence_rates=[1]),
            rupture_aspect_ratio=1.9,
            upper_seismogenic_depth=0,
            lower_seismogenic_depth=18.5,
            magnitude_scaling_relationship=PeerMSR(),
            nodal_plane_distribution=PMF([
                (0.5, NodalPlane(strike=1, dip=2, rake=3)),
                (0.5, NodalPlane(strike=1, dip=20, rake=3)),
            ]),
            location=Point(2.0, 0.0),
        )
        self.source2 = make_point_source(
            mfd=EvenlyDiscretizedMFD(min_mag=6.5, bin_width=1,
                                     occurrence_rates=[1]),
            rupture_aspect_ratio=0.5,
            upper_seismogenic_depth=0,
            lower_seismogenic_depth=18.5,
            magnitude_scaling_relationship=PeerMSR(),
            nodal_plane_distribution=PMF([
                (0.5, NodalPlane(strike=1, dip=10, rake=3)),
                (0.5, NodalPlane(strike=1, dip=20, rake=3)),
            ]),
            location=Point(2.0, 0.0),
        )

    def test_zero_integration_distance(self):
        filtered = self.source1.filter_sites_by_distance_to_source(
            integration_distance=0, sites=self.sitecol
        )
        self.assertIsInstance(filtered, FilteredSiteCollection)
        self.assertIsNot(filtered, self.sitecol)
        numpy.testing.assert_array_equal(filtered.indices, [0])
        numpy.testing.assert_array_equal(filtered.vs30, [0.1])

        filtered = self.source2.filter_sites_by_distance_to_source(
            integration_distance=0, sites=self.sitecol
        )
        numpy.testing.assert_array_equal(filtered.indices, [0, 1])

    def test_fifty_km(self):
        filtered = self.source1.filter_sites_by_distance_to_source(
            integration_distance=50, sites=self.sitecol
        )
        numpy.testing.assert_array_equal(filtered.indices, [0, 1, 2])

        filtered = self.source2.filter_sites_by_distance_to_source(
            integration_distance=50, sites=self.sitecol
        )
        numpy.testing.assert_array_equal(filtered.indices, [0, 1, 2])

    def test_495_km(self):
        filtered = self.source1.filter_sites_by_distance_to_source(
            integration_distance=495, sites=self.sitecol
        )
        numpy.testing.assert_array_equal(filtered.indices, [0, 1, 2])

        filtered = self.source2.filter_sites_by_distance_to_source(
            integration_distance=495, sites=self.sitecol
        )
        self.assertIs(filtered, self.sitecol)  # nothing filtered

    def test_filter_all_out(self):
        self.source1.location.latitude = 13.6
        for int_dist in (0, 1, 10, 100, 1000):
            filtered = self.source1.filter_sites_by_distance_to_source(
                integration_distance=int_dist, sites=self.sitecol
            )
            self.assertIs(filtered, None)


class PointSourceRuptureFilterTestCase(unittest.TestCase):
    SITES = PointSourceSourceFilterTestCase.SITES

    def setUp(self):
        super(PointSourceRuptureFilterTestCase, self).setUp()
        self.hypocenter = Point(2, 0, 50)
        self.sitecol = SiteCollection(self.SITES)

    def _make_rupture(self, width, length, dip):
        mid_left = self.hypocenter.point_at(length / 2.0, 0, azimuth=270)
        mid_right = self.hypocenter.point_at(length / 2.0, 0, azimuth=90)
        hwidth = width * numpy.cos(numpy.radians(dip)) / 2.0
        vwidth = width * numpy.sin(numpy.radians(dip)) / 2.0
        top_left = mid_left.point_at(hwidth, -vwidth, azimuth=0)
        bottom_left = mid_left.point_at(hwidth, vwidth, azimuth=180)
        top_right = mid_right.point_at(hwidth, -vwidth, azimuth=0)
        bottom_right = mid_right.point_at(hwidth, vwidth, azimuth=180)
        surface = PlanarSurface(1, 2, dip, top_left, top_right,
                                bottom_right, bottom_left)
        rupture = ParametricProbabilisticRupture(
            mag=1, rake=2, tectonic_region_type=TRT.VOLCANIC,
            hypocenter=self.hypocenter, surface=surface,
            source_typology=PointSource, occurrence_rate=3,
            temporal_occurrence_model=PoissonTOM(1)
        )
        return rupture

    def test_zero_integration_distance(self):
        rup = self._make_rupture(10, 15, 45)
        # the JB distances are [8.29156163, 5.05971598, 15.13297135,
        # 495.78630103, 496.89812309], so given that the integration
        # distance is 0 all sites are filtered out
        filtered = filters.filter_sites_by_distance_to_rupture(
            rup, integration_distance=0, sites=self.sitecol
        )
        self.assertIs(filtered, None)

    def test_495_km(self):
        rup = self._make_rupture(7, 10, 30)
        # the JB distance area [5.84700762, 6.8290327, 14.53519629,
        # 496.25926891, 497.37116174] so given that the integration
        # distance is 495 only the first 3 sites are kept
        filtered = filters.filter_sites_by_distance_to_rupture(
            rup, integration_distance=495, sites=self.sitecol
        )
        expected_filtered = SiteCollection(self.SITES[:3])
        numpy.testing.assert_array_equal(filtered.indices, [0, 1, 2])
        numpy.testing.assert_array_equal(
            filtered.vs30, expected_filtered.vs30
        )
        numpy.testing.assert_array_equal(
            filtered.vs30measured, expected_filtered.vs30measured
        )
        numpy.testing.assert_array_equal(
            filtered.z1pt0, expected_filtered.z1pt0
        )
        numpy.testing.assert_array_equal(
            filtered.z2pt5, expected_filtered.z2pt5
        )
        numpy.testing.assert_array_equal(
            filtered.mesh.lons, expected_filtered.mesh.lons
        )
        numpy.testing.assert_array_equal(
            filtered.mesh.lats, expected_filtered.mesh.lats
        )
        numpy.testing.assert_array_equal(
            filtered.mesh.depths, expected_filtered.mesh.depths
        )

    def test_filter_all_out(self):
        rup = self._make_rupture(50, 80, 9)
        # the JB distances are [47.0074159, 37.99716685, 40.7944923,
        #  476.2521365, 477.36015879]
        for int_dist in (0, 1, 10, 20, 37.99):
            filtered = filters.filter_sites_by_distance_to_rupture(
                rup, integration_distance=int_dist, sites=self.sitecol
            )
            self.assertIs(filtered, None)
