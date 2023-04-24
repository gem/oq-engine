# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2023 GEM Foundation
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

import time
import unittest
from openquake.baselib import config
from openquake.baselib.workerpool import WorkerMaster
from openquake.baselib.parallel import Starmap
from openquake.baselib.general import socket_ready


def double(x):
    return 2 * x


class WorkerPoolTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.z = config.zworkers.copy()
        cls.z['host_cores'] = '127.0.0.1 4'
        hostport = '127.0.0.1', int(cls.z['ctrl_port']) + 1
        if not socket_ready(hostport):
            raise unittest.SkipTest('The task streamer is off')
        cls.master = WorkerMaster(cls.z)
        cls.master.start()

    def test(self):
        iterargs = ((i,) for i in range(10))
        smap = Starmap(double, iterargs, distribute='zmq')
        self.assertEqual(sum(res for res in smap), 90)
        # sum[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test_status(self):
        time.sleep(1)  # wait a bit for the workerpool to start
        self.assertEqual(self.master.status(), [('127.0.0.1', 'running')])

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
        config.zworkers = cls.z
