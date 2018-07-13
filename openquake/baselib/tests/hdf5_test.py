#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

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
import os
import numpy
import unittest
from openquake.baselib import general, hdf5


class Hdf5TestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = general.gettemp(suffix='.hdf5')

    def test_extend3(self):
        nrows = hdf5.extend3(self.tmp, 'dset', numpy.zeros(3))
        self.assertEqual(nrows, 3)

    def test_extend3_vlen(self):
        data = numpy.array([[], [1, 2], [3]], hdf5.vfloat32)
        nrows = hdf5.extend3(self.tmp, 'dset', data)
        self.assertEqual(nrows, 3)
        with hdf5.File(self.tmp, 'r') as f:
            print(f['dset'].value)

    def test_extend3_vlen_same_len(self):
        data = numpy.array([[4, 1], [1, 2], [3, 1]], hdf5.vfloat32)
        nrows = hdf5.extend3(self.tmp, 'dset', data)
        self.assertEqual(nrows, 3)
        with hdf5.File(self.tmp, 'r') as f:
            print(f['dset'].value)

    def tearDown(self):
        os.remove(self.tmp)
