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


class GridTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = greenpool.GreenPool()

    def test_cell(self):
        cell = (50, 50)
        grid = computation.Grid(pool=self.pool, 
                                cell_factory=test.ConcatComputation)
        
        test_cell = grid.cell(cell)
        self.assert_(isinstance(test_cell, test.ConcatComputation))

        test_cell_again = grid.cell(cell)
        self.assertEqual(test_cell_again, test_cell)

    def test_basic(self):
        cell = (50, 50)
        first_grid = computation.Grid(pool=self.pool, 
                                      cell_factory=test.ConcatComputation)

        # check that queue is empty
        for x in first_grid.results():
            self.fail('queue should have been empty')
    
        def _get_result(grid):
            timer = timeout.Timeout(0.01)
            rv = grid.results().next()
            timer.cancel()
            return rv

        test_cell = first_grid.cell(cell)

        # should time out because we haven't given it data
        self.assertRaises(timeout.Timeout, _get_result, first_grid)
        
        # this time give it some data so it won't timeout
        next_grid = computation.Grid(pool=self.pool, 
                                     cell_factory=test.ConcatComputation)

        test_cell = next_grid.cell(cell)
        test_cell.receive('shake', 'one')
        test_cell.receive('roll', 'two')

        result_cell, result = _get_result(next_grid)

        self.assertEqual(result_cell, cell)
        self.assertEqual(result, 'one:two')

    def test_clear(self):
        cell = (50, 50)
        next_grid = computation.Grid(pool=self.pool, 
                                     cell_factory=test.ConcatComputation)

        test_cell = next_grid.cell(cell)
        test_cell.receive('shake', 'one')
        test_cell.receive('roll', 'two')

        self.assertEqual(next_grid.size(), 1)

        for cell, result in next_grid.results(clear=True):
            pass

        self.assertEqual(next_grid.size(), 0)
