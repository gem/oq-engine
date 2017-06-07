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
from copy import deepcopy
from openquake.baselib.python3compat import range
from openquake.hazardlib.const import TRT
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD
import openquake.hazardlib.mfd.evenly_discretized as mfdeven
import openquake.hazardlib.scalerel.base as msr
import openquake.hazardlib.tom as tom
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
        for i in range(len(expected_ruptures)):
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
                         'mesh spacing 1 is too high to represent '
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


class HypoLocSlipRupture(unittest.TestCase):

    def setUp(self):
        # Set the source property

        self.src_mfd = mfdeven.EvenlyDiscretizedMFD(7.5, 1., [1.])
        self.src_msr = msr.BaseMSR
        self.src_tom = tom.PoissonTOM(50)
        self.sarea = WC1994()
        self.upper_seismogenic_depth = 0.
        self.lower_seismogenic_depth = 40.
        self.dip = 90.
        self.rake = 0.
        self.mesh_spacing = 1.
        self.fault_trace_start = Point(0.0, 0.0)
        self.fault_trace_end = Point(1.0, 0.0)
        self.fault_trace_nodes = [self.fault_trace_start, self.fault_trace_end]
        # Set the fault trace

        self.fault_trace = Line(self.fault_trace_nodes)

    def test_hypoloc_vertical_rupture(self):
        source_id = name = 'test-source'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        hypo_list = numpy.array([[0.25, 0.25, 0.4], [0.75, 0.75, 0.6]])
        slip_list = numpy.array([[90., 1.]])
        src = SimpleFaultSource(source_id, name, trt,
                                self.src_mfd, self.mesh_spacing,
                                self.sarea, 1., self.src_tom,
                                self.upper_seismogenic_depth,
                                self.lower_seismogenic_depth,
                                self.fault_trace, self.dip,
                                self.rake, hypo_list, slip_list)

        lon = [0.11691180881629422, 0.35972864251163345, 0.12590502487907043,
               0.36872185857443507, 0.13489824094187208, 0.37771507463723675,
               0.14389145700464828, 0.38670829070001295, 0.15288467306744993,
               0.39570150676281457, 0.16187788913025158, 0.40469472282559077,
               0.17087110519302778, 0.41368793888839245, 0.17986432125582943,
               0.42268115495119407, 0.18885753731860563, 0.43167437101397027,
               0.19785075338140728, 0.44066758707677195, 0.20684396944418348,
               0.44966080313954815, 0.21583718550698514, 0.45865401920234977,
               0.22483040156978679, 0.46764723526512603, 0.23382361763256301,
               0.47664045132792765, 0.24281683369536466, 0.48563366739072933,
               0.25181004975814086, 0.49462688345350553, 0.26080326582094249,
               0.50362009951630715, 0.26979648188374417, 0.51261331557908341,
               0.27878969794652037, 0.52160653164188497, 0.28778291400932199,
               0.53059974770468665, 0.29677613007209824, 0.53959296376746291,
               0.30576934613489987, 0.54858617983026448, 0.31476256219770149,
               0.55757939589304073, 0.32375577826047774, 0.56657261195584241,
               0.33274899432327937, 0.57556582801864398, 0.34174221038605557,
               0.58455904408142023, 0.35073542644885725, 0.59355226014422191,
               0.35972864251163345, 0.60254547620699805, 0.36872185857443507,
               0.61153869226979973, 0.37771507463723675, 0.62053190833257599,
               0.38670829070001295, 0.62952512439537756, 0.39570150676281457,
               0.63851834045817923, 0.40469472282559077, 0.64751155652095549,
               0.41368793888839245, 0.65650477258375706, 0.42268115495119407,
               0.66549798864653331, 0.43167437101397027, 0.67449120470933499,
               0.44066758707677195, 0.68348442077213656, 0.44966080313954815,
               0.69247763683491281, 0.45865401920234977, 0.70147085289771449,
               0.46764723526512603, 0.71046406896049064, 0.47664045132792765,
               0.71945728502329231, 0.48563366739072933, 0.72845050108606846,
               0.49462688345350553, 0.73744371714887014, 0.50362009951630715,
               0.74643693321167182, 0.51261331557908341, 0.75543014927444796,
               0.52160653164188497, 0.76442336533724964, 0.53059974770468665,
               0.77341658140002589, 0.53959296376746291, 0.78240979746282757,
               0.54858617983026448, 0.79140301352562914, 0.55757939589304073,
               0.80039622958840539, 0.56657261195584241, 0.80938944565120707,
               0.57556582801864398, 0.81838266171398322, 0.58455904408142023,
               0.82737587777678498, 0.59355226014422191, 0.83636909383958657,
               0.60254547620699805, 0.84536230990236272, 0.61153869226979973,
               0.85435552596516445, 0.62053190833257599, 0.86334874202794054,
               0.62952512439537756, 0.87234195809074222, 0.63851834045817923,
               0.88133517415351847]
        lat = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0]
        dep = [10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0]

        rate = [0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728,
                0.0067796610169491532, 0.010169491525423728]

        for rup, i in zip(src.iter_ruptures(), range(1000)):
            self.assertAlmostEqual(
                rup.hypocenter.longitude, lon[i], delta=0.01)
            self.assertAlmostEqual(rup.hypocenter.latitude, lat[i], delta=0.01)
            self.assertAlmostEqual(rup.hypocenter.depth, dep[i], delta=0.01)
            self.assertAlmostEqual(rup.occurrence_rate, rate[i], delta=0.01)

    def test_hypoloc_dip_rupture(self):
        source_id = name = 'test-source'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        dip = 30.
        hypo_list = numpy.array([[0.25, 0.25, 0.4], [0.75, 0.75, 0.6]])
        slip_list = numpy.array([[90., 1.]])
        self.mesh_spacing = 5.
        src = SimpleFaultSource(source_id, name, trt,
                                self.src_mfd, self.mesh_spacing, self.sarea,
                                1., self.src_tom, self.upper_seismogenic_depth,
                                self.lower_seismogenic_depth,
                                self.fault_trace, dip, self.rake, hypo_list,
                                slip_list)

        lon = [0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993,
               0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993,
               0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993,
               0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993,
               0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993,
               0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993,
               0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993,
               0.0899, 0.3148, 0.1349, 0.3597, 0.1799, 0.4047, 0.2248,
               0.4497, 0.2698, 0.4946, 0.3148, 0.5396, 0.3597, 0.5846,
               0.4047, 0.6295, 0.4497, 0.6745, 0.4946, 0.7195, 0.5396,
               0.7644, 0.5846, 0.8094, 0.6295, 0.8544, 0.6745, 0.8993]

        lat = [-0.0779, -0.2726, -0.0779, -0.2726, -0.0779, -0.2726,
               -0.0779, -0.2726, -0.0779, -0.2726, -0.0779, -0.2726, -0.0779,
               -0.2726, -0.0779, -0.2726, -0.0779, -0.2726, -0.0779, -0.2726,
               -0.0779, -0.2726, -0.0779, -0.2726, -0.0779, -0.2726, -0.0779,
               -0.2726, -0.1168, -0.3115, -0.1168, -0.3115, -0.1168, -0.3115,
               -0.1168, -0.3115, -0.1168, -0.3115, -0.1168, -0.3115, -0.1168,
               -0.3115, -0.1168, -0.3115, -0.1168, -0.3115, -0.1168, -0.3115,
               -0.1168, -0.3115, -0.1168, -0.3115, -0.1168, -0.3115, -0.1168,
               -0.3115, -0.1558, -0.3505, -0.1558, -0.3505, -0.1558, -0.3505,
               -0.1558, -0.3505, -0.1558, -0.3505, -0.1558, -0.3505, -0.1558,
               -0.3505, -0.1558, -0.3505, -0.1558, -0.3505, -0.1558, -0.3505,
               -0.1558, -0.3505, -0.1558, -0.3505, -0.1558, -0.3505, -0.1558,
               -0.3505, -0.1947, -0.3894, -0.1947, -0.3894, -0.1947, -0.3894,
               -0.1947, -0.3894, -0.1947, -0.3894, -0.1947, -0.3894, -0.1947,
               -0.3894, -0.1947, -0.3894, -0.1947, -0.3894, -0.1947, -0.3894,
               -0.1947, -0.3894, -0.1947, -0.3894, -0.1947, -0.3894, -0.1947,
               -0.3894, -0.2337, -0.4284, -0.2337, -0.4284, -0.2337,
               -0.4284, -0.2337, -0.4284, -0.2337, -0.4284, -0.2337, -0.4284,
               -0.2337, -0.4284, -0.2337, -0.4284, -0.2337, -0.4284, -0.2337,
               -0.4284, -0.2337, -0.4284, -0.2337, -0.4284, -0.2337, -0.4284,
               -0.2337, -0.4284, -0.2726, -0.4673, -0.2726, -0.4673, -0.2726,
               -0.4673, -0.2726, -0.4673, -0.2726, -0.4673, -0.2726, -0.4673,
               -0.2726, -0.4673, -0.2726, -0.4673, -0.2726, -0.4673, -0.2726,
               -0.4673, -0.2726, -0.4673, -0.2726, -0.4673, -0.2726, -0.4673,
               -0.2726, -0.4673, -0.3115, -0.5062, -0.3115, -0.5062, -0.3115,
               -0.5062, -0.3115, -0.5062, -0.3115, -0.5062, -0.3115, -0.5062,
               -0.3115, -0.5062, -0.3115, -0.5062, -0.3115, -0.5062, -0.3115,
               -0.5062, -0.3115, -0.5062, -0.3115, -0.5062, -0.3115, -0.5062,
               -0.3115, -0.5062, -0.3505, -0.5452, -0.3505, -0.5452, -0.3505,
               -0.5452, -0.3505, -0.5452, -0.3505, -0.5452, -0.3505, -0.5452,
               -0.3505, -0.5452, -0.3505, -0.5452, -0.3505, -0.5452, -0.3505,
               -0.5452, -0.3505, -0.5452, -0.3505, -0.5452, -0.3505, -0.5452,
               -0.3505, -0.5452]

        dep = [5.0, 17.5, 5.0, 17.5, 5.0, 17.5, 5.0,
               17.5, 5.0, 17.5, 5.0, 17.5, 5.0, 17.5, 5.0, 17.5, 5.0, 17.5,
               5.0, 17.5, 5.0, 17.5, 5.0, 17.5, 5.0, 17.5, 5.0, 17.5, 7.5,
               20.0, 7.5, 20.0, 7.5, 20.0, 7.5, 20.0, 7.5, 20.0, 7.5, 20.0,
               7.5, 20.0, 7.5, 20.0, 7.5, 20.0, 7.5, 20.0, 7.5, 20.0, 7.5,
               20.0, 7.5, 20.0, 7.5, 20.0, 10.0, 22.5, 10.0, 22.5, 10.0,
               22.5, 10.0, 22.5, 10.0, 22.5, 10.0, 22.5, 10.0, 22.5, 10.0,
               22.5, 10.0, 22.5, 10.0, 22.5, 10.0, 22.5, 10.0, 22.5, 10.0,
               22.5, 10.0, 22.5, 12.5, 25.0, 12.5, 25.0, 12.5, 25.0, 12.5,
               25.0, 12.5, 25.0, 12.5, 25.0, 12.5, 25.0, 12.5, 25.0, 12.5,
               25.0, 12.5, 25.0, 12.5, 25.0, 12.5, 25.0, 12.5, 25.0, 12.5,
               25.0, 15.0, 27.5, 15.0, 27.5, 15.0, 27.5, 15.0, 27.5,
               15.0, 27.5, 15.0, 27.5, 15.0, 27.5, 15.0, 27.5, 15.0, 27.5,
               15.0, 27.5, 15.0, 27.5, 15.0, 27.5, 15.0, 27.5, 15.0, 27.5,
               17.5, 30.0, 17.5, 30.0, 17.5, 30.0, 17.5, 30.0, 17.5, 30.0,
               17.5, 30.0, 17.5, 30.0, 17.5, 30.0, 17.5, 30.0, 17.5, 30.0,
               17.5, 30.0, 17.5, 30.0, 17.5, 30.0, 17.5, 30.0, 20.0, 32.5,
               20.0, 32.5, 20.0, 32.5, 20.0, 32.5, 20.0, 32.5, 20.0, 32.5,
               20.0, 32.5, 20.0, 32.5, 20.0, 32.5, 20.0, 32.5, 20.0, 32.5,
               20.0, 32.5, 20.0, 32.5, 20.0, 32.5, 22.5, 35.0, 22.5, 35.0,
               22.5, 35.0, 22.5, 35.0, 22.5, 35.0, 22.5, 35.0, 22.5, 35.0,
               22.5, 35.0, 22.5, 35.0, 22.5, 35.0, 22.5, 35.0, 22.5, 35.0,
               22.5, 35.0, 22.5, 35.0]

        rate = [0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036,
                0.0054, 0.0036, 0.0054, 0.0036, 0.0054, 0.0036, 0.0054,
                0.0036, 0.0054, 0.0036, 0.0054]

        for rup, i in zip(src.iter_ruptures(), range(1000)):
            self.assertAlmostEqual(rup.hypocenter.longitude, lon[i], delta=0.1)
            self.assertAlmostEqual(rup.hypocenter.latitude, lat[i], delta=0.1)
            self.assertAlmostEqual(rup.hypocenter.depth, dep[i], delta=0.1)
            self.assertAlmostEqual(rup.occurrence_rate, rate[i], delta=0.01)

    def test_hypoloc_multisegment_rupture_test(self):
        source_id = name = 'test-source'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        hypo_list = numpy.array([[0.25, 0.25, 0.4], [0.75, 0.75, 0.6]])
        slip_list = numpy.array([[90., 1.]])
        self.mesh_spacing = 5.
        self.fault_trace_nodes = [
            self.fault_trace_start, Point(0.3, 0.3), self.fault_trace_end]
        self.fault_trace = Line(self.fault_trace_nodes)
        src = SimpleFaultSource(source_id, name, trt,
                                self.src_mfd, self.mesh_spacing,
                                self.sarea, 1., self.src_tom,
                                self.upper_seismogenic_depth,
                                self.lower_seismogenic_depth,
                                self.fault_trace, self.dip, self.rake,
                                hypo_list, slip_list)

        lon = [0.0954, 0.2544, 0.1272, 0.2862, 0.159, 0.3279, 0.1908, 0.3696,
               0.2226, 0.4114, 0.2544, 0.4531, 0.2862, 0.4949, 0.3279, 0.5366,
               0.3696, 0.5783, 0.4114, 0.6201, 0.4531, 0.6618, 0.4949, 0.7035,
               0.5366, 0.7453, 0.5783, 0.787, 0.6201, 0.8288, 0.6618, 0.8705]

        lat = [0.0954, 0.2544, 0.1272, 0.2862, 0.159, 0.2694, 0.1908, 0.2527,
               0.2226, 0.236, 0.2544, 0.2192, 0.2862, 0.2025, 0.2694, 0.1858,
               0.2527, 0.169, 0.236, 0.1523, 0.2192, 0.1356, 0.2025, 0.1188,
               0.1858, 0.1021, 0.169, 0.0854, 0.1523, 0.0687, 0.1356, 0.0519]

        dep = [10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0, 10.0, 30.0,
               10.0, 30.0]

        rate = [0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375,
                0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375,
                0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375,
                0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375, 0.025, 0.0375]

        for rup, i in zip(src.iter_ruptures(), range(1000)):
            self.assertAlmostEqual(rup.hypocenter.longitude, lon[i], delta=0.1)
            self.assertAlmostEqual(rup.hypocenter.latitude, lat[i], delta=0.1)
            self.assertAlmostEqual(rup.hypocenter.depth, dep[i], delta=0.1)
            self.assertAlmostEqual(rup.occurrence_rate, rate[i], delta=0.01)

    def test_slip_vertical_rupture(self):
        self.src_mfd = mfdeven.EvenlyDiscretizedMFD(8.5, 1., [1.])
        source_id = name = 'test-source'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        hypo_list = numpy.array([[0.25, 0.25, 0.4], [0.75, 0.75, 0.6]])
        slip_list = numpy.array([[90., 0.25], [0., 0.75]])
        src = SimpleFaultSource(source_id, name, trt,
                                self.src_mfd, self.mesh_spacing,
                                self.sarea, 1., self.src_tom,
                                self.upper_seismogenic_depth,
                                self.lower_seismogenic_depth,
                                self.fault_trace, self.dip,
                                self.rake, hypo_list, slip_list)

        slip = [90., 0., 90., 0.]
        rate = [0.1, 0.3, 0.15, 0.45]

        for rup, i in zip(src.iter_ruptures(), range(1000)):
            self.assertAlmostEqual(rup.rupture_slip_direction,
                                   slip[i], delta=0.1)
            self.assertAlmostEqual(rup.occurrence_rate, rate[i], delta=0.01)


