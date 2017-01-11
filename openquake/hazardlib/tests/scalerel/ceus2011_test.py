# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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

from openquake.hazardlib.scalerel.ceus2011 import CEUS2011


class CEUS2011TestCase(unittest.TestCase):
    """
    Tests for the magnitude-scaling relationship used in the CEUS SSC model

    """

    def setUp(self):
        self.asr = CEUS2011()

    def test_get_median_area(self):
        """
        This tests the MSR
        """
        self.assertAlmostEqual(self.asr.get_median_area(4.0, None), 0.430526, 
                places=5)
        self.assertAlmostEqual(self.asr.get_median_area(5.0, 20), 4.305266,
                places=5)
        self.assertAlmostEqual(self.asr.get_median_area(6.0, 138), 43.052661,
                places=5)
        self.assertAlmostEqual(self.asr.get_median_area(7.0, -136), 430.526610,
                places=5)
        self.assertAlmostEqual(self.asr.get_median_area(8.0, 50), 4305.266105,
                places=5)
