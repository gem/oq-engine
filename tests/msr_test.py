import unittest

from nhe.msr import PeerMSR, WC1994MSR


class BaseMSRTestCase(unittest.TestCase):
    MSR_CLASS = None

    def setUp(self):
        super(BaseMSRTestCase, self).setUp()
        self.msr = self.MSR_CLASS()

    def _test_get_median_area(self, mag, rake, expected_value, epsilon=0.0):
        self.assertAlmostEqual(self.msr.get_median_area(mag, rake, epsilon),
                               expected_value)


class PeerMSRMSRTestCase(BaseMSRTestCase):
    MSR_CLASS = PeerMSR

    def test_median_area(self):
        self._test_get_median_area(4.3, None, 1.9952623)
        self._test_get_median_area(5.1, 0, 12.5892541)
        # With uncertainty
        self._test_get_median_area(4.8, None, 4.7315126, -0.5)
        self._test_get_median_area(3.4, 0, 0.2818383, 0.2)


class WC1994MSRTestCase(BaseMSRTestCase):
    MSR_CLASS = WC1994MSR

    def test_median_area_all(self):
        self._test_get_median_area(2.2, None, 0.0325087)
        self._test_get_median_area(1.3, None, 0.0049317)
        # With uncertainty
        self._test_get_median_area(2.2, None, 0.0343558, 0.1)
        self._test_get_median_area(1.3, None, 0.0101158, 1.3)

    def test_median_area_strike_slip(self):
        self._test_get_median_area(3.9, -28.22, 1.2302688)
        self._test_get_median_area(3.9, -45, 1.2302688)
        self._test_get_median_area(3.9, 0, 1.2302688)
        self._test_get_median_area(3.9, 45, 1.2302688)
        # With uncertainty
        self._test_get_median_area(3.9, 12, 10.3276141, 4.2)
        self._test_get_median_area(3.9, 136, 10.3276141, 4.2)
        self._test_get_median_area(3.9, -140, 10.3276141, 4.2)

    def test_median_area_thrust(self):
        self._test_get_median_area(4.1, 50, 1.0665961)
        self._test_get_median_area(4.1, 95, 1.0665961)
        # With uncertainty
        self._test_get_median_area(4.1, 60, 0.9183326, -0.25)
        self._test_get_median_area(4.1, 70, 0.9183326, -0.25)

    def test_median_area_normal(self):
        self._test_get_median_area(5.9, -59, 92.8966387)
        self._test_get_median_area(5.9, -125, 92.8966387)
        # With uncertainty
        self._test_get_median_area(4.3, -90, 5.2722986, 0.3)
        self._test_get_median_area(4.3, -46, 5.2722986, 0.3)

    def test_mag_from_area_all(self):
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(50, None), 5.7349906)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(136, None), 6.1608681)
        # With uncertainty
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(50, None, 0.4), 5.8309906)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(100, None, 0.2), 6.078)

    def test_mag_from_area_strike_slip(self):
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(500, 20), 6.7329494)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(500, 136), 6.7329494)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(500, -139), 6.7329494)
        # With uncertainty
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(180, 45, 0.8), 6.4643780)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(180, 140, 0.8), 6.4643780)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(180, -150, 0.8), 6.4643780)

    def test_mag_from_area_thrust(self):
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(1500, 46), 7.1884821)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(1500, 134), 7.1884821)
        # With uncertainty
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(700, 46, 1.8), 7.3405882)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(700, 134, 1.8), 7.3405882)

    def test_mag_from_area_normal(self):
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(2500, -48), 7.3958988)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(2500, -134), 7.3958988)
        # With uncertainty
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(50, -49, 1.8), 6.1129494)
        self.assertAlmostEqual(
            self.msr.get_magnitude_from_area(50, -120, 1.8), 6.1129494)
