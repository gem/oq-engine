# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.



# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
import tempfile

from openquake import producer
from openquake import shapes
from utils import test


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
