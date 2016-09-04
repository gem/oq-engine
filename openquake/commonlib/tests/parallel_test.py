# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy
from openquake.commonlib import parallel


def get_length(data):
    return {'n': len(data)}


def get_len(data, monitor):
    with monitor:
        result = {'n': len(data)}
    monitor.flush()
    return result


class TaskManagerTestCase(unittest.TestCase):
    monitor = parallel.Monitor()

    def test_apply_reduce(self):
        res = parallel.apply(
            get_length, (numpy.arange(10),), concurrent_tasks=3).reduce()
        self.assertEqual(res, {'n': 10})  # chunks [4, 4, 2]

    # this case is non-trivial since there is a key, so two groups are
    # generated even if everything is run in a single core
    def test_apply_reduce_no_tasks(self):
        res = parallel.apply(
            get_length, ('aaabb',), concurrent_tasks=0,
            key=lambda char: char).reduce()
        self.assertEqual(res, {'n': 5})
        # chunks [['a', 'a', 'a'], ['b', 'b']]

    def test_spawn(self):
        all_data = [
            ('a', list(range(10))), ('b', list(range(20))),
            ('c', list(range(15)))]
        res = {key: parallel.starmap(get_length, [(data,)])
               for key, data in all_data}
        for key, val in res.items():
            res[key] = val.reduce()
        parallel.TaskManager.restart()
        self.assertEqual(res, {'a': {'n': 10}, 'c': {'n': 15}, 'b': {'n': 20}})

    def test_no_flush(self):
        mon = parallel.Monitor('test')
        res = parallel.safely_call(get_len, ('ab', mon))
        self.assertIn('Monitor(\'test\').flush() must not be called'
                      ' by get_len!', res[0])
        self.assertEqual(res[1], RuntimeError)
        self.assertEqual(res[2].operation, mon.operation)
