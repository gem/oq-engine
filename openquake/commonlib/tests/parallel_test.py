import unittest
from openquake.commonlib import parallel


def get_length(data):
    return {'n': len(data)}


class TaskManagerTestCase(unittest.TestCase):
    def test_apply_reduce(self):
        res = parallel.apply_reduce(
            get_length, (range(10),), concurrent_tasks=3)
        self.assertEqual(res, {'n': 10})
        self.assertEqual(map(len, parallel.apply_reduce._chunks), [4, 4, 2])

    def test_spawn(self):
        all_data = [
            ('a', range(10)), ('b', range(20)), ('c', range(15))]
        res = {key: parallel.starmap(get_length, [(data,)])
               for key, data in all_data}
        for key, val in res.iteritems():
            res[key] = val.result()
        parallel.TaskManager.restart()
        self.assertEqual(res, {'a': {'n': 10}, 'c': {'n': 15}, 'b': {'n': 20}})
