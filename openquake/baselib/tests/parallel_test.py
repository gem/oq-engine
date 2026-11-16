# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
import time
import shutil
import unittest
import itertools
import tempfile
import logging
from unittest import mock
import numpy
import pandas

from openquake.baselib import parallel, general, hdf5, performance, zeromq


def process_df(df, monitor):
    acc = dict(mag=[], dist=[])
    for (mag, dist) in zip(df.mag, df.dist):
        acc['mag'].append(mag)
        acc['dist'].append(dist * 2)
    return pandas.DataFrame(acc)


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


class StallDiagnosticsTestCase(unittest.TestCase):

    def setUp(self):
        self.smap = parallel.Starmap.__new__(parallel.Starmap)
        self.smap.tasks = {1: None}
        self.smap.calc_id = 42
        self.result_socket = mock.Mock()
        self.result_socket.zsocket.poll.return_value = 0

    def test_socket_recovery(self):
        sock = zeromq.Socket('tcp://127.0.0.1:1909', zeromq.zmq.REP, 'bind')
        sock.port = 1909
        sock.zsocket = mock.Mock(closed=True)
        sock.zsocket.poll.side_effect = [
            False, True, False, zeromq.zmq.ZMQError()]
        sock.zsocket.recv_pyobj.return_value = 'recovered'
        with mock.patch.object(zeromq.time, 'monotonic',
                               side_effect=[0, 200, 201, 401]), \
                mock.patch.object(zeromq.logging, 'debug') as log:
            self.assertEqual(list(sock), ['recovered'])
        self.assertEqual(log.call_count, 2)
        for call in log.call_args_list:
            self.assertTrue(call.args[0].startswith('No message received'))

    def test_poll_timeout(self):
        modes = ('processpool', 'zmq', 'slurm', 'threadpool')
        for mode, waited, debug in itertools.product(
                modes, (30, 199, 200), (False, True)):
            with self.subTest(mode=mode, waited=waited, debug=debug):
                smap = mock.Mock(distribute=mode)
                with mock.patch.object(logging.getLogger(), 'isEnabledFor',
                                       return_value=debug):
                    parallel.Starmap.poll_timeout(smap, 'socket', waited)
                self.assertEqual(smap.check_tasks_alive.call_count,
                                 int(mode == 'processpool'))
                expected = mode in ('zmq', 'slurm') and waited >= 200
                self.assertEqual(smap._zmq_stall_report.call_count,
                                 int(expected))

    def test_worker_failure_and_throttling(self):
        with mock.patch.object(parallel, 'host_cores', ['127.0.0.1 1']), \
                mock.patch.object(parallel, 'Socket',
                                  side_effect=RuntimeError('offline')) as sock, \
                mock.patch.object(parallel.time, 'monotonic',
                                  side_effect=[0, 199, 200]), \
                self.assertLogs(level=logging.DEBUG) as log:
            for _ in range(3):
                self.smap._zmq_stall_report(self.result_socket)
        self.assertEqual(sock.call_count, 2)
        self.assertEqual(len(log.records), 4)
        self.assertEqual([r.levelno for r in log.records],
                         [logging.DEBUG, logging.WARNING] * 2)
        self.assertIn('Could not query workerpool', log.records[-1].message)

    def test_unreachable_worker(self):
        # An unreachable worker may still be running the outstanding task.
        idle, offline = mock.MagicMock(), mock.MagicMock()
        idle.__enter__.return_value.send.side_effect = [1, '', 0.]
        offline.__enter__.side_effect = zeromq.TimeoutError('offline')
        with mock.patch.object(parallel, 'host_cores',
                               ['127.0.0.1 1', '127.0.0.2 1']), \
                mock.patch.object(parallel, 'Socket',
                                  side_effect=[idle, offline]):
            self.smap._zmq_stall_report(self.result_socket)
        self.result_socket.zsocket.poll.assert_not_called()

    def test_memory_query_failure(self):
        for busy in ('42-1', ''):
            with self.subTest(busy=busy), \
                    mock.patch.object(parallel, 'host_cores',
                                      ['127.0.0.1 1']), \
                    mock.patch.object(parallel, 'Socket') as cls:
                self.smap.__dict__.pop('_last_stall_report', None)
                cls.return_value.__enter__.return_value.send.side_effect = [
                    1, busy, zeromq.TimeoutError('memory query')]
                if busy:
                    self.smap._zmq_stall_report(self.result_socket)
                else:
                    with self.assertRaisesRegex(RuntimeError, 'Lost 1'):
                        self.smap._zmq_stall_report(self.result_socket)

    def test_idle_workers_without_results(self):
        with mock.patch.object(parallel, 'host_cores', ['127.0.0.1 1']), \
                mock.patch.object(parallel, 'Socket') as cls:
            cls.return_value.__enter__.return_value.send.side_effect = [
                1, '', 0.]
            with self.assertRaisesRegex(RuntimeError, 'Lost 1'):
                self.smap._zmq_stall_report(self.result_socket)
        self.result_socket.zsocket.poll.assert_called_once_with(0)

    def test_result_arrives_during_queries(self):
        with zeromq.context.socket(zeromq.zmq.PULL) as receiver:
            port = receiver.bind_to_random_port('tcp://127.0.0.1')
            addr = 'tcp://127.0.0.1:%d' % port
            with zeromq.Socket(addr, zeromq.zmq.PUSH, 'connect') as sender:
                def reply(cmd):
                    if cmd == 'get_num_workers':
                        sender.send('completed task result')
                        self.assertTrue(receiver.poll(1000))
                        return 1
                    return '' if cmd == 'get_executing' else 0.

                with mock.patch.object(parallel, 'host_cores',
                                       ['127.0.0.1 1']), \
                        mock.patch.object(parallel, 'Socket') as cls:
                    worker = cls.return_value.__enter__.return_value
                    worker.send.side_effect = reply
                    sock = mock.Mock(zsocket=receiver)
                    self.smap._zmq_stall_report(sock)
                self.assertEqual(receiver.recv_pyobj(),
                                 'completed task result')


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

    def test_apply_to_dataframe(self):
        orig_df = pandas.DataFrame(dict(mag=[5.0, 5.1, 5.2, 5.3],
                                        dist=[100., 110., 120., 99.]))
        smap = parallel.Starmap.apply(process_df, (orig_df,))
        out_df = pandas.concat(smap).sort_values('mag')
        self.assertEqual(list(out_df.mag), [5.0, 5.1, 5.2, 5.3])
        self.assertEqual(list(out_df.dist), [200.0, 220.0, 240.0, 198.0])

    @classmethod
    def tearDownClass(cls):
        parallel.Starmap.shutdown()


def sum_chunk(slc, hdf5path):
    with hdf5.File(hdf5path, 'r') as f:
        return f['array'][slc].sum()


def multispawn(func, allargs, h5):
    import multiprocessing
    parallel.multispawn(func, allargs)
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
            tot = sum(multispawn(sum_chunk, allargs, h5))
        self.assertEqual(tot, 4950)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.dirname(cls.tmp))


def process_elements(elements, timefactor, monitor):
    for el in elements:
        time.sleep(el * timefactor)
    return sum(elements)


def update(s_array, index, value, monitor):
    """
    Update a shared array
    """
    with s_array as arr:
        arr[index] = value


class SharedArrayTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s_array = parallel.SharedArray((2, 2), float, 0.)

    @classmethod
    def tearDownClass(cls):
        cls.s_array.unlink()
        parallel.Starmap.shutdown()

    def test(self):
        parallel.Starmap(update, [(self.s_array, index, value)
                                  for index, value in zip([0, 1], [.1, .2])]
        ).reduce()
        with self.s_array as arr:
            numpy.testing.assert_allclose(arr, [[.1, .1], [.2, .2]])
