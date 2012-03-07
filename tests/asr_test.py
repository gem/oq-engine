import unittest

from nhe.sr.wc1994 import WC1994


class WC1994ASRTestCase(unittest.TestCase):

    def setUp(self):
        self.asr = WC1994()

    def test_get_std_dev_mag(self):
        self.assertEqual(self.asr.get_std_dev_mag(None), 0.24)
        self.assertEqual(self.asr.get_std_dev_mag(20), 0.23)
        self.assertEqual(self.asr.get_std_dev_mag(138), 0.23)
        self.assertEqual(self.asr.get_std_dev_mag(-136), 0.23)
        self.assertEqual(self.asr.get_std_dev_mag(50), 0.25)
        self.assertEqual(self.asr.get_std_dev_mag(-130), 0.25)

    def test_get_median_mag(self):
        self.assertAlmostEqual(self.asr.get_median_mag(50, None), 5.7349906)
        self.assertAlmostEqual(self.asr.get_median_mag(500, 20), 6.7329494)
        self.assertAlmostEqual(self.asr.get_median_mag(500, 138), 6.7329494)
        self.assertAlmostEqual(self.asr.get_median_mag(500, -136), 6.7329494)
        self.assertAlmostEqual(self.asr.get_median_mag(700, 50), 6.8905882)
        self.assertAlmostEqual(self.asr.get_median_mag(800, -130), 6.8911518)

    def test_get_mag(self):
        self.assertAlmostEqual(self.asr.get_mag(100, 45, 0.4), 6.1120000)
        self.assertAlmostEqual(self.asr.get_mag(500, None, 1.3), 7.0269906)
