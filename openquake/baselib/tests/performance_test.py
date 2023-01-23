# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2016-2023 GEM Foundation
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
from openquake.baselib.performance import Monitor, kollapse


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
        self.assertGreaterEqual(mon.mem, 0)

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


class KollapseTestCase(unittest.TestCase):
    def test_small(self):
        # build a small structured array
        dtlist = [('mdbin', numpy.uint32), ('rake', numpy.float64),
                  ('sids', numpy.uint32)]
        N = 10
        arr = numpy.zeros(N, dtlist)
        rng = numpy.random.default_rng(42)
        arr['mdbin'] = rng.integers(50, size=N)
        arr['rake'] = rng.random(N) * 360
        arr['sids'] = rng.integers(1000, size=N)
        sids = []
        for rec in kollapse(arr, ['mdbin']):
            sids.append(arr['sids'][arr['mdbin'] == rec['mdbin']])
        expected_sids = [[450, 858, 631], [276], [554, 887], [92],
                         [827], [227], [63]]
        numpy.testing.assert_equal(sids, expected_sids)

        # now test kollapse with an aggregate field afield='sids'
        out, allsids = kollapse(arr, ['mdbin'], afield='sids')
        numpy.testing.assert_equal(allsids, expected_sids)

    def test_big(self):
        # build a very large structured array
        dtlist = [('mdbin', numpy.uint32), ('rake', numpy.float64),
                  ('sids', numpy.uint32)]
        N = 10_000_000
        arr = numpy.zeros(N, dtlist)
        rng = numpy.random.default_rng(42)
        arr['mdbin'] = rng.integers(50, size=N)
        arr['rake'] = rng.random(N) * 360
        arr['sids'] = rng.integers(1000, size=N)
        t0 = time.time()
        mean = kollapse(arr, ['mdbin'])
        sids = []
        for mdbin in mean['mdbin']:
            sids.append(arr['sids'][arr['mdbin'] == mdbin])
        print([len(s) for s in sids])
        dt = time.time() - t0
        print('Grouped %d elements in %.1f seconds' % (N, dt))
