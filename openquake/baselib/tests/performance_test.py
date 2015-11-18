import time
import unittest
import pickle
import h5py
import numpy
from openquake.baselib.performance import PerformanceMonitor, perf_dt
from openquake.baselib.hdf5 import Hdf5Dataset


class MonitorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fname = '/tmp/x.h5'
        Hdf5Dataset.create(h5py.File(fname, 'w'), 'performance_data', perf_dt)
        cls.mon = PerformanceMonitor('test', fname)

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
        mon1 = self.mon('child1', autoflush=True)
        mon2 = self.mon('child2', autoflush=True)
        with mon1:
            time.sleep(0.1)
        with mon2:
            time.sleep(0.1)
        with mon2:  # called twice on purpose
            time.sleep(0.1)
        self.mon.flush()
        data = self.mon.performance()
        total_time = data['time_sec'].sum()
        self.assertGreaterEqual(total_time, 0.2)

    def test_pickleable(self):
        pickle.loads(pickle.dumps(self.mon))

    @classmethod
    def tearDownClass(cls):
        data = cls.mon.performance()
        numpy.testing.assert_equal(
            data['operation'], ['child1', 'child2', 'test_mem', 'test_no_mem'])
        numpy.testing.assert_equal(
            data['counts'], [1, 2, 1, 1])
        assert data['time_sec'].sum() > 0
        assert data['memory_mb'].sum() > 0
