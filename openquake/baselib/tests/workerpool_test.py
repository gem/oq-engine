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
import tempfile
import unittest
from unittest import mock
from openquake.baselib import config, parallel, zeromq as z
from openquake.baselib.workerpool import WorkerMaster, missing_requirements
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


class RequirementsTestCase(unittest.TestCase):
    def test_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fname = os.path.join(tmp, 'requirements.txt')
            with open(fname, 'w') as f:
                f.write('numpy>=1  # installed\n'
                        '-r other.txt\n'
                        'no-such-package-xyz>=1\n'
                        'numpy>=999\n'
                        'numpy>=999 ; python_version < "3"\n'
                        'https://x/no_such_wheel-1.0-py3-none-any.whl'
                        ' ; sys_platform == "linux"\n'
                        'https://x/no_such_wheel2-1.0-py3-none-any.whl'
                        ' ; sys_platform == "win32"\n')
            self.assertEqual(missing_requirements(fname),
                             ['no-such-package-xyz', 'numpy',
                              'no_such_wheel'])


def fake_docker(*args, check=False):
    # the swarm has two nodes, with 8 and 4 cores
    if args[:2] == ('node', 'inspect'):
        return '8000000000\n4000000000'
    if args[:2] == ('node', 'ls'):
        return 'id1\nid2'
    return ''


class SwarmTestCase(unittest.TestCase):
    def test_hosts(self):
        # the nodes are the static host_cores, also with a swarm
        zworkers = dict(ctrl_port='1909',
                        host_cores='10.0.0.1 -1,10.0.0.2 -1',
                        swarm_image='oq-engine')
        master = WorkerMaster(zworkers)
        self.assertEqual(master.host_cores,
                         [('10.0.0.1', 1909, '-1'),
                          ('10.0.0.2', 1909, '-1')])

    def test_code_mount(self):
        # the service reads the engine code from swarm_code_dir
        calls = []

        def record(*args, check=False):
            calls.append(args)
            return fake_docker(*args, check=check)

        zworkers = dict(ctrl_port='1909', host_cores='',
                        swarm_image='oq-engine',
                        swarm_code_dir='/opt/openquake/oq-engine')
        with mock.patch('openquake.baselib.workerpool._docker', record):
            WorkerMaster(zworkers).start()
        [create] = [c for c in calls if c[:2] == ('service', 'create')]
        self.assertIn('PYTHONPATH=/opt/openquake/oq-engine', create)
        self.assertIn('type=bind,source=/opt/openquake/oq-engine,'
                      'target=/opt/openquake/oq-engine,readonly', create)

    def test_memory(self):
        # 2.5 GB per core on the smallest node, which has 4 cores
        zworkers = dict(ctrl_port='1909', host_cores='',
                        swarm_image='oq-engine')
        with mock.patch('openquake.baselib.workerpool._docker', fake_docker):
            master = WorkerMaster(zworkers)
            self.assertEqual(master._swarm_memory(), str(10 * 1024**3))


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
