# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2026 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
from openquake.baselib import config, parallel, zeromq as z
from openquake.baselib.workerpool import WorkerMaster, ssh_args
from openquake.baselib.parallel import Starmap, parse_hostcore


def whoami(x):
    # the parent of a worker process is the workerpool process
    return os.getppid()


class ParseHostcoreTestCase(unittest.TestCase):
    def test_default_port(self):
        self.assertEqual(parse_hostcore('10.0.0.1 4', 1909),
                         ('10.0.0.1', 1909, '4'))

    def test_explicit_port(self):
        self.assertEqual(parse_hostcore('127.0.0.1:1910 -1', '1909'),
                         ('127.0.0.1', 1910, '-1'))

    def test_ssh_args(self):
        host_cores = [('127.0.0.1', 1910, '2'), ('127.0.0.1', 1909, '3')]
        got = [(host, port, cores)
               for host, port, cores, _args in ssh_args(host_cores)]
        self.assertEqual(got, [('127.0.0.1', 1910, '2'),
                               ('127.0.0.1', 1909, '3')])


class WorkerPoolTestCase(unittest.TestCase):
    # two workerpools on the same host, on the two ports after ctrl_port
    @classmethod
    def setUpClass(cls):
        cls.z = config.zworkers.copy()
        base = int(cls.z['ctrl_port'])
        cls.ports = [base, base + 1]
        cls.z['host_cores'] = '127.0.0.1:%d 2,127.0.0.1:%d 2' % tuple(
            cls.ports)
        cls.host_cores = parallel.host_cores[:]
        parallel.host_cores[:] = cls.z['host_cores'].split(',')
        cls.master = WorkerMaster(cls.z)
        cls.master.start()
        cls.status = cls.master.wait(30)

    def test(self):
        iterargs = ((i,) for i in range(10))
        smap = Starmap(whoami, iterargs, distribute='zmq')
        # the tasks alternate between the two workerpools
        pids = {pid for pid in smap}
        # ask the workerpools for their own PIDs: on Windows the Popen
        # pid is the venv launcher, not the process running the pool
        expected = set()
        for port in self.ports:
            url = 'tcp://127.0.0.1:%d' % port
            with z.Socket(url, z.zmq.REQ, 'connect') as sock:
                expected.add(sock.send('getpid'))
        self.assertEqual(pids, expected)

    def test_status(self):
        self.assertEqual(
            self.status,
            [('127.0.0.1:%d' % port, 0, 2) for port in self.ports])

    @classmethod
    def tearDownClass(cls):
        procs = list(cls.master.popens)
        cls.master.stop()
        parallel.host_cores[:] = cls.host_cores
        # the workerpools must exit on their own after the stop command
        codes = [p.returncode for p in procs]
        if codes != [0, 0]:  # explicit, so that it survives python -O
            raise AssertionError('exit codes %s' % codes)
