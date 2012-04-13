# nhlib: A New Hazard Library
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

from nhlib.const import TRT
from nhlib.source.simple_fault import SimpleFaultSource
from nhlib.source.rupture import ProbabilisticRupture
from nhlib.mfd import TruncatedGRMFD
from nhlib.scalerel.peer import PeerMSR
from nhlib.geo import Point, Line
from nhlib.tom import PoissonTOM

from tests.geo.surface._utils import assert_mesh_is
from tests.source import _simple_fault_test_data as test_data


def assert_angles_equal(testcase, angle1, angle2, delta):
    if abs(angle1 - angle2) > 180:
        angle1, angle2 = 360 - max((angle1, angle2)), min((angle1, angle2))
    testcase.assertAlmostEqual(angle1, angle2, delta=delta)


class _BaseSimpleFaultSourceTestCase(unittest.TestCase):
    TRT = TRT.ACTIVE_SHALLOW_CRUST
    RAKE = 0

    def _make_source(self, mfd, aspect_ratio, fault_trace=None):
        source_id = name = 'test-source'
        trt = self.TRT
        rake = self.RAKE
        dip = 45
        rupture_mesh_spacing = 1
        upper_seismogenic_depth = 0
        lower_seismogenic_depth = 4.2426406871192848
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = aspect_ratio
        if fault_trace is None:
            fault_trace = Line([Point(0.0, 0.0),
                                Point(0.0, 0.0359728811758),
                                Point(0.0190775080917, 0.0550503815181),
                                Point(0.03974514139, 0.0723925718855)])

        return SimpleFaultSource(
            source_id, name, trt, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            upper_seismogenic_depth, lower_seismogenic_depth,
            fault_trace, dip, rake
        )


class SimpleFaultIterRupturesTestCase(_BaseSimpleFaultSourceTestCase):
    def _test(self, expected_ruptures, mfd, aspect_ratio, **kwargs):
        source = self._make_source(mfd, aspect_ratio, **kwargs)
        tom = PoissonTOM(time_span=50)
        ruptures = list(source.iter_ruptures(tom))
        for rupture in ruptures:
            self.assertIsInstance(rupture, ProbabilisticRupture)
            self.assertIs(rupture.temporal_occurrence_model, tom)
            self.assertIs(rupture.tectonic_region_type, self.TRT)
            self.assertEqual(rupture.rake, self.RAKE)
        self.assertEqual(len(expected_ruptures), len(ruptures))
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

    def test_2(self):
        # rupture dimensions are larger then mesh_spacing, number of nodes
        # along strike and dip is even
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=3.0, max_mag=4.0,
                             bin_width=1.0)
        self._test(test_data.TEST2_RUPTURES, mfd=mfd, aspect_ratio=1.0)

    def test_3(self):
        # rupture length greater than fault length, number of nodes along
        # length is odd and along width is even
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.0, max_mag=6.0,
                             bin_width=1.0)
        self._test(test_data.TEST3_RUPTURES, mfd=mfd, aspect_ratio=4.0)

    def test_4(self):
        # rupture width greater than fault width, number of nodes along
        # length is even, along width is odd
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.4, max_mag=5.5,
                             bin_width=0.1)
        self._test(test_data.TEST4_RUPTURES, mfd=mfd, aspect_ratio=0.5)

    def test_5(self):
        # rupture length and width greater than fault length and width
        # respectively
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=6.0, max_mag=7.0,
                             bin_width=1.0)
        self._test(test_data.TEST5_RUPTURES, mfd=mfd, aspect_ratio=1.0)


class SimpleFaultParametersChecksTestCase(_BaseSimpleFaultSourceTestCase):
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
