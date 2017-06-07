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

from openquake.hazardlib.scalerel.wc1994_qcss import WC1994_QCSS
from openquake.hazardlib.tests.scalerel.msr_test import BaseMSRTestCase

class WC1994QCSSTestCase(BaseMSRTestCase):
    """
    Tests the scaling relationship WC1994_QCSS, a local adaptation of the
    Wells & Coppersmith model for the Queen Charlotte Strike-Slip fault in
    Western Canada

    Test values verified by hand
    """

    MSR_CLASS = WC1994_QCSS

    def test_median_area(self):
        # Length less than 20 km for M < 6.5
        self._test_get_median_area(5.0, None, 11.48153621, places=5)
        self._test_get_median_area(6.0, None, 199.52623150, places=5)
        # Length > 20 km
        self._test_get_median_area(7.0, None, 1177.68731071, places=5)
        self._test_get_median_area(8.0, None, 4909.41783137, places=5)

    def test_get_stddev_area(self):
        """
        Should always equal 0.15
        """
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, 0.0),
                               0.15)
