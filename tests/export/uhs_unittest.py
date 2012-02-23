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
import tempfile
import unittest

from django.contrib.gis.geos.point import Point

from openquake.export import uhs as uhs_export


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

        poe = 0.02
        ds_names = [
            'lon:0.0-lat:0.0',
            'lon:1.0-lat:0.0',
            'lon:0.0-lat:1.0',
            'lon:1.0-lat:1.0',
        ]
        n_rlz = 3
        n_periods = 4

        expected_matrix = numpy.zeros((n_rlz, n_periods), dtype=numpy.float64)

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
                self.assertEqual(expected_matrix.dtype, actual_matrix.dtype)
                self.assertTrue((expected_matrix == actual_matrix).all())
