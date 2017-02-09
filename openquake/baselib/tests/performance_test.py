#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016-2017 GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import time
import unittest
import pickle
import numpy
from openquake.baselib.performance import Monitor


class MonitorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mon = Monitor('test')

    def test_no_mem(self):
        mon = self.mon('test_no_mem')
        for i in range(3):
            with mon:
                time.sleep(0.1)
        self.assertGreater(mon.duration, 0.3)
        mon.flush()

    def test_mem(self):
        mon = self.mon('test_mem', measuremem=True)
        ls = []
        for i in range(3):
            with mon:
                ls.append(list(range(100000)))  # allocate some RAM
                time.sleep(0.1)
        self.assertGreaterEqual(mon.mem, 0)
        mon.flush()

    def test_children(self):
        mon1 = self.mon('child1')
        mon2 = self.mon('child2')
        with mon1:
            time.sleep(0.1)
        with mon2:
            time.sleep(0.1)
        with mon2:  # called twice on purpose
            time.sleep(0.1)

        data = numpy.concatenate([mon.get_data() for mon in self.mon.children])
        self.assertEqual(list(data['counts']), [1, 2])
        total_time = data['time_sec'].sum()
        self.assertGreaterEqual(total_time, 0.3)
        self.mon.flush()

    def test_pickleable(self):
        pickle.loads(pickle.dumps(self.mon))
