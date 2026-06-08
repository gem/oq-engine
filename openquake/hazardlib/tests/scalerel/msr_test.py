# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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

from openquake.hazardlib.scalerel import (
    get_available_scalerel,
    get_available_magnitude_scalerel,
    get_available_sigma_magnitude_scalerel,
    get_available_area_scalerel,
    get_available_sigma_area_scalerel)

from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.scalerel.wc1994 import WC1994


class AvailableMSRTestCase(unittest.TestCase):
    """
    The scalerel module contains methods to determine the scaling relations
    contained within. This class tests that all execute - without necessarily
    verifying the number or set of scaling relations available
    """
    def _test_get_available_scalerel(self):
        self.assertGreater(len(get_available_scalerel()), 0)

    def _test_get_available_magnitude_scalerel(self):
        self.assertGreater(len(get_available_magnitude_scalerel()), 0)

    def _test_get_available_sigma_magnitude_scalerel(self):
        self.assertGreater(len(get_available_sigma_magnitude_scalerel()), 0)

    def _test_get_available_area_scalerel(self):
        self.assertGreater(len(get_available_area_scalerel()), 0)

    def _test_get_available_sigma_area_scalerel(self):
        self.assertGreater(len(get_available_sigma_area_scalerel()), 0)


class BaseMSRTestCase(unittest.TestCase):
    MSR_CLASS = None

    def setUp(self):
        super().setUp()
        self.msr = self.MSR_CLASS()

    def _test_get_median_area(self, mag, rake, expected_value, places=7):
        self.assertAlmostEqual(self.msr.get_median_area(mag, rake),
                               expected_value, places=places)

    def _test_get_median_mag(self, area, rake, expected_value, places=7):
        self.assertAlmostEqual(self.msr.get_median_mag(area, rake),
                               expected_value, places=places)

    def _test_get_median_length(self, mag, expected_value, places=7):
        self.assertAlmostEqual(self.msr.get_median_length(mag),
                               expected_value, places=places)

    def _test_get_median_width(self, mag, expected_value, places=7):
        self.assertAlmostEqual(self.msr.get_median_width(mag),
                               expected_value, places=places)


class PeerMSRMSRTestCase(BaseMSRTestCase):
    MSR_CLASS = PeerMSR

    def test_median_area(self):
        self._test_get_median_area(4.3, None, 1.9952623)
        self._test_get_median_area(5.1, 0, 12.5892541)


class WC1994MSRTestCase(BaseMSRTestCase):
    MSR_CLASS = WC1994

    def test_median_area_all(self):
        self._test_get_median_area(2.2, None, 0.0325087)
        self._test_get_median_area(1.3, None, 0.0049317)

    def test_median_area_strike_slip(self):
        self._test_get_median_area(3.9, -28.22, 1.2302688)
        self._test_get_median_area(3.9, -45, 1.2302688)
        self._test_get_median_area(3.9, 0, 1.2302688)
        self._test_get_median_area(3.9, 45, 1.2302688)

    def test_median_area_thrust(self):
        self._test_get_median_area(4.1, 50, 1.0665961)
        self._test_get_median_area(4.1, 95, 1.0665961)

    def test_median_area_normal(self):
        self._test_get_median_area(5.9, -59, 92.8966387)
        self._test_get_median_area(5.9, -125, 92.8966387)

    def test_get_std_dev_area(self):
        self.assertEqual(self.msr.get_std_dev_area(None, None), 0.24)
        self.assertEqual(self.msr.get_std_dev_area(20, 4), 0.22)
        self.assertEqual(self.msr.get_std_dev_area(None, 138), 0.22)
        self.assertEqual(self.msr.get_std_dev_area(None, -136), 0.22)
        self.assertEqual(self.msr.get_std_dev_area(None, 50), 0.26)
        self.assertEqual(self.msr.get_std_dev_area(None, -130), 0.22)

    def test_median_length_and_width_all(self):
        self.assertAlmostEqual(self.msr.get_median_srl(5.9, None), 7.0957776, places=6)
        self.assertAlmostEqual(self.msr.get_median_rld(5.9, None), 10.9900583, places=6)
        self.assertAlmostEqual(self.msr.get_median_rw(5.9, None), 7.5509227, places=6)

    def test_median_length_and_width_strike_slip(self):
        self.assertAlmostEqual(self.msr.get_median_srl(6.2, 0.0), 10.9144033, places=6)
        self.assertAlmostEqual(self.msr.get_median_rld(6.2, 180.0), 18.7931681, places=6)
        self.assertAlmostEqual(self.msr.get_median_rw(6.2, -15.0), 8.2035154, places=6)

    def test_median_length_and_width_thrust(self):
        self.assertAlmostEqual(self.msr.get_median_srl(5.8, 65.0), 6.2230028, places=6)
        self.assertAlmostEqual(self.msr.get_median_rld(5.8, 90.0), 8.7902251, places=6)
        self.assertAlmostEqual(self.msr.get_median_rw(5.8, 75.0), 5.8613816, places=6)

    def test_median_length_and_width_normal(self):
        self.assertAlmostEqual(self.msr.get_median_srl(6.1, -50.0), 10.9647819, places=6)
        self.assertAlmostEqual(self.msr.get_median_rld(6.1, -90.0), 14.7910838, places=6)
        self.assertAlmostEqual(self.msr.get_median_rw(6.1, -125.0), 9.8855309, places=6)

    def test_get_std_dev_length_and_width(self):
        # all
        self.assertEqual(self.msr.get_std_dev_srl(None, None), 0.22)
        self.assertEqual(self.msr.get_std_dev_rld(None, None), 0.16)
        self.assertEqual(self.msr.get_std_dev_rw(None, None), 0.15)
        # strike slip
        self.assertEqual(self.msr.get_std_dev_srl(None, -135.0), 0.23)
        self.assertEqual(self.msr.get_std_dev_rld(None, 35.0), 0.15)
        self.assertEqual(self.msr.get_std_dev_rw(None, 270.0), 0.14)
        # reverse
        self.assertEqual(self.msr.get_std_dev_srl(None, 90.0), 0.20)
        self.assertEqual(self.msr.get_std_dev_rld(None, 65.0), 0.16)
        self.assertEqual(self.msr.get_std_dev_rw(None, 125.0), 0.15)
        # normal
        self.assertEqual(self.msr.get_std_dev_srl(None, -50.0), 0.21)
        self.assertEqual(self.msr.get_std_dev_rld(None, -95.0), 0.17)
        self.assertEqual(self.msr.get_std_dev_rw(None, -115.0), 0.12)

    def test_string(self):
        self.assertEqual(str(self.msr), "WC1994")
