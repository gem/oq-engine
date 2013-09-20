import unittest

from openquake.hazardlib import scalerel


class AvailableScaleRelTestCase(unittest.TestCase):

    def test_get_available_scalerel(self):
        self.assertEqual({'WC1994': scalerel.wc1994.WC1994,
                          'PeerMSR': scalerel.peer.PeerMSR,
                          'CEUS2011': scalerel.ceus2011.CEUS2011},
                         dict(scalerel.get_available_scalerel()))

    def test_get_available_area_scalerel(self):
        self.assertEqual({'WC1994': scalerel.wc1994.WC1994},
                         dict(scalerel.get_available_area_scalerel()))

    def test_get_available_magnitude_scalerel(self):
        self.assertEqual({'PeerMSR': scalerel.peer.PeerMSR,
                          'WC1994': scalerel.wc1994.WC1994,
                          'CEUS2011': scalerel.ceus2011.CEUS2011},
                         dict(scalerel.get_available_magnitude_scalerel()))

    def test_get_available_sigma_area_scalerel(self):
        self.assertEqual({'WC1994': scalerel.wc1994.WC1994},
                         dict(scalerel.get_available_sigma_area_scalerel()))

    def test_get_available_sigma_magnitude_scalerel(self):
        self.assertEqual({'PeerMSR': scalerel.peer.PeerMSR,
                          'WC1994': scalerel.wc1994.WC1994},
                         dict(scalerel.get_available_sigma_magnitude_scalerel()))
