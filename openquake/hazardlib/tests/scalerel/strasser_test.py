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
# import unittest

from openquake.hazardlib.scalerel.strasser2010 import (StrasserInterface,
                                                       StrasserIntraslab)
from openquake.hazardlib.tests.scalerel.msr_test import BaseMSRTestCase


class StrasserInterfaceTestCase(BaseMSRTestCase):
    '''
    Tests for the magnitude-scaling relationship Strasser et al. (2010) for
    interface events.

    '''

    MSR_CLASS = StrasserInterface

    def test_median_area(self):
        """
        This tests the MSR
        """
        self._test_get_median_area(4.0, None, 2.14783, places=5)
        self._test_get_median_area(5.0, None, 19.23092, places=5)
        self._test_get_median_area(6.0, None, 172.18686, places=5)
        self._test_get_median_area(7.0, None, 1541.70045, places=5)
        self._test_get_median_area(8.0, None, 13803.84265, places=5)

    def test_median_magnitude(self):
        """
        This tests the MSR
        """
        self._test_get_median_mag(2.14783, None, 4.72, places=2)
        self._test_get_median_mag(19.23092, None, 5.53, places=2)
        self._test_get_median_mag(172.18686, None, 6.33, places=2)
        self._test_get_median_mag(1541.70045, None, 7.14, places=2)
        self._test_get_median_mag(13803.84265, None, 7.94, places=2)


class StrasserIntraslabTestCase(BaseMSRTestCase):
    '''
    Tests for the magnitude-scaling relationship Strasser et al. (2010) for
    intraslab events.

    '''

    MSR_CLASS = StrasserIntraslab

    def test_median_area(self):
        """
        This tests the MSR
        """
        self._test_get_median_area(4.0, None, 2.16272, places=5)
        self._test_get_median_area(5.0, None, 16.78804, places=5)
        self._test_get_median_area(6.0, None, 130.31668, places=5)
        self._test_get_median_area(7.0, None, 1011.57945, places=5)
        self._test_get_median_area(8.0, None, 7852.35635, places=5)

    def test_median_magnitude(self):
        """
        This tests the MSR
        """
        self._test_get_median_mag(2.16272, None, 4.38, places=2)
        self._test_get_median_mag(16.78804, None, 5.26, places=2)
        self._test_get_median_mag(130.31668, None, 6.13, places=2)
        self._test_get_median_mag(1011.57945, None, 7.00, places=2)
        self._test_get_median_mag(7852.35635, None, 7.87, places=2)
