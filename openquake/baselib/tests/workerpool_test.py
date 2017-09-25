#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from openquake.baselib.workerpool import WorkerMaster
from openquake.baselib.performance import Monitor


def double(x, mon):
    return 2 * x


class WorkerPoolTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = 'tcp://127.0.0.1:5000-5100'
        cls.master = WorkerMaster('ipc://starmap', 'tcp://127.0.0.1:1910')
        cls.master.start('2908', [('127.0.0.1', '4')])

    def test1(self):
        mon = Monitor()
        iterargs = ((i, mon) for i in range(10))
        res = list(self.master.starmap(self.url, double, iterargs))
        self.assertEqual(sum(r[0] for r in res), 90)
        # sum[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test2(self):
        mon = Monitor()
        iterargs = ((i, mon) for i in range(5))
        res = list(self.master.starmap(self.url, double, iterargs))
        self.assertEqual(sum(r[0] for r in res), 20)  # sum[0, 2, 4, 6, 8]

    @classmethod
    def tearDownClass(cls):
        cls.master.stop()
