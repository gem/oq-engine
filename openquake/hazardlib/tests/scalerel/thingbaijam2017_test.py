# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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

import os
import numpy
from openquake.hazardlib.scalerel.thingbaijam2017 import ThingbaijamInterface, ThingbaijamStrikeSlip
from openquake.hazardlib.tests.scalerel.msr_test import BaseMSRTestCase

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'thingbaijam2017')


class ThingbaijamInterfaceTestCase(BaseMSRTestCase):
    '''
    Tests for the magnitude-scaling relationship Thingbaijam et al. (2017) for
    interface events.
    '''

    MSR_CLASS = ThingbaijamInterface

    def test_median_area(self):
        """
        Tests against data digitized from a figure and manual data
        """
        # digitized data
        fname = os.path.join(DATA_DIR, 'interface.csv')
        data = numpy.loadtxt(fname, delimiter=',')
        msr = ThingbaijamInterface()
        computed = msr.get_median_area(data[:, 0], 90.)
        numpy.testing.assert_allclose(computed, 10**data[:, 1], rtol=10)
        # manual data
        self._test_get_median_area(8.0, None, 19952.6231496888, places=5)
        self._test_get_median_area(7.0, None, 2243.8819237828, places=5)

    def test_median_magnitude(self):
        """
        This tests the MSR
        """
        self._test_get_median_mag(19952.6231496888, None, 8.00, places=2)
        self._test_get_median_mag(2243.8819237828, None, 7.00, places=2)


class ThingbaijamStrikeSlipTestCase(BaseMSRTestCase):
    '''
    Tests for the magnitude-scaling relationship Thingbaijam et al. (2017) for
    interface events.
    '''

    MSR_CLASS = ThingbaijamStrikeSlip

    def test_median_area(self):
        """
        Tests against data digitized from a figure and manual data
        """
        # digitized data
        fname = os.path.join(DATA_DIR, 'strikeslip.csv')
        data = numpy.loadtxt(fname, delimiter=',')
        msr = ThingbaijamStrikeSlip()
        computed = msr.get_median_area(data[:, 0], 90.)
        numpy.testing.assert_allclose(computed, 10**data[:, 1], rtol=10)
        # manual data
        self._test_get_median_area(8.0, None, 11220.184543, places=5)
        self._test_get_median_area(7.0, None, 1282.33058266, places=5)

    def test_median_magnitude(self):
        """
        This tests the MSR
        """
        self._test_get_median_mag(11220.184543, None, 8.00, places=2)
        self._test_get_median_mag(1282.33058266, None, 7.00, places=2)