class ModifySimpleFaultTestCase(_BaseFaultSourceTestCase):
    """
    Tests all of the geometry modification methods
    """
    def setUp(self):
        self.basic_trace = Line([Point(30.0, 30.0), Point(30.0, 32.0)])
        self.mfd = EvenlyDiscretizedMFD(7.0, 0.1, [1.0])
        self.aspect = 1.0
        self.dip = 45.0
        self.fault = self._make_source(self.mfd, self.aspect, self.basic_trace,
                                       self.dip)
        self.fault.lower_seismogenic_depth = 10.0

    def test_modify_set_geometry_trace(self):
        new_fault = deepcopy(self.fault) 
        new_trace = Line([Point(30.0, 30.0), Point(30.2, 32.25)])
        new_fault.modify_set_geometry(new_trace, 0., 10., 45., 1.)
        exp_lons = [30.0, 30.2]
        exp_lats = [30.0, 32.25]
        for iloc in range(len(new_fault.fault_trace)):
            self.assertAlmostEqual(
                new_fault.fault_trace.points[iloc].longitude,
                exp_lons[iloc]
                )
            self.assertAlmostEqual(
                new_fault.fault_trace.points[iloc].latitude,
                exp_lats[iloc]
                )
        # Verify that the dip and seismogenic depths were not modified
        self.assertAlmostEqual(new_fault.dip, 45.0)
        self.assertAlmostEqual(new_fault.upper_seismogenic_depth, 0.0)
        self.assertAlmostEqual(new_fault.lower_seismogenic_depth, 10.0)

    def test_modify_set_geometry_other_params(self):
        new_fault = deepcopy(self.fault) 
        new_fault.modify_set_geometry(self.basic_trace, 1., 12., 60., 1.)
        self.assertAlmostEqual(new_fault.dip, 60.)
        self.assertAlmostEqual(new_fault.upper_seismogenic_depth, 1.0)
        self.assertAlmostEqual(new_fault.lower_seismogenic_depth, 12.0)

    def test_modify_adjust_dip(self):
        # Increase dip
        new_fault = deepcopy(self.fault) 
        new_fault.modify_adjust_dip(15.0)
        self.assertAlmostEqual(new_fault.dip, 60.0)
        # Decrease dip
        new_fault = deepcopy(self.fault) 
        new_fault.modify_adjust_dip(-15.0)
        self.assertAlmostEqual(new_fault.dip, 30.0)

    def test_modify_adjust_dip_bad(self):
        with self.assertRaises(ValueError) as ar:
            # Adjustment would put dip out of 0 - 90 degree range
            self.fault.modify_adjust_dip(70.0)
        self.assertEqual(str(ar.exception), "dip must be between 0.0 and 90.0")

    def test_modify_set_dip(self):
        new_fault = deepcopy(self.fault) 
        new_fault.modify_set_dip(72.0)
        self.assertAlmostEqual(new_fault.dip, 72.0)
