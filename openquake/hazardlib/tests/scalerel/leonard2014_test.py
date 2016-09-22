from openquake.hazardlib.scalerel.leonard2014 import Leonard2014_SCR, Leonard2014_Interplate
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

class Leonard2014_InterplateTestCase(BaseMSRTestCase):
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
