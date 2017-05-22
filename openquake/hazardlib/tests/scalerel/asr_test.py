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

from openquake.hazardlib.scalerel.wc1994 import WC1994


class WC1994ASRTestCase(unittest.TestCase):

    def setUp(self):
        self.asr = WC1994()

    def test_get_std_dev_mag(self):
        self.assertEqual(self.asr.get_std_dev_mag(None), 0.24)
        self.assertEqual(self.asr.get_std_dev_mag(20), 0.23)
        self.assertEqual(self.asr.get_std_dev_mag(138), 0.23)
        self.assertEqual(self.asr.get_std_dev_mag(-136), 0.23)
        self.assertEqual(self.asr.get_std_dev_mag(50), 0.25)
        self.assertEqual(self.asr.get_std_dev_mag(-130), 0.25)

    def test_get_median_mag(self):
        self.assertAlmostEqual(self.asr.get_median_mag(50, None), 5.7349906)
        self.assertAlmostEqual(self.asr.get_median_mag(500, 20), 6.7329494)
        self.assertAlmostEqual(self.asr.get_median_mag(500, 138), 6.7329494)
        self.assertAlmostEqual(self.asr.get_median_mag(500, -136), 6.7329494)
        self.assertAlmostEqual(self.asr.get_median_mag(700, 50), 6.8905882)
        self.assertAlmostEqual(self.asr.get_median_mag(800, -130), 6.8911518)

    def test_str(self):
        self.assertEqual(str(self.asr), "<WC1994>")
