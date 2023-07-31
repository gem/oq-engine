# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
import unittest.mock as mock
import time
import shutil
import unittest
import itertools
import tempfile
import numpy
import sys
import pytest
from openquake.baselib import parallel, general, hdf5, performance


def get_length(data, monitor):
    return {'n': len(data)}


def gfunc(text, monitor):
    for char in text:
        yield char * 3


def supertask(text, monitor):
    # a supertask spawning subtasks of kind get_length
    with monitor('waiting'):
        time.sleep(.1)
    yield {}
    for block in general.block_splitter(text, max_weight=10):
        items = [(k, len(list(grp))) for k, grp in itertools.groupby(block)]
        if len(items) == 1:
            # for instance items = [('i', 1)]
            k, v = items[0]
            yield get_length(k * v, monitor)
            return
        # for instance items = [('a', 4), ('e', 4), ('i', 2)]
        for k, v in items:
            yield get_length, k * v


def countletters(text1, text2, monitor):
    for block in general.block_splitter(text1 + text2, 5):
        yield get_length, ''.join(block)


class StarmapTestCase(unittest.TestCase):
    monitor = parallel.Monitor()

    @classmethod
    def setUpClass(cls):
        parallel.Starmap.init()  # initialize the pool

    def test_apply(self):
        res = parallel.Starmap.apply(
            get_length, (numpy.arange(10),), concurrent_tasks=3).reduce()
        self.assertEqual(res, {'n': 10})  # chunks [4, 4, 2]

    # this case is non-trivial since there is a key, so two groups are
    # generated even if everything is run in a single core
    def test_apply_no_tasks(self):
        res = parallel.Starmap.apply(
            get_length, ('aaabb',),
            concurrent_tasks=0, key=lambda char: char)
        # chunks [['a', 'a', 'a'], ['b', 'b']]
        partial_sums = sorted(dic['n'] for dic in res)
        self.assertEqual(partial_sums, [2, 3])

    def test_apply_maxweight(self):
        res = parallel.Starmap.apply(
            get_length, ('aaabb',), maxweight=2,
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
                get_length, [(data,)]).submit_all()
        for key, val in res.items():
            res[key] = val.reduce()
        self.assertEqual(res, {'a': {'n': 10}, 'c': {'n': 15}, 'b': {'n': 20}})

    def test_gfunc(self):
        res = list(parallel.Starmap(gfunc, [('xy',), ('z',)],
                                    distribute='no'))
        self.assertEqual(sorted(res), ['xxx', 'yyy', 'zzz'])

        res = list(parallel.Starmap(gfunc, [('xy',), ('z',)]))
        self.assertEqual(sorted(res), ['xxx', 'yyy', 'zzz'])

    def test_supertask(self):
        # this test has 4 supertasks generating 4 + 5 + 3 + 5 = 17 subtasks
        allargs = [('aaaaeeeeiii',),
                   ('uuuuaaaaeeeeiii',),
                   ('aaaaaaaaeeeeiii',),
                   ('aaaaeeeeiiiiiooooooo',)]
        numchars = sum(len(arg) for arg, in allargs)  # 61
        tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(tmpdir, 'calc_1.hdf5')
        performance.init_performance(tmp)
        smap = parallel.Starmap(supertask, allargs, h5=hdf5.File(tmp, 'a'))
        res = smap.reduce()
        smap.h5.close()
        self.assertEqual(res, {'n': numchars})
        # check that the correct information is stored in the hdf5 file
        with hdf5.File(tmp, 'r') as h5:
            num = general.countby(h5['performance_data'][()], 'operation')
            self.assertEqual(num[b'waiting'], 4)
            self.assertEqual(num[b'total supertask'], 4)  # tasks
            self.assertEqual(num[b'total get_length'], 17)  # subtasks
            info = h5['task_info'][()]
            dic = dict(general.fast_agg3(info, 'taskname', ['received']))
            self.assertGreater(dic[b'get_length'], 0)
            self.assertGreater(dic[b'supertask'], 0)
        shutil.rmtree(tmpdir)

    def test_countletters(self):
        data = [('hello', 'world'), ('ciao', 'mondo')]
        smap = parallel.Starmap(countletters, data)
        self.assertEqual(smap.reduce(), {'n': 19})

    @classmethod
    def tearDownClass(cls):
        parallel.Starmap.shutdown()


