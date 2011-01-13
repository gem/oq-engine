# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
import tempfile

from openquake import producer
from openquake import shapes
from openquake import test


def generate_data(prefix):
    for i in xrange(1, 110):
        yield ((i, i), '%s%s' % (prefix, i))


class FileProducerTestCase(unittest.TestCase):
    def setUp(self):
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
        for ((cell_x, cell_y), word) in generate_data(prefix):
            f.write('%d %d %s\n' % (cell_x, cell_y, word))

        f.close()
        self.files.append(path)
        return path

    def test_iterator_interface(self):
        path = self._make_data_file('test')
        prod = test.WordProducer(path)
        for ((cell_x, cell_y), data) in prod:
            self.assertEqual(data, 'test%s' % int(cell_x))

    def test_filter(self):
        constraint = shapes.RegionConstraint.from_simple((10, 10), (100, 100))

        path = self._make_data_file('test')
        prod = test.WordProducer(path)

        # TODO(termie): Right now the bound
        expected = dict(zip(range(10, 101), range(10, 101)))
        for ((cell_x, cell_y), data) in prod.filter(constraint):
            test_cell = expected.pop(int(cell_x))
            self.assertEqual(data, 'test%s' % int(test_cell))
        
        self.assertEqual(len(expected), 0)
