# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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

import os
import mock
import unittest
import numpy
from openquake.baselib import parallel

try:
    import celery
except ImportError:
    celery = None


def get_length(data, monitor):
    return {'n': len(data)}


class StarmapTestCase(unittest.TestCase):
    monitor = parallel.Monitor()

    @classmethod
    def setUpClass(cls):
        parallel.Starmap.init()  # initialize the pool

    def test_apply(self):
        res = parallel.Starmap.apply(
            get_length, (numpy.arange(10), self.monitor),
            concurrent_tasks=3).reduce()
        self.assertEqual(res, {'n': 10})  # chunks [4, 4, 2]

    # this case is non-trivial since there is a key, so two groups are
    # generated even if everything is run in a single core
    def test_apply_no_tasks(self):
        res = parallel.Starmap.apply(
            get_length, ('aaabb', self.monitor),
            concurrent_tasks=0, key=lambda char: char)
        # chunks [['a', 'a', 'a'], ['b', 'b']]
        partial_sums = sorted(dic['n'] for dic in res)
        self.assertEqual(partial_sums, [2, 3])

    def test_apply_maxweight(self):
        res = parallel.Starmap.apply(
            get_length, ('aaabb', self.monitor), maxweight=2,
            key=lambda char: char)
        # chunks ['aa', 'ab', 'b']
        partial_sums = sorted(dic['n'] for dic in res)
        self.assertEqual(partial_sums, [1, 2, 2])

    def test_spawn(self):
        all_data = [
            ('a', list(range(10))), ('b', list(range(20))),
            ('c', list(range(15)))]
        res = {}
        for key, data in all_data:
            res[key] = parallel.Starmap(
                get_length, [(data, self.monitor)]).submit_all()
        for key, val in res.items():
            res[key] = val.reduce()
        self.assertEqual(res, {'a': {'n': 10}, 'c': {'n': 15}, 'b': {'n': 20}})

    @classmethod
    def tearDownClass(cls):
        parallel.Starmap.shutdown()


class ThreadPoolTestCase(unittest.TestCase):
    def test(self):
        monitor = parallel.Monitor()
        with mock.patch.dict(os.environ, {'OQ_DISTRIBUTE': 'threadpool'}):
            parallel.Starmap.init()
            try:
                res = parallel.Starmap.apply(
                    get_length, (numpy.arange(10), monitor),
                    concurrent_tasks=3).reduce()
                self.assertEqual(res, {'n': 10})  # chunks [4, 4, 2]
            finally:
                parallel.Starmap.shutdown()
