from decimal import Decimal

import unittest

from nhe.common.pmf import PMF


class PMFTestCase(unittest.TestCase):
    def test_creation(self):
        data = [(Decimal('0.1'), i) for i in xrange(10)]
        pmf = PMF(data[:])
        self.assertEqual(pmf.data, data)

    def test_wrong_sum(self):
        data = [(0.1, i) for i in xrange(10)]
        self.assertRaises(RuntimeError, PMF, data)

    def test_empty_data(self):
        self.assertRaises(RuntimeError, PMF, [])