class ThreadPoolTestCase(unittest.TestCase):
    def test(self):
        with mock.patch.dict(os.environ, {'OQ_DISTRIBUTE': 'threadpool'}):
            parallel.Starmap.init()
            try:
                res = parallel.Starmap.apply(
                    get_length, (numpy.arange(10),),
                    concurrent_tasks=3).reduce()
                self.assertEqual(res, {'n': 10})  # chunks [4, 4, 2]
            finally:
                parallel.Starmap.shutdown()


def sum_chunk(slc, hdf5path):
    with hdf5.File(hdf5path, 'r') as f:
        return f['array'][slc].sum()


def pool_starmap(func, allargs, h5):
    import multiprocessing
    with multiprocessing.get_context('spawn').Pool() as pool:
        for i, res in enumerate(pool.starmap(func, allargs)):
            perf = numpy.array([(func.__name__, 0, 0, i, i)],
                               performance.perf_dt)
            hdf5.extend(h5['performance_data'], perf)
            yield res


class SWMRTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tmpdir = tempfile.mkdtemp()
        cls.tmp = os.path.join(tmpdir, 'calc_1.hdf5')
        with hdf5.File(cls.tmp, 'w') as h:
            h['array'] = numpy.arange(100)
        performance.init_performance(cls.tmp)

    def test(self):
        allargs = []
        for s in range(0, 100, 10):
            allargs.append((slice(s, s + 10), self.tmp))
        with hdf5.File(self.tmp, 'a') as h5:
            h5.swmr_mode = True
            tot = sum(pool_starmap(sum_chunk, allargs, h5))
        self.assertEqual(tot, 4950)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.dirname(cls.tmp))


def process_elements(elements, timefactor, monitor):
    for el in elements:
        time.sleep(el * timefactor)
    return sum(elements)


class SplitTaskTestCase(unittest.TestCase):
    def test(self):
        rng = numpy.random.default_rng(42)
        elements = rng.random(size=100)
        tmpdir = tempfile.mkdtemp()
        tmp = os.path.join(tmpdir, 'calc_1.hdf5')
        print('Creating', tmp)
        duration = .5
        outs_per_task = 5
        timefactor = .2
        with hdf5.File(tmp, 'w') as h5:
            performance.init_performance(h5)
            smap = parallel.Starmap(process_elements, h5=h5)
            smap.submit_split((elements, timefactor), duration, outs_per_task)
            res = smap.reduce(acc=0)
        self.assertAlmostEqual(res, 48.6718458266)
        """
        with hdf5.File(tmp, 'w') as h5:
            performance.init_performance(h5)
            res = parallel.Starmap.apply_split(
                process_elements, (elements, timefactor),
                h5=h5, duration=duration
            ).reduce(acc=0)
        self.assertAlmostEqual(res, 48.6718458266)
        """
        shutil.rmtree(tmpdir)


def update_array(shared, index):
    with shared as array:
        for i in range(index):
            for j in range(index):
                array[i, j] *= .99


class SharedMemoryTestCase(unittest.TestCase):
    @pytest.mark.skipif(
        sys.platform == 'win32',
        reason="Skipping on Windows")
    def test(self):
        shape = 10, 10
        smap = parallel.Starmap(update_array)
        shared = smap.create_shared(shape, value=1.)
        for i in range(shape[1]):
            smap.submit((shared, i))
        smap.reduce()
        print()
        with shared as array:
            print(array)
        parallel.Starmap.shutdown()
