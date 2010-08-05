# vim: tabstop=4 shiftwidth=4 softtabstop=4

import unittest

from eventlet import greenpool
from eventlet import timeout

from opengem import computation
from opengem import test


class ComputationTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = greenpool.GreenPool()

    def test_basic(self):
        cell = (50, 50)
        comp = test.ConcatComputation(self.pool, cell)

        self.pool.spawn(comp.compute)
    

        def _get_result():
            timer = timeout.Timeout(0.01)
            rv = comp.result.wait()
            timer.cancel()
            return rv
        
        # should time out because we haven't given it data
        self.assertRaises(timeout.Timeout, _get_result)
        
        comp.receive('shake', 'one')
        comp.receive('roll', 'two')

        result_cell, result = _get_result()

        self.assertEqual(result_cell, cell)
        self.assertEqual(result, 'one:two')
