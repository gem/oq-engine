# The Hazard Library
# Copyright (C) 2013-2018 GEM Foundation
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

from openquake.hazardlib.scalerel.germany2018 import GermanyMSR


class GermanyMSRTestCase(unittest.TestCase):
    """
    Tests for the magnitude-scaling relationship used in the 2018 Germany
    national seismic hazard model
    """

    def setUp(self):
        self.msr = GermanyMSR()

    def test_get_median_area(self):
        """
        This tests the MSR
        """
        self.assertAlmostEqual(self.msr.get_median_area(4.0, None), 0.8317637,
                               places=5)
        self.assertAlmostEqual(self.msr.get_median_area(5.0, None), 3.2359365,
                               places=5)
        self.assertAlmostEqual(self.msr.get_median_area(6.0, None), 12.589254,
                               places=5)
        self.assertAlmostEqual(self.msr.get_median_area(7.0, None), 48.9778819,
                               places=5)
        self.assertAlmostEqual(self.msr.get_median_area(8.0, None), 190.546071,
                               places=5)
