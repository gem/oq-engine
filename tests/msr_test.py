import unittest

from nhe.msr import Peer


class PeerMSRTestCase(unittest.TestCase):
    def test_median_area(self):
        msr = Peer()
        self.assertAlmostEqual(msr.get_median_area(4.3, 0), 1.9952623)
        self.assertAlmostEqual(msr.get_median_area(5.1, 0), 12.5892541)
