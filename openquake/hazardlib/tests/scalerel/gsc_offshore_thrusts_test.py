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
"""
Tests the Geological Survey of Canada (GSC) offshore fault scaling relations

Test values verified by hand
"""
from openquake.hazardlib.scalerel.gsc_offshore_thrusts import (
    GSCCascadia,
    GSCEISB,
    GSCEISI,
    GSCEISO,
    GSCOffshoreThrustsHGT,
    GSCOffshoreThrustsWIN)
from openquake.hazardlib.tests.scalerel.msr_test import BaseMSRTestCase


class GSCCascadiaTestCase(BaseMSRTestCase):
    MSR_CLASS = GSCCascadia

    def test_median_area(self):
        self._test_get_median_area(5.0, None, 129392.77083492, places=5)
        self._test_get_median_area(6.0, None, 129691.05197725, places=5)
        self._test_get_median_area(7.0, None, 129990.02072863, places=5)
        self._test_get_median_area(8.0, None, 130289.67867416, places=5)
        self._test_get_median_area(9.0, None, 130590.02740260, places=5)

    def test_get_stddev_area(self):
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, None), 0.01)


class GSCCEISBTestCase(BaseMSRTestCase):
    MSR_CLASS = GSCEISB

    def test_median_area(self):
        self._test_get_median_area(5.0, None, 4420.45076025, places=5)
        self._test_get_median_area(6.0, None, 4430.64095167, places=5)
        self._test_get_median_area(7.0, None, 4440.85463390, places=5)
        self._test_get_median_area(8.0, None, 4451.09186110, places=5)
        self._test_get_median_area(9.0, None, 4461.35268754, places=5)

    def test_get_stddev_area(self):
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, None), 0.01)


class GSCCEISITestCase(BaseMSRTestCase):
    MSR_CLASS = GSCEISI

    def test_median_area(self):
        self._test_get_median_area(5.0, None, 5980.60985211, places=5)
        self._test_get_median_area(6.0, None, 5994.39658167, places=5)
        self._test_get_median_area(7.0, None, 6008.21509292, places=5)
        self._test_get_median_area(8.0, None, 6022.06545913, places=5)
        self._test_get_median_area(9.0, None, 6035.94775374, places=5)

    def test_get_stddev_area(self):
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, None), 0.01)


class GSCCEISOTestCase(BaseMSRTestCase):
    MSR_CLASS = GSCEISO

    def test_median_area(self):
        self._test_get_median_area(5.0, None, 2860.29166840, places=5)
        self._test_get_median_area(6.0, None, 2866.88532167, places=5)
        self._test_get_median_area(7.0, None, 2873.49417487, places=5)
        self._test_get_median_area(8.0, None, 2880.11826306, places=5)
        self._test_get_median_area(9.0, None, 2886.75762135, places=5)

    def test_get_stddev_area(self):
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, None), 0.01)


class GSCOffshoreThrustsHGTTestCase(BaseMSRTestCase):
    MSR_CLASS = GSCOffshoreThrustsHGT

    def test_median_area(self):
        self._test_get_median_area(5.0, None, 124.39569234, places=5)
        self._test_get_median_area(6.0, None, 591.29654523, places=5)
        self._test_get_median_area(7.0, None, 2810.64076924, places=5)
        self._test_get_median_area(8.0, None, 13359.96565091, places=5)
        self._test_get_median_area(9.0, None, 63504.62291263, places=5)

    def test_get_stddev_area(self):
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, None), 0.2)


class GSCOffshoreThrustsWINTestCase(BaseMSRTestCase):
    MSR_CLASS = GSCOffshoreThrustsWIN

    def test_median_area(self):
        self._test_get_median_area(5.0, None, 32.07192474, places=5)
        self._test_get_median_area(6.0, None, 152.44915593, places=5)
        self._test_get_median_area(7.0, None, 724.64453981, places=5)
        self._test_get_median_area(8.0, None, 3444.49076059, places=5)
        self._test_get_median_area(9.0, None, 16372.87793945, places=5)

    def test_get_stddev_area(self):
        self.assertAlmostEqual(self.msr.get_std_dev_area(6.0, None), 0.2)
