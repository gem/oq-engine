
import numpy as np
import unittest
from openquake.hazardlib.imt import SA
from conditional import get_conditional_mean_stds, _get_correlation_mtx
from cross_correlation import BakerJayaram2008


class BakerJayaram2008Test(unittest.TestCase):
    """
    Tests the implementation of the Baker and Jayaram (2008) model. For the
    testing we use the original matlab implementation available at:
    https://web.stanford.edu/~bakerjw/GMPEs.html
    """

    def _test(self, imt_from, imt_to, expected):
        computed = self.cm.get_correlation(imt_from, imt_to)
        msg = 'The computed correlation coefficient is wrong'
        self.assertAlmostEqual(computed, expected, places=7, msg=msg)

    def setUp(self):
        self.cm = BakerJayaram2008()

    def test_01(self):
        imt_from = SA(0.1)
        imt_to = SA(0.5)
        expected = 0.4745240873
        self._test(imt_from, imt_to, expected)

    def test_02(self):
        imt_from = SA(0.15)
        imt_to = SA(0.5)
        expected = 0.5734688765
        self._test(imt_from, imt_to, expected)

    def test_03(self):
        imt_from = SA(0.05)
        imt_to = SA(0.15)
        expected = 0.9153049738
        self._test(imt_from, imt_to, expected)

    def test_04(self):
        imt_from = SA(0.05)
        imt_to = SA(0.10)
        expected = 0.9421213925
        self._test(imt_from, imt_to, expected)
