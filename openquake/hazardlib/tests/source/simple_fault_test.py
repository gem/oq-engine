# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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

from openquake.hazardlib.const import TRT
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD
from openquake.hazardlib.scalerel import PeerMSR, WC1994
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.tom import PoissonTOM

from openquake.hazardlib.tests import assert_angles_equal, assert_pickleable
from openquake.hazardlib.tests.geo.surface._utils import assert_mesh_is
from openquake.hazardlib.tests.source import \
    _simple_fault_test_data as test_data


class _BaseFaultSourceTestCase(unittest.TestCase):
    TRT = TRT.ACTIVE_SHALLOW_CRUST
    RAKE = 0
    TOM = PoissonTOM(50.)

    def _make_source(self, mfd, aspect_ratio, fault_trace=None, dip=45):
        source_id = name = 'test-source'
        trt = self.TRT
        rake = self.RAKE
        rupture_mesh_spacing = 1
        upper_seismogenic_depth = 0
        lower_seismogenic_depth = 4.2426406871192848
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = aspect_ratio
        tom = self.TOM
        if fault_trace is None:
            fault_trace = Line([Point(0.0, 0.0),
                                Point(0.0, 0.0359728811758),
                                Point(0.0190775080917, 0.0550503815181),
                                Point(0.03974514139, 0.0723925718855)])

        sfs = SimpleFaultSource(
            source_id, name, trt, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio, tom,
            upper_seismogenic_depth, lower_seismogenic_depth,
            fault_trace, dip, rake
        )
        assert_pickleable(sfs)
        return sfs

    def _test_ruptures(self, expected_ruptures, source):
        ruptures = list(source.iter_ruptures())
        for rupture in ruptures:
            self.assertIsInstance(rupture, ParametricProbabilisticRupture)
            self.assertIs(rupture.temporal_occurrence_model, self.TOM)
            self.assertIs(rupture.tectonic_region_type, self.TRT)
            self.assertEqual(rupture.rake, self.RAKE)
        self.assertEqual(len(expected_ruptures), source.count_ruptures())
        for i in xrange(len(expected_ruptures)):
            expected_rupture, rupture = expected_ruptures[i], ruptures[i]
            self.assertAlmostEqual(rupture.mag, expected_rupture['mag'])
            self.assertAlmostEqual(rupture.rake, expected_rupture['rake'])
            self.assertAlmostEqual(rupture.occurrence_rate,
                                   expected_rupture['occurrence_rate'])
            assert_mesh_is(self, rupture.surface,
                           expected_rupture['surface'])
            self.assertEqual(rupture.hypocenter,
                             Point(*expected_rupture['hypocenter']))
            assert_angles_equal(self, rupture.surface.get_strike(),
                                expected_rupture['strike'], delta=0.5)
            assert_angles_equal(self, rupture.surface.get_dip(),
                                expected_rupture['dip'], delta=3)


class SimpleFaultIterRupturesTestCase(_BaseFaultSourceTestCase):
    def test_2(self):
        # rupture dimensions are larger then mesh_spacing, number of nodes
        # along strike and dip is even
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=3.0, max_mag=4.0,
                             bin_width=1.0)
        self._test_ruptures(test_data.TEST2_RUPTURES,
                            self._make_source(mfd=mfd, aspect_ratio=1.0))

    def test_3(self):
        # rupture length greater than fault length, number of nodes along
        # length is odd and along width is even
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.0, max_mag=6.0,
                             bin_width=1.0)
        self._test_ruptures(test_data.TEST3_RUPTURES,
                            self._make_source(mfd=mfd, aspect_ratio=4.0))

    def test_4(self):
        # rupture width greater than fault width, number of nodes along
        # length is even, along width is odd
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.4, max_mag=5.5,
                             bin_width=0.1)
        self._test_ruptures(test_data.TEST4_RUPTURES,
                            self._make_source(mfd=mfd, aspect_ratio=0.5))

    def test_5(self):
        # rupture length and width greater than fault length and width
        # respectively
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=6.0, max_mag=7.0,
                             bin_width=1.0)
        self._test_ruptures(test_data.TEST5_RUPTURES,
                            self._make_source(mfd=mfd, aspect_ratio=1.0))

    def test_Pago_VeianoMontaguto(self):
        # regression test
        fault_trace = Line([Point(15.2368, 41.1594), Point(15.1848, 41.1644),
                            Point(15.1327, 41.1694), Point(15.0807, 41.1745),
                            Point(15.0286, 41.1795), Point(14.9765, 41.1846),
                            Point(14.9245, 41.1896), Point(14.8724, 41.1946),
                            Point(14.8204, 41.1997)])
        mfd = EvenlyDiscretizedMFD(min_mag=6.9, bin_width=0.2,
                                   occurrence_rates=[1.0])
        dip = 70.0
        upper_seismogenic_depth = 11.0
        lower_seismogenic_depth = 25.0
        rake = -130
        scalerel = WC1994()
        rupture_mesh_spacing = 5
        rupture_aspect_ratio = 1
        tom = PoissonTOM(10)

        fault = SimpleFaultSource(
            'ITCS057', 'Pago Veiano-Montaguto', TRT.ACTIVE_SHALLOW_CRUST, mfd,
            rupture_mesh_spacing, scalerel, rupture_aspect_ratio, tom,
            upper_seismogenic_depth, lower_seismogenic_depth,
            fault_trace, dip, rake
        )

        self.assertEqual(len(list(fault.iter_ruptures())), 1)


