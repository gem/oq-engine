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
from openquake.hazardlib.scalerel.allenhayes2017 import (
                                                AllenHayesInterfaceLinear,
                                                AllenHayesInterfaceBilinear,
                                                AllenHayesIntraslab)
from openquake.hazardlib.tests.scalerel.msr_test import BaseMSRTestCase

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'allenhayes2017')


class AllenHayesInterfaceLinearTestCase(BaseMSRTestCase):
    '''
    Tests for the magnitude-scaling relationship Allen and Hayes (2017) for
    interface events.
    '''

    MSR_CLASS = AllenHayesInterfaceLinear

    def test_median_area(self):
        """
        Tests against data digitized from a figure and manual data
        """
        # digitized data
        fname = os.path.join(DATA_DIR, 'interface_li.csv')
        data = numpy.loadtxt(fname, delimiter=',')
        msr = AllenHayesInterfaceLinear()
        computed = msr.get_median_area(data[:, 0], 90.)
        numpy.testing.assert_allclose(computed, data[:, 1], rtol=10)
        # manual data
        self._test_get_median_area(8.0, None, 11220.18454301963, places=5)
        self._test_get_median_area(7.0, None, 1230.268770812381, places=5)

    def test_median_magnitude(self):
        """
        This tests the MSR
        """
        self._test_get_median_mag(19952.6231496888, None, 8.260, places=2)
        self._test_get_median_mag(2243.8819237828, None, 7.272, places=2)


class AllenHayesInterfaceBilnearTestCase(BaseMSRTestCase):
    '''
    Tests for the magnitude-scaling relationship Allen and Hayes (2017) for
    interface events.
    '''

    MSR_CLASS = AllenHayesInterfaceBilinear

    def test_median_area(self):
        """
        Tests against data digitized from a figure and manual data
        """
        # digitized data
        fname = os.path.join(DATA_DIR, 'interface_bi.csv')
        data = numpy.loadtxt(fname, delimiter=',')
        msr = AllenHayesInterfaceBilinear()
        computed = [msr.get_median_area(d, 90.) for d in data[:, 0]]
        numpy.testing.assert_allclose(computed, data[:, 1], rtol=10)
        # manual data
        self._test_get_median_area(8.0, None, 13803.84264602883, places=5)
        self._test_get_median_area(9.0, None, 104712.8548050898, places=5)

    def test_median_magnitude(self):
        """
        This tests the MSR
        """
        self._test_get_median_mag(19952.6231496888, None, 8.131, places=2)
        self._test_get_median_mag(119952.6231496888, None, 9.190, places=2)


class AllenHayesIntrslabTestCase(BaseMSRTestCase):
    '''
    Tests for the magnitude-scaling relationship Allen and Hayes (2017) for
    intraslab events.
    '''

    MSR_CLASS = AllenHayesIntraslab

    def test_median_area(self):
        """
        Tests against data digitized from a figure and manual data
        """
        # digitized data
        fname = os.path.join(DATA_DIR, 'intraslab.csv')
        data = numpy.loadtxt(fname, delimiter=',')
        msr = AllenHayesIntraslab()
        computed = msr.get_median_area(data[:, 0], 90.)
        numpy.testing.assert_allclose(computed, data[:, 1], rtol=10)
        # manual data
        self._test_get_median_area(8.0, None, 6165.950018614816, places=5)
        self._test_get_median_area(7.0, None, 676.0829753919812, places=5)

    def test_median_magnitude(self):
        """
        This tests the MSR
        """
        self._test_get_median_mag(19952.6231496888, None, 8.531, places=2)
        self._test_get_median_mag(2243.8819237828, None, 7.543, places=2)
