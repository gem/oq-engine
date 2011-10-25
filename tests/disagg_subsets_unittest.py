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

    LATITUDE_BIN_LIMITS = [-0.6, -0.3, -0.1, 0.1, 0.3, 0.6]
    LONGITUDE_BIN_LIMITS = LATITUDE_BIN_LIMITS
    DISTANCE_BIN_LIMITS = [0.0, 20.0, 40.0, 60.0]
    MAGNITUDE_BIN_LIMITS = [5.0, 6.0, 7.0, 8.0, 9.0]
    EPSILON_BIN_LIMITS = [-0.5, +0.5, +1.5, +2.5, +3.5]

    NDIST = len(DISTANCE_BIN_LIMITS)
    NLAT = len(LATITUDE_BIN_LIMITS)
    NLON = len(LONGITUDE_BIN_LIMITS)
    NMAG = len(MAGNITUDE_BIN_LIMITS)
    NEPS = len(EPSILON_BIN_LIMITS)
    NTRT = 5
    FULL_MATRIX_SHAPE = (NLAT, NLON, NMAG, NEPS, NTRT)

    SITE = (0.0, 0.0)

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.full_matrix_path = os.path.join(cls.tempdir, 'full-matrix.hdf5')
        full_matrix = h5py.File(cls.full_matrix_path, 'w')
        ds = numpy.ndarray([cls.NLAT - 1, cls.NLON - 1, cls.NMAG - 1,
                            cls.NEPS - 1, cls.NTRT],
                           disagg_subsets.DATA_TYPE)
        cls.read_data_file(cls.FULL_MATRIX_DATA, ds)
        full_matrix.create_dataset(disagg_subsets.FULL_MATRIX_DS_NAME, data=ds)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    @classmethod
    def read_data_file(cls, data_filename, target_dataset):
        data = open(helpers.get_data_path('disagg/result/%s' % data_filename))
        numbers = (float(line.split()[-1]) for line in data)
        if len(target_dataset.shape) == 1:
            for i, number in enumerate(numbers):
                target_dataset[i] = number
            return
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

    def _test_pmf(self, name, datafile, result_shape):
        target_path = os.path.join(self.tempdir, '%s.hdf5' % name)
        disagg_subsets.extract_subsets(
            self.SITE, self.full_matrix_path,
            self.LATITUDE_BIN_LIMITS, self.LONGITUDE_BIN_LIMITS,
            self.MAGNITUDE_BIN_LIMITS, self.EPSILON_BIN_LIMITS,
            self.DISTANCE_BIN_LIMITS,
            target_path, [name]
        )
        expected_result = numpy.ndarray(result_shape)
        self.read_data_file(datafile, expected_result)
        result = h5py.File(target_path, 'r')[name].value
        helpers.assertDeepAlmostEqual(self, expected_result, result)

    def test_magpmf(self):
        self._test_pmf('magpmf', 'magnitudePMF.dat', [self.NMAG - 1])

    def test_distpmf(self):
        self._test_pmf('distpmf', 'distancePMF.dat', [self.NDIST - 1])

    def test_trtpmf(self):
        self._test_pmf('trtpmf', 'tectonicRegionTypePMF.dat', [self.NTRT])

    def test_magdistpmf(self):
        self._test_pmf('magdistpmf', 'magnitudeDistancePMF.dat',
                       [self.NMAG - 1, self.NDIST - 1])

    def test_magdistepspmf(self):
        self._test_pmf('magdistepspmf', 'magnitudeDistanceEpsilonPMF.dat',
                       [self.NMAG - 1, self.NDIST - 1, self.NEPS - 1])

    def test_latlonpmf(self):
        self._test_pmf('latlonpmf', 'latitudeLongitudePMF.dat',
                       [self.NLAT - 1, self.NLON - 1])

    def test_latlonmagpmf(self):
        self._test_pmf('latlonmagpmf', 'latitudeLongitudeMagnitudePMF.dat',
                       [self.NLAT - 1, self.NLON - 1, self.NMAG - 1])

    def test_latlonmagepspmf(self):
        self._test_pmf('latlonmagepspmf',
                       'latitudeLongitudeMagnitudeEpsilonPMF.dat',
                       [self.NLAT - 1, self.NLON - 1,
                        self.NMAG - 1, self.NEPS - 1])

    def test_magtrtpmf(self):
        self._test_pmf('magtrtpmf', 'magnitudeTectonicRegionTypePMF.dat',
                       [self.NMAG - 1, self.NTRT])

    def test_latlontrtpmf(self):
        self._test_pmf('latlontrtpmf',
                       'latitudeLongitudeTectonicRegionTypePMF.dat',
                       [self.NLAT - 1, self.NLON - 1, self.NTRT])

    def test_full_matrix(self):
        self._test_pmf(disagg_subsets.FULL_MATRIX_DS_NAME,
                       self.FULL_MATRIX_DATA,
                       [self.NLAT - 1, self.NLON - 1, self.NMAG - 1,
                        self.NEPS - 1, self.NTRT])

    def test_multiple_matrices(self):
        target_path = os.path.join(self.tempdir, 'multiple.hdf5')
        pmfs = {
            'magdistepspmf': ('magnitudeDistanceEpsilonPMF.dat',
                              [self.NMAG - 1, self.NDIST - 1, self.NEPS - 1]),
            'latlonpmf': ('latitudeLongitudePMF.dat',
                          [self.NLAT - 1, self.NLON - 1]),
            disagg_subsets.FULL_MATRIX_DS_NAME: (
                self.FULL_MATRIX_DATA,
                [self.NLAT - 1, self.NLON - 1, self.NMAG - 1,
                 self.NEPS - 1, self.NTRT]
            )
        }
        disagg_subsets.extract_subsets(
            self.SITE, self.full_matrix_path,
            self.LATITUDE_BIN_LIMITS, self.LONGITUDE_BIN_LIMITS,
            self.MAGNITUDE_BIN_LIMITS, self.EPSILON_BIN_LIMITS,
            self.DISTANCE_BIN_LIMITS,
            target_path,
            pmfs.keys()
        )
        result = h5py.File(target_path, 'r')
        for name, (datafile, shape) in pmfs.items():
            expected_result = numpy.ndarray(shape)
            self.read_data_file(datafile, expected_result)
            helpers.assertDeepAlmostEqual(self, expected_result, result[name])
