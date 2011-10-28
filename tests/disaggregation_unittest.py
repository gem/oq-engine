# -*- coding: utf-8 -*-
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


import h5py
import numpy
import os
import tempfile
import unittest

from nose.plugins.attrib import attr

from openquake import java
from openquake import shapes
from openquake.hazard import disaggregation as disagg
from openquake.hazard.general import store_source_model, store_gmpe_map
from openquake.input.logictree import LogicTreeProcessor

from tests.utils import helpers

DISAGG_DEMO_CONFIG_FILE = helpers.demo_file('disaggregation/config.gem')


class DisaggregationFuncsTestCase(unittest.TestCase):
    """Test for disaggregation calculator helper functions."""

    def test_list_to_jdouble_array(self):
        """Test construction of a Double[] (Java array) from a list of floats.
        """
        test_input = [0.01, 0.02, 0.03, 0.04]

        # Make the (Java) Double[] array (the input is copied as a simple way
        # to avoid false positives).
        jdouble_a = disagg.list_to_jdouble_array(list(test_input))

        # It should be a jpype Double[] type:
        self.assertEqual('java.lang.Double[]', jdouble_a.__class__.__name__)

        # Now check that the len and values are correct:
        self.assertEqual(len(test_input), len(jdouble_a))
        self.assertEqual(test_input, [x.doubleValue() for x in jdouble_a])

    def test_save_5d_matrix_to_h5(self):
        """Save a 5D matrix (as a numpy array of float64s) to a file, then read
        the file and make sure the data is save properly."""

        # 2x2x2x2x2 matrix
        data = numpy.array([
            [[[[0.0, 1.0], [2.0, 3.0]], [[4.0, 5.0], [6.0, 7.0]]],
            [[[8.0, 9.0], [10.0, 11.0]], [[12.0, 13.0], [14.0, 15.0]]]],
            [[[[16.0, 17.0], [18.0, 19.0]], [[20.0, 21.0], [22.0, 23.0]]],
            [[[24.0, 25.0], [26.0, 27.0]], [[28.0, 29.0], [30.0, 31.0]]]]
        ], numpy.float64)

        file_path = disagg.save_5d_matrix_to_h5(tempfile.tempdir, data)

        # sanity check: does the file exist?
        self.assertTrue(os.path.exists(file_path))

        # Okay, read the file and make sure the data was written properly:
        with h5py.File(file_path, 'r') as read_hdf:
            actual_data = read_hdf[disagg.FULL_DISAGG_MATRIX].value

        # the data should be the same as it was written:
        self.assertTrue((data == actual_data).all())

        # For clean up, delete the hdf5 we generated.
        os.unlink(file_path)


class DisaggregationTaskTestCase(unittest.TestCase):
    """Tests for the disaggregation matrix computation task."""

    def test_compute_disagg_matrix(self):
        """Test the core function of the main disaggregation task."""

        # for the given test input data, we expect the calculator to return
        # this gmv:
        expected_gmv = 0.225743641602613

        the_job = helpers.job_from_file(DISAGG_DEMO_CONFIG_FILE)

        # We need to store the source model and gmpe model in the KVS for this
        # test.
        lt_proc = LogicTreeProcessor(
            the_job.params['BASE_PATH'],
            the_job.params['SOURCE_MODEL_LOGIC_TREE_FILE_PATH'],
            the_job.params['GMPE_LOGIC_TREE_FILE_PATH'])

        src_model_seed = int(the_job.params.get('SOURCE_MODEL_LT_RANDOM_SEED'))
        gmpe_seed = int(the_job.params.get('GMPE_LT_RANDOM_SEED'))

        store_source_model(the_job.job_id, src_model_seed, the_job.params,
                           lt_proc)
        store_gmpe_map(the_job.job_id, gmpe_seed, lt_proc)

        site = shapes.Site(0.0, 0.0)
        poe = 0.1
        result_dir = tempfile.tempdir

        gmv, matrix_path = disagg.compute_disagg_matrix(
            the_job.job_id, site, poe, result_dir)

        # Now test the following:
        # 1) The matrix file exists
        # 2) The matrix file has a size > 0
        # 3) Check that the returned GMV is what we expect
        # Here we don't test the actual matrix contents or the hdf5 file;
        # there are tests on the Java side with verify the actual data in the
        # matrix, plus other tests on the Python side which deal with saving
        # the matrix.
        self.assertTrue(os.path.exists(matrix_path))
        self.assertTrue(os.path.getsize(matrix_path) > 0)
        self.assertEqual(expected_gmv, gmv)

        # For clean up, delete the hdf5 we generated.
        os.unlink(matrix_path)
