import unittest
import numpy
from openquake.commonlib import parallel


def get_length(data):
    return {'n': len(data)}


class TaskManagerTestCase(unittest.TestCase):
    monitor = parallel.DummyMonitor()

    def test_apply_reduce(self):
        res = parallel.apply_reduce(
            get_length, (numpy.arange(10),), concurrent_tasks=3)
        self.assertEqual(res, {'n': 10})
        self.assertEqual(map(len, parallel.apply_reduce._chunks), [4, 4, 2])

    # this case is non-trivial since there is a key, so two groups are
    # generated even if everything is run in a single core
    def test_apply_reduce_no_tasks(self):
        res = parallel.apply_reduce(
            get_length, ('aaabb',), concurrent_tasks=0,
            key=lambda char: char)
        self.assertEqual(res, {'n': 5})
        self.assertEqual(parallel.apply_reduce._chunks,
                         [['a', 'a', 'a'], ['b', 'b']])

    def test_spawn(self):
        all_data = [
            ('a', range(10)), ('b', range(20)), ('c', range(15))]
        res = {key: parallel.starmap(get_length, [(data,)])
               for key, data in all_data}
        for key, val in res.iteritems():
            res[key] = val.reduce()
        parallel.TaskManager.restart()
        self.assertEqual(res, {'a': {'n': 10}, 'c': {'n': 15}, 'b': {'n': 20}})
