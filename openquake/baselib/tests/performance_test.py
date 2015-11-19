import time
import unittest
import pickle
from openquake.baselib.performance import PerformanceMonitor


# NB: tests for the HDF5 functionality are in risklib
class MonitorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mon = PerformanceMonitor('test')

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

    def test_pickleable(self):
        pickle.loads(pickle.dumps(self.mon))
