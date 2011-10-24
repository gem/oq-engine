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
import tempfile
import shutil
import unittest

import h5py
import numpy

from tests.utils import helpers

from openquake.hazard.disagg import subsets as disagg_subsets


class SubsetExtractionTestCase(unittest.TestCase):
    FULL_MATRIX_DATA = \
        'latitudeLongitudeMagnitudeEpsilonTectonicRegionTypePMF.dat'
    #                   lat lon mag eps trt
    FULL_MATRIX_SHAPE = (5,  5,  4,  4,  5)

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        full_matrix_path = os.path.join(cls.tempdir, 'full-matrix.hdf5')
        full_matrix = h5py.File(full_matrix_path, 'w')
        ds = numpy.ndarray(cls.FULL_MATRIX_SHAPE, disagg_subsets.DATA_TYPE)
        cls.read_data_file(cls.FULL_MATRIX_DATA, ds)
        full_matrix.create_dataset(disagg_subsets.FULL_MATRIX_DS_NAME, data=ds)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    @classmethod
    def read_data_file(cls, data_filename, target_dataset):
        data = open(helpers.get_data_path('DisaggSubsets/%s' % data_filename))
        numbers = (float(line.split()[-1]) for line in data)
        stack = [iter(target_dataset)]
        while stack:
            try:
                arr = next(stack[-1])
            except StopIteration:
                stack.pop()
                continue
            if len(arr.shape) == 1:
                for i in xrange(len(arr)):
                    arr[i] = next(numbers)
            else:
                stack.append(iter(arr))
        assert len(list(numbers)) == 0

    def test(self):
        pass
