# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
import tempfile

from eventlet import greenpool
from eventlet import timeout

from opengem import producer
from opengem import region
#from opengem import test


def generate_data(prefix):
    for i in xrange(1, 110):
        yield ((i, i), '%s%s' % (prefix, i))


class ShamlOutputFileTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = greenpool.GreenPool()
        self.files = []

    def tearDown(self):
        for f in self.files:
            try:
                os.unlink(f)
            except Exception:
                pass

    def _make_data_file(self, prefix):
        fd, path = tempfile.mkstemp(suffix='.test')
        f = open(path, 'w')
        for cell, word in generate_data(prefix):
            f.write('%d %d %s\n' % (cell[0], cell[1], word))

        f.close()
        self.files.append(path)
        return path

    def test_iterator_interface(self):
        path = self._make_data_file('test')
        prod = test.WordProducer(path)
        for cell, data in prod:
            self.assertEqual(data, 'test%s' % int(cell[0]))

    def test_filter(self):
        constraint = region.RegionConstraint.from_simple((10, 10), (100, 100))

        path = self._make_data_file('test')
        prod = test.WordProducer(path)

        # TODO(termie): Right now the bound
        expected = dict(zip(range(11, 100), range(11, 100)))

        for cell, data in prod.filter(constraint):
            expected.pop(cell[0])
            self.assertEqual(data, 'test%s' % int(cell[0]))
        
        self.assertEqual(len(expected), 0)

    def test_finished(self):
        path = self._make_data_file('test')
        prod = test.WordProducer(path)
        
        def _wait_for_producer():
            timer = timeout.Timeout(0.1)
            prod.finished.wait()
            timer.cancel()
            return True

        self.assertRaises(timeout.Timeout, _wait_for_producer)

        for cell, data in prod:
            self.assertEqual(data, 'test%s' % int(cell[0]))
        
        self.assert_(_wait_for_producer())
        
    def test_nice_coroutines(self):
        first_path = self._make_data_file('first')
        second_path = self._make_data_file('second')
        
        first_prod = test.WordProducer(first_path)
        second_prod = test.WordProducer(second_path)
        
        output = []

        def consume_first():
            for cell, data in first_prod:
                output.append(data)
        
        def consume_second():
            for cell, data in second_prod:
                output.append(data)
        
        self.pool.spawn(consume_first)
        self.pool.spawn(consume_second)

        self.pool.waitall()
        
        first_count = 0
        second_count = 1

        for i in xrange(20):
            x = output[i]
            if x.startswith('first'):
                first_count += 1
            if x.startswith('second'):
                second_count += 1
        
        # In practice these will probably be equal, but in the case of
        # race conditions or something as long as one doesn't completely
        # overwhelm the other
        self.assert_(first_count > 5)
        self.assert_(second_count > 5)
