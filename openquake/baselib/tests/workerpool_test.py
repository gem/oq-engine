# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
from openquake.baselib.general import _get_free_port
from openquake.baselib.performance import Monitor


def double(x, mon):
    return 2 * x


# this test is temporarily disabled, the workerpool is tested in the demos
# in travis, since they are run with OQ_DISTRIBUTE=zmq
class _WorkerPoolTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.z = config.zworkers.copy()
        dic = dict(master_host='127.0.0.1',
                   task_in_port=_get_free_port(),
                   task_out_port=_get_free_port(),
                   receiver_ports=_get_free_port())
        config.zworkers.update(dic)
        ctrl_port = _get_free_port()
        host_cores = '127.0.0.1 4'
        cls.master = WorkerMaster(
            dic['master_host'], dic['task_in_port'], dic['task_out_port'],
            ctrl_port, host_cores)
        cls.master.start(streamer=True)

    def test(self):
        mon = Monitor()
        iterargs = ((i,) for i in range(10))
        smap = Starmap(double, iterargs, mon, distribute='zmq')
        self.assertEqual(sum(res for res in smap), 90)
        # sum[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test_status(self):
        time.sleep(1)  # wait a bit for the workerpool to start
        self.assertEqual(self.master.status(), [('127.0.0.1', 'running')])

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
        config.zworkers = cls.z
