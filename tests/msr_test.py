import unittest

from nhe.msr import PeerMSR, WC1994MSR


class BaseMSRTestCase(unittest.TestCase):
    MSR_CLASS = None

    def setUp(self):
        super(BaseMSRTestCase, self).setUp()
        self.msr = self.MSR_CLASS()

    def _test_get_median_area(self, mag, rake, expected_value):
        self.assertAlmostEqual(self.msr.get_median_area(mag, rake),
                               expected_value)

    def _test_get_area(self, mag, rake, epsilon, expected_value):
        self.assertAlmostEqual(self.msr.get_area(mag, rake, epsilon),
                               expected_value)


class PeerMSRMSRTestCase(BaseMSRTestCase):
    MSR_CLASS = PeerMSR

    def test_median_area(self):
        self._test_get_median_area(4.3, None, 1.9952623)
        self._test_get_median_area(5.1, 0, 12.5892541)

    def test_get_area(self):
        self._test_get_area(4.8, None, -0.5, 4.7315126)
        self._test_get_area(3.4, 0, 0.2, 0.2818383)


class WC1994MSRTestCase(BaseMSRTestCase):
    MSR_CLASS = WC1994MSR

    def test_median_area_all(self):
        self._test_get_median_area(2.2, None, 0.0325087)
        self._test_get_median_area(1.3, None, 0.0049317)

    def test_median_area_strike_slip(self):
        self._test_get_median_area(3.9, -28.22, 1.2302688)
        self._test_get_median_area(3.9, -45, 1.2302688)
        self._test_get_median_area(3.9, 0, 1.2302688)
        self._test_get_median_area(3.9, 45, 1.2302688)

    def test_median_area_thrust(self):
        self._test_get_median_area(4.1, 50, 1.0665961)
        self._test_get_median_area(4.1, 95, 1.0665961)

    def test_median_area_normal(self):
        self._test_get_median_area(5.9, -59, 92.8966387)
        self._test_get_median_area(5.9, -125, 92.8966387)

    def test_get_std_dev_area(self):
        self.assertEqual(self.msr.get_std_dev_area(None, None), 0.24)
        self.assertEqual(self.msr.get_std_dev_area(20, 4), 0.22)
        self.assertEqual(self.msr.get_std_dev_area(None, 138), 0.22)
        self.assertEqual(self.msr.get_std_dev_area(None, -136), 0.22)
        self.assertEqual(self.msr.get_std_dev_area(None, 50), 0.26)
        self.assertEqual(self.msr.get_std_dev_area(None, -130), 0.22)

    def test_get_area(self):
        self._test_get_area(4.8, 50, 0.3, 6.1944108)
        self._test_get_area(5.6, 138, 1.3, 80.5378441)

    def test_get_std_dev_mag_from_area(self):
        self.assertEqual(self.msr.get_std_dev_mag_from_area(None), 0.24)
        self.assertEqual(self.msr.get_std_dev_mag_from_area(20), 0.23)
        self.assertEqual(self.msr.get_std_dev_mag_from_area(138), 0.23)
        self.assertEqual(self.msr.get_std_dev_mag_from_area(-136), 0.23)
        self.assertEqual(self.msr.get_std_dev_mag_from_area(50), 0.25)
        self.assertEqual(self.msr.get_std_dev_mag_from_area(-130), 0.25)

    def test_get_median_mag_from_area(self):
        self.assertAlmostEqual(
            self.msr.get_median_mag_from_area(50, None), 5.7349906)
        self.assertAlmostEqual(
            self.msr.get_median_mag_from_area(500, 20), 6.7329494)
        self.assertAlmostEqual(
            self.msr.get_median_mag_from_area(500, 138), 6.7329494)
        self.assertAlmostEqual(
            self.msr.get_median_mag_from_area(500, -136), 6.7329494)
        self.assertAlmostEqual(
            self.msr.get_median_mag_from_area(700, 50), 6.8905882)
        self.assertAlmostEqual(
            self.msr.get_median_mag_from_area(800, -130), 6.8911518)

    def test_get_magnitude_from_area(self):
        self.assertAlmostEqual(
            self.msr.get_mag_from_area(100, 45, 0.4), 6.1120000)
        self.assertAlmostEqual(
            self.msr.get_mag_from_area(500, None, 1.3), 7.0269906)