class SimpleFaultParametersChecksTestCase(_BaseFaultSourceTestCase):
    def test_mesh_spacing_too_small(self):
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=0.5, max_mag=1.5,
                             bin_width=1.0)
        with self.assertRaises(ValueError) as ar:
            self._make_source(mfd=mfd, aspect_ratio=1.0)
        self.assertEqual(str(ar.exception),
                         'mesh spacing 1 is too low to represent '
                         'ruptures of magnitude 1.5')

    def test_fault_trace_intersects_itself(self):
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=10, max_mag=20,
                             bin_width=1.0)
        fault_trace = Line([Point(0, 0), Point(0, 1),
                            Point(1, 1), Point(0, 0.5)])
        with self.assertRaises(ValueError) as ar:
            self._make_source(mfd=mfd, aspect_ratio=1, fault_trace=fault_trace)
        self.assertEqual(str(ar.exception), 'fault trace intersects itself')


class SimpleFaultRupEncPolyTestCase(_BaseFaultSourceTestCase):
    mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=10, max_mag=20,
                         bin_width=1.0)

    def test_dip_90_no_dilation(self):
        trace = Line([Point(0.0, 0.0), Point(0.0, 0.04),
                      Point(0.03, 0.05), Point(0.04, 0.06)])
        source = self._make_source(self.mfd, 1, dip=90, fault_trace=trace)
        polygon = source.get_rupture_enclosing_polygon()
        elons = [0, 0, 0.04]
        elats = [0, 0.04, 0.06]
        numpy.testing.assert_allclose(polygon.lons, elons, rtol=0, atol=1e-5)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dip_90_dilated(self):
        trace = Line([Point(-1.0, 2.0), Point(-1.0, 2.04)])
        source = self._make_source(self.mfd, 1, dip=90, fault_trace=trace)
        polygon = source.get_rupture_enclosing_polygon(dilation=4.5)
        elons = [
            -1.0405401, -1.0403452, -1.0397622, -1.0387967, -1.0374580,
            -1.0357589, -1.0337159, -1.0313487, -1.0286799, -1.0286349,
            -1.0256903, -1.0224984, -1.0190897, -1.0154972, -1.0117554,
            -1.0079004, -1.0039693, -1.0000000, -0.9960307, -0.9920996,
            -0.9882446, -0.9845028, -0.9809103, -0.9775016, -0.9743097,
            -0.9713651, -0.9713201, -0.9686513, -0.9662841, -0.9642411,
            -0.9625420, -0.9612033, -0.9602378, -0.9596548, -0.9594599,
            -0.9594609, -0.9596560, -0.9602391, -0.9612048, -0.9625436,
            -0.9642428, -0.9662858, -0.9686531, -0.9713218, -0.9713668,
            -0.9743113, -0.9775031, -0.9809116, -0.9845039, -0.9882454,
            -0.9921002, -0.9960310, -1.0000000, -1.0039690, -1.0078998,
            -1.0117546, -1.0154961, -1.0190884, -1.0224969, -1.0256887,
            -1.0286332, -1.0286782, -1.0313469, -1.0337142, -1.0357572,
            -1.0374564, -1.0387952, -1.0397609, -1.0403440, -1.0405391
        ]
        elats = [
            2.0399995, 2.0439662, 2.0478947, 2.0517472, 2.0554866, 2.0590768,
            2.0624833, 2.0656733, 2.0686160, 2.0686610, 2.0713281, 2.0736940,
            2.0757358, 2.0774338, 2.0787718, 2.0797368, 2.0803196, 2.0805144,
            2.0803196, 2.0797368, 2.0787718, 2.0774338, 2.0757358, 2.0736940,
            2.0713281, 2.0686610, 2.0686160, 2.0656733, 2.0624833, 2.0590768,
            2.0554866, 2.0517472, 2.0478947, 2.0439662, 2.0399995, 1.9999995,
            1.9960328, 1.9921043, 1.9882519, 1.9845126, 1.9809224, 1.9775160,
            1.9743261, 1.9713835, 1.9713385, 1.9686715, 1.9663057, 1.9642640,
            1.9625660, 1.9612281, 1.9602631, 1.9596804, 1.9594856, 1.9596804,
            1.9602631, 1.9612281, 1.9625660, 1.9642640, 1.9663057, 1.9686715,
            1.9713385, 1.9713835, 1.9743261, 1.9775160, 1.9809224, 1.9845126,
            1.9882519, 1.9921043, 1.9960328, 1.9999999
        ]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats, rtol=0, atol=1e-6)

    def test_dip_30_no_dilation(self):
        trace = Line([Point(0.0, 0.0), Point(0.0, 0.04),
                      Point(0.03, 0.05), Point(0.04, 0.06)])
        source = self._make_source(self.mfd, 1, dip=30, fault_trace=trace)
        polygon = source.get_rupture_enclosing_polygon()
        elons = [0.0549872, 0., 0., 0.04, 0.09498719]
        elats = [-0.0366581, 0, 0.04, 0.06, 0.02334187]
        numpy.testing.assert_allclose(polygon.lons, elons, rtol=0, atol=1e-5)
        numpy.testing.assert_allclose(polygon.lats, elats, rtol=0, atol=1e-5)

    def test_dip_30_dilated(self):
        trace = Line([Point(0.0, 0.0), Point(0.0, 0.04),
                      Point(0.03, 0.05), Point(0.04, 0.06)])
        source = self._make_source(self.mfd, 1, dip=30, fault_trace=trace)
        polygon = source.get_rupture_enclosing_polygon(dilation=10)
        elons = [
            0.1298154, 0.1245655, 0.1186454, 0.1121124, 0.1050291,
            0.0974640, 0.0894897, 0.0811832, 0.0726244, 0.0638958,
            0.0550813, 0.0462659, 0.0375346, 0.0289713, 0.0206585,
            0.0126764, 0.0051017, -0.0498855, -0.0569870, -0.0635385,
            -0.0694768, -0.0747446, -0.0792910, -0.0830722, -0.0860516,
            -0.0882006, -0.0894983, -0.0899323, -0.0899323, -0.0894772,
            -0.0881164, -0.0858637, -0.0827419, -0.0787826, -0.0740259,
            -0.0685199, -0.0623203, -0.0554900, -0.0480979, -0.0402191,
            -0.0002190, 0.0076432, 0.0158009, 0.0241796, 0.0327029,
            0.0412927, 0.0498708, 0.0583587, 0.0666790, 0.0747555,
            0.0825147, 0.0898855, 0.1448728, 0.1519670, 0.1585125,
            0.1644462, 0.1697109, 0.1742561, 0.1780378, 0.1810197,
            0.1831731, 0.1844772, 0.1849194, 0.1844956, 0.1832098,
            0.1810743, 0.1781097, 0.1743447, 0.1698154
        ]
        elats = [
            -0.0865436, -0.0936378, -0.1001833, -0.1061170, -0.1113818,
            -0.1159269, -0.1197087, -0.1226906, -0.1248440, -0.1261481,
            -0.1265903, -0.1261665, -0.1248807, -0.1227452, -0.1197807,
            -0.1160156, -0.1114863, -0.0748281, -0.0695722, -0.0636449,
            -0.0571033, -0.0500106, -0.0424352, -0.0344503, -0.0261330,
            -0.0175634, -0.0088243, -0.0000000, 0.0400000, 0.0490364,
            0.0579813, 0.0667442, 0.0752364, 0.0833720, 0.0910686,
            0.0982482, 0.1048383, 0.1107721, 0.1159895, 0.1204378,
            0.1404379, 0.1439098, 0.1466154, 0.1485298, 0.1496358,
            0.1499230, 0.1493889, 0.1480385, 0.1458839, 0.1429450,
            0.1392485, 0.1348282, 0.0981700, 0.0929200, 0.0870000,
            0.0804669, 0.0733837, 0.0658185, 0.0578443, 0.0495378,
            0.0409790, 0.0322503, 0.0234359, 0.0146206, 0.0058892,
            -0.0026741, -0.0109868, -0.0189689, -0.0265436
        ]
        numpy.testing.assert_allclose(polygon.lons, elons, rtol=0, atol=1e-5)
        numpy.testing.assert_allclose(polygon.lats, elats, rtol=0, atol=1e-5)
