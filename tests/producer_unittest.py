# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import os
import unittest
import tempfile

from openquake import shapes
from openquake import producer
from tests.utils import helpers

TEST_FILE_PATH = helpers.get_data_path('config.gem')


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
        prod = helpers.WordProducer(path)
        for ((cell_x, cell_y), data) in prod:
            self.assertEqual(data, 'test%s' % int(cell_x))

    def test_filter(self):
        constraint = shapes.RegionConstraint.from_simple((10, 10), (100, 100))

        path = self._make_data_file('test')
        prod = helpers.WordProducer(path)

        # TODO(termie): Right now the bound
        expected = dict(zip(range(10, 101), range(10, 101)))
        for ((cell_x, cell_y), data) in prod.filter(constraint):
            test_cell = expected.pop(int(cell_x))
            self.assertEqual(data, 'test%s' % int(test_cell))

        self.assertEqual(len(expected), 0)

    def test_reset_open_file(self):
        """
        Test the reset() method of a FileProducer object.

        In this case, we want to test the behavior of the reset when the
        producer's file handle is still open.
        """
        fp = producer.FileProducer(TEST_FILE_PATH)

        # the file should be open
        self.assertFalse(fp.file.closed)
        # seek position starts at 0
        self.assertEqual(0, fp.file.tell())

        # change the file seek position to something != 0
        fp.file.seek(1)
        self.assertEqual(1, fp.file.tell())

        fp.reset()

        # the file should be open still
        self.assertFalse(fp.file.closed)
        # verify the file seek position was reset
        self.assertEqual(0, fp.file.tell())

    def test_reset_closed_file(self):
        """
        Test the reset() method of a FileProducer object.

        In this case, we want to test the behavior of the reset when the
        producer's file handle is closed.
        """
        fp = producer.FileProducer(TEST_FILE_PATH)
        file_name = fp.file.name

        # close the file to start the test
        fp.file.close()

        self.assertTrue(fp.file.closed)

        fp.reset()

        # the same file should be open, seek position at 0
        self.assertFalse(fp.file.closed)
        self.assertEqual(file_name, fp.file.name)
        self.assertEqual(0, fp.file.tell())
