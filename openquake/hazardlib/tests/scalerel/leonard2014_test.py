# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.


from openquake.hazardlib.scalerel.leonard2014 import (Leonard2014_SCR,
                                                      Leonard2014_Interplate)
from openquake.hazardlib.tests.scalerel.msr_test import BaseMSRTestCase


class Leonard2014_SCRTestCase(BaseMSRTestCase):
    """
    Tests the scaling relationship Leonard2014 for Stable Continental Regions

    Test values verified by hand
    """

    MSR_CLASS = Leonard2014_SCR

    def test_median_area(self):
        """
        Test magnitude to area scaling
        """
        self._test_get_median_area(4.0, 0, 0.66069, places=5)
        self._test_get_median_area(4.0, 45, 0.66069, places=5)
        self._test_get_median_area(4.0, -45, 0.66069, places=5)
        self._test_get_median_area(4.0, 135, 0.66069, places=5)
        self._test_get_median_area(4.0, -135, 0.66069, places=5)
        self._test_get_median_area(4.0, 90, 0.64565, places=5)
        self._test_get_median_area(4.0, 70, 0.64565, places=5)
        self._test_get_median_area(4.0, -70, 0.64565, places=5)
        self._test_get_median_area(4.0, None, 0.65313, places=5)
        self._test_get_median_area(6.0, 0, 66.06934, places=5)
        self._test_get_median_area(6.0, 90, 64.56542, places=5)
        self._test_get_median_area(8.0, 0, 6606.93448, places=5)
        self._test_get_median_area(8.0, 90, 6456.54229, places=5)

    def test_median_magnitude(self):
        """
        Test area to magnitude scaling
        """
        self._test_get_median_mag(0.65, 0, 3.99291, places=5)
        self._test_get_median_mag(0.65, 90, 4.00291, places=5)
        self._test_get_median_mag(0.65, 45, 3.99291, places=5)
        self._test_get_median_mag(0.65, -45, 3.99291, places=5)
        self._test_get_median_mag(0.65, 135, 3.99291, places=5)
        self._test_get_median_mag(0.65, -135, 3.99291, places=5)
        self._test_get_median_mag(0.65, 90, 4.00291, places=5)
        self._test_get_median_mag(0.65, 70, 4.00291, places=5)
        self._test_get_median_mag(0.65, -70, 4.00291, places=5)
        self._test_get_median_mag(0.65, None, 3.99791, places=5)
        self._test_get_median_mag(66.0, 0, 5.99954, places=5)
        self._test_get_median_mag(66.0, 90, 6.00954, places=5)
        self._test_get_median_mag(6600.0, 0, 7.99954, places=5)
        self._test_get_median_mag(6600.0, 90, 8.00954, places=5)

    def test_stddev_area(self):
        """
        Tests the standard deviation for area.
        Trivial result - included only for coverage
        """
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, 0.0), 0.0)

    def test_stddev_mag(self):
        """
        Tests the standard deviation for magnitude.
        Trivial result - included only for coverage
        """
        self.assertAlmostEqual(self.msr.get_std_dev_mag(1000.0, 0.0), 0.0)


class Leonard2014_InterplateTestCase(Leonard2014_SCRTestCase):
    """
    Tests the scaling relationship Leonard2014 for Interplate Regions

    Test values verified by hand
    """

    MSR_CLASS = Leonard2014_Interplate

    def test_median_area(self):
        """
        Test magnitude to area scaling
        """
        self._test_get_median_area(4.0, 0, 1.02329, places=5)
        self._test_get_median_area(4.0, 45, 1.02329, places=5)
        self._test_get_median_area(4.0, -45, 1.02329, places=5)
        self._test_get_median_area(4.0, 135, 1.02329, places=5)
        self._test_get_median_area(4.0, -135, 1.02329, places=5)
        self._test_get_median_area(4.0, 90, 1.00000, places=5)
        self._test_get_median_area(4.0, 70, 1.00000, places=5)
        self._test_get_median_area(4.0, -70, 1.00000, places=5)
        self._test_get_median_area(4.0, None, 1.01158, places=5)
        self._test_get_median_area(6.0, 0, 102.32930, places=5)
        self._test_get_median_area(6.0, 90, 100.00000, places=5)
        self._test_get_median_area(8.0, 0, 10232.92992, places=5)
        self._test_get_median_area(8.0, 90, 10000.00000, places=5)

    def test_median_magnitude(self):
        """
        Test area to magnitude scaling
        """
        self._test_get_median_mag(0.65, 0, 3.80291, places=5)
        self._test_get_median_mag(0.65, 45, 3.80291, places=5)
        self._test_get_median_mag(0.65, -45, 3.80291, places=5)
        self._test_get_median_mag(0.65, 135, 3.80291, places=5)
        self._test_get_median_mag(0.65, -135, 3.80291, places=5)
        self._test_get_median_mag(0.65, 90, 3.81291, places=5)
        self._test_get_median_mag(0.65, 70, 3.81291, places=5)
        self._test_get_median_mag(0.65, -70, 3.81291, places=5)
        self._test_get_median_mag(0.65, None, 3.80791, places=5)
        self._test_get_median_mag(66.0, 0, 5.80954, places=5)
        self._test_get_median_mag(66.0, 90, 5.81954, places=5)
        self._test_get_median_mag(6600.0, 0, 7.80954, places=5)
        self._test_get_median_mag(6600.0, 90, 7.81954, places=5)
