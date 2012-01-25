import unittest

from nhe.const import TRT
from nhe.source.point import PointSource
from nhe.mfd import TruncatedGR
from nhe.msr import Peer
from nhe.common.geo import Point
from nhe.common.pmf import PMF
from nhe.common.nodalplane import NodalPlane
from nhe.common.tom import PoissonTOM


class PointSourceRuptureReshapingTestCase(unittest.TestCase):
    def _get_rupture(self, min_mag, max_mag, hypocenter_depth,
                     aspect_ratio, dip):
        source_id = name = 'test-source'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        mfd = TruncatedGR(a_val=2, b_val=1, min_mag=min_mag, max_mag=max_mag,
                          bin_width=1)
        location = Point(0, 0)
        nodal_plane = NodalPlane(strike=45, dip=dip, rake=-123.23)
        nodal_plane_distribution = PMF([(1, nodal_plane)])
        hypocenter_distribution = PMF([(1, hypocenter_depth)])
        upper_seismogenic_depth = 2
        lower_seismogenic_depth = 16
        magnitude_scaling_relationship = Peer()
        rupture_aspect_ratio = aspect_ratio
        point_source = PointSource(
            source_id, name, trt, mfd,
            location, nodal_plane_distribution, hypocenter_distribution,
            upper_seismogenic_depth, lower_seismogenic_depth,
            magnitude_scaling_relationship, rupture_aspect_ratio
        )
        tom = PoissonTOM(time_span=50)
        ruptures = list(point_source.iter_ruptures(tom))
        self.assertEqual(len(ruptures), 1)
        [rupture] = ruptures
        self.assertIs(rupture.source, point_source)
        self.assertEqual(rupture.rake, -123.23)
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

    def test_1_rupture_is_inside(self):
        rupture = self._get_rupture(min_mag=5, max_mag=6, hypocenter_depth=8,
                                    aspect_ratio=1, dip=30)
        self.assertEqual(rupture.mag, 5.5)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 8))
        self.assertAlmostEqual(rupture.probability, 0.0440025182)

        surface = rupture.surface
        self._check_dimensions(surface, 5.623413252, 5.623413252)
        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0333647435005, -0.00239548066924, 6.59414668702
        )))
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            0.00239548107539, 0.0333647434713, 6.59414668702
        )))
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            -0.00239548107539, -0.0333647434713, 9.40585331298
        )))
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0333647435005, 0.00239548066924, 9.40585331298
        )))

    def test_2_rupture_shallower_than_upper_seismogenic_depth(self):
        rupture = self._get_rupture(min_mag=5, max_mag=6, hypocenter_depth=3,
                                    aspect_ratio=1, dip=30)
        self.assertEqual(rupture.mag, 5.5)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 3))
        self.assertAlmostEqual(rupture.probability, 0.0440025182)

        surface = rupture.surface
        self._check_dimensions(surface, 5.623413252, 5.623413252)
        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0288945127134, -0.0068657114195, 2.0
        )))
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            0.00686571229256, 0.028894512506, 2.0
        )))
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            0.00207475040284, -0.0378349743787, 4.81170662595
        )))
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0378349744035, -0.00207474995049, 4.81170662595
        )))

    def test_3_rupture_deeper_than_lower_seismogenic_depth(self):
        rupture = self._get_rupture(min_mag=5, max_mag=6, hypocenter_depth=15,
                                    aspect_ratio=1, dip=30)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 15))

        surface = rupture.surface
        self._check_dimensions(surface, 5.623413252, 5.623413252)
        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0378349744035, 0.00207474995049, 13.188293374
        )))
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            -0.00207475040284, 0.0378349743787, 13.188293374
        )))
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            -0.00686571229256, -0.028894512506, 16.0
        )))
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0288945127134, 0.0068657114195, 16.0
        )))

    def test_4_rupture_wider_than_seismogenic_layer(self):
        rupture = self._get_rupture(min_mag=7, max_mag=8, hypocenter_depth=9,
                                    aspect_ratio=1, dip=30)
        self.assertEqual(rupture.mag, 7.5)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 9))

        surface = rupture.surface
        # in this test we need to increase the tolerance because the rupture
        # created is rather big and float imprecision starts to be noticeable
        self._check_dimensions(surface, 112.93848786315641, 28, delta=2e-3)

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
                                    aspect_ratio=2, dip=90)
        self.assertEqual(rupture.hypocenter, Point(0, 0, 9))

        surface = rupture.surface
        self._check_dimensions(surface, 7.9527072876705063, 3.9763536438352536)

        self.assertAlmostEqual(0, surface.top_left.distance(Point(
            -0.0252862987308, -0.0252862962683, 7.01182317808
        )))
        self.assertAlmostEqual(0, surface.top_right.distance(Point(
            0.0252862987308, 0.0252862962683, 7.01182317808
        )))
        self.assertAlmostEqual(0, surface.bottom_left.distance(Point(
            -0.0252862987308, -0.0252862962683, 10.9881768219
        )))
        self.assertAlmostEqual(0, surface.bottom_right.distance(Point(
            0.0252862987308, 0.0252862962683, 10.9881768219
        )))
