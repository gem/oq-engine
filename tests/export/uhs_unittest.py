# Copyright (c) 2010-2012, GEM Foundation.
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


import h5py
import numpy
import os
import shutil
import tempfile
import unittest

from collections import namedtuple

from django.contrib.gis.geos.point import Point

from openquake.export import uhs as uhs_export

from tests.utils import helpers


class UHSExportTestCase(unittest.TestCase):

    def test__point_to_ds_name(self):
        test_input = [
            Point(1.0, 2.0),
            Point(179.1234567, -79.1234567),
            Point(-179.12345675, 79.12345674),
        ]

        # Note the function under test uses round_float(), so we expected the
        # resulting lat/lon values to be rounded to 7 digits after the decimal
        # point.
        # See function `openquake.utils.round_float`.
        expected = [
            'lon:1.0-lat:2.0',
            'lon:179.1234567-lat:-79.1234567',
            'lon:-179.1234568-lat:79.1234567',
        ]

        actual = [uhs_export._point_to_ds_name(t) for t in test_input]

        self.assertEqual(expected, actual)

    def test_touch_result_hdf5_file(self):
        target_dir = tempfile.mkdtemp()

        try:
            poe = 0.02
            ds_names = [
                'lon:0.0-lat:0.0',
                'lon:1.0-lat:0.0',
                'lon:0.0-lat:1.0',
                'lon:1.0-lat:1.0',
            ]
            n_rlz = 3
            n_periods = 4

            # Each dataset should be created empty (all zeros)
            expected_matrix = numpy.zeros((n_rlz, n_periods),
                                          dtype=numpy.float64)

            path = uhs_export.touch_result_hdf5_file(
                target_dir, poe, ds_names, n_rlz, n_periods)

            directory, file_name = os.path.split(path)

            self.assertEqual(target_dir, directory)
            self.assertEqual('uhs_poe:0.02.hdf5', file_name)

            with h5py.File(path, 'r') as h5_file:

                # Verify the quanity and name of the datatsets:
                self.assertEqual(set(ds_names), set(h5_file.keys()))

                for ds in ds_names:
                    actual_matrix = h5_file[ds].value
                    self.assertEqual(expected_matrix.dtype,
                                     actual_matrix.dtype)
                    self.assertTrue((expected_matrix == actual_matrix).all())

        finally:
            shutil.rmtree(target_dir)

    def test_write_uhs_data(self):
        # Test object type to use instead of `UhSpectrumData`;
        # this is a little more light-weight

        # First, set up all the test data:
        Data = namedtuple('Data', 'realization, sa_values, location')

        points = [
            Point(0.0, 0.0),
            Point(1.0, 0.0),
            Point(0.0, 1.0),
            Point(1.0, 1.0),
        ]

        # A single 2D matrix for each location/point
        sa_test_values = [
            # each row repsents a realization,
            # while the contents of each row is an array of SA values
            [[1.0, 2.0, 3.0, 4.0],
             [5.0, 6.0, 7.0, 8.0],
             [9.0, 10.0, 11.0, 12.0]],

            [[13.0, 14.0, 15.0, 16.0],
             [17.0, 18.0, 19.0, 20.0],
             [21.0, 22.0, 23.0, 24.0]],

            [[25.0, 26.0, 27.0, 28.0],
             [29.0, 30.0, 31.0, 32.0],
             [33.0, 34.0, 35.0, 36.0]],

            [[37.0, 38.0, 39.0, 40.0],
             [41.0, 42.0, 43.0, 44.0],
             [45.0, 46.0, 47.0, 48.0]],
        ]

        uhs_data = []
        for i, pt in enumerate(points):
            for j, sa_values in enumerate(sa_test_values[i]):
                uhs_data.append(Data(j, sa_values, pt))

        # Done setting up the test data.

        # Now, create the empty file:
        target_dir = tempfile.mkdtemp()

        try:

            poe = 0.05
            n_rlz = 3  # rows
            n_periods = 4  # columns
            ds_names = [uhs_export._point_to_ds_name(p) for p in points]

            # As a robustness test, reverse the order of the ds_names.
            # It should not matter when we're creating the file (since the
            # structure of the file is basically a dict of 2D matrices).
            the_file = uhs_export.touch_result_hdf5_file(
                target_dir, poe, ds_names[::-1], n_rlz, n_periods)

            # Finally, call the function under test with our list of fake
            # `UhSpectrumData` objects.
            uhs_export.write_uhs_data(the_file, uhs_data)

            # Now read the file and check the contents:
            with h5py.File(the_file, 'r') as h5_file:
                for i, ds in enumerate(ds_names):
                    helpers.assertDeepAlmostEqual(
                        self, sa_test_values[i], h5_file[ds].value)
        finally:
            shutil.rmtree(target_dir)
