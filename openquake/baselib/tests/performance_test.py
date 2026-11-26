# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2016-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import time
import unittest
import pickle
import numpy
from openquake.baselib import hdf5
from openquake.baselib.performance import (
    Monitor, init_performance, read_task_sent, save_task_sent)


# Starmap._loop updates task_sent as tasks complete. Check migration of the
# older format and visibility to SWMR readers during those updates.
def test_task_sent_swmr(tmp_path):
    path = tmp_path / 'performance.hdf5'
    before = {'hazard': {'sources': 12}, 'risk': {'assets': 24}}
    after = {'hazard': {'sources': 35}, 'risk': {'gmfs': 42}}
    with hdf5.File(path, 'w') as writer:
        writer['task_sent'] = str(before)  # older file format
        assert read_task_sent(writer) == before
        init_performance(writer, swmr=True)
        with hdf5.File(path, 'r') as reader:
            assert read_task_sent(reader) == before
            save_task_sent(writer, {'hazard': after['hazard']})
            save_task_sent(writer, {'risk': after['risk']})
            reader['task_sent'].refresh()
            assert read_task_sent(reader) == after


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

    def test_mem(self):
        mon = self.mon('test_mem', measuremem=True)
        ls = []
        for i in range(3):
            with mon:
                ls.append(list(range(100000)))  # allocate some RAM
                time.sleep(0.1)

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

    def test_pickleable(self):
        pickle.loads(pickle.dumps(self.mon))
