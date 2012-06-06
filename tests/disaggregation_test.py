# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import h5py
import numpy
import os
import tempfile
import unittest

from openquake import shapes
from openquake.calculators.hazard.disagg import FULL_DISAGG_MATRIX
from openquake.calculators.hazard.disagg import core as disagg_core

from tests.utils import helpers

DISAGG_DEMO_CONFIG_FILE = helpers.demo_file('disaggregation/config.gem')


class DisaggregationFuncsTestCase(unittest.TestCase):
    """Test for disaggregation calculator helper functions."""

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

        file_path = disagg_core.save_5d_matrix_to_h5(
            tempfile.gettempdir(), data)

        # sanity check: does the file exist?
        self.assertTrue(os.path.exists(file_path))

        # Okay, read the file and make sure the data was written properly:
        with h5py.File(file_path, 'r') as read_hdf:
            actual_data = read_hdf[FULL_DISAGG_MATRIX].value

        # the data should be the same as it was written:
        self.assertTrue((data == actual_data).all())

        # For clean up, delete the hdf5 we generated.
        os.unlink(file_path)


class DisaggregationTaskTestCase(unittest.TestCase):
    """Tests for the disaggregation matrix computation task."""

    def test_compute_disagg_matrix(self):
        # Test the core function of the main disaggregation task.

        # for the given test input data, we expect the calculator to return
        # this gmv:
        expected_gmv = 0.2259803374787534

        the_job = helpers.job_from_file(DISAGG_DEMO_CONFIG_FILE)

        helpers.store_hazard_logic_trees(the_job)

        site = shapes.Site(0.0, 0.0)
        poe = 0.1
        result_dir = tempfile.gettempdir()

        gmv, matrix_path = disagg_core.compute_disagg_matrix(
            the_job, site, poe, result_dir)

        # Now test the following:
        # 1) The matrix file exists
        # 2) The matrix file has a size > 0
        # 3) Check that the returned GMV is what we expect
        # Here we don't test the actual matrix contents or the hdf5 file;
        # there are tests on the Java side which verify the actual data in
        # the matrix, plus other tests on the Python side which deal with
        # saving the matrix.
        self.assertTrue(os.path.exists(matrix_path))
        self.assertTrue(os.path.getsize(matrix_path) > 0)
        self.assertEqual(expected_gmv, gmv)

        # For clean up, delete the hdf5 we generated.
        os.unlink(matrix_path)

    def test_compute_disagg_matrix_calls_site_model_fns(self):
        # Test that `compute_disagg_matrix` calls the required site model
        # functions when the configuration defines a site model.
        cfg = helpers.demo_file('disaggregation/config_with_site_model.gem')

        the_job = helpers.prepare_job_context(cfg)
        the_job.to_kvs()
        calc = disagg_core.DisaggHazardCalculator(the_job)
        calc.initialize()  # store the site model

        helpers.store_hazard_logic_trees(the_job)

        site = shapes.Site(0.0, 0.0)
        poe = 0.1
        result_dir = tempfile.gettempdir()

        get_sm_patch = helpers.patch(
            'openquake.calculators.hazard.general.get_site_model')
        get_closest_patch = helpers.patch(
            'openquake.calculators.hazard.general.get_closest_site_model_data')
        compute_patch = helpers.patch(
            'openquake.calculators.hazard.disagg.core._compute_matrix')
        save_patch = helpers.patch(
            'openquake.calculators.hazard.disagg.core.save_5d_matrix_to_h5')

        get_sm_mock = get_sm_patch.start()
        get_closest_mock = get_closest_patch.start()
        compute_mock = compute_patch.start()
        save_mock = save_patch.start()

        try:
            _, _ = disagg_core.compute_disagg_matrix(the_job, site, poe,
                                                     result_dir)

            self.assertEqual(1, get_sm_mock.call_count)
            self.assertEqual(1, get_closest_mock.call_count)
            self.assertEqual(1, compute_mock.call_count)
            self.assertEqual(1, save_mock.call_count)
        finally:
            get_sm_patch.stop()
            get_closest_patch.stop()
            compute_patch.stop()
            save_patch.stop()


class DisaggHazardCalculatorTestCase(unittest.TestCase):
    """Test for the
    :class:`openquake.hazard.disagg.core.DisaggHazardCalculator`.
    """

    def test_create_result_dir(self):
        """Test creation of the result_dir, the path for which is constructed
        from a the nfs base_dir (defined in the openquake.cfg) and the job id.
        """
        base_path = tempfile.gettempdir()
        job_id = 1234

        expected_dir = os.path.join(
            tempfile.gettempdir(), 'disagg-results', 'job-%s' % job_id)

        result_dir = disagg_core.DisaggHazardCalculator.create_result_dir(
            base_path, job_id)

        self.assertEqual(expected_dir, result_dir)
        self.assertTrue(os.path.exists(result_dir))
        self.assertTrue(os.path.isdir(result_dir))

        # clean up: delete the result_dir containing the job info
        os.rmdir(result_dir)

    def test_create_result_dir_already_exists(self):
        # Test create_result_dir when the target directory already exists.
        tmp_dir = tempfile.mkdtemp()
        job_id = 1234

        expected_dir = os.path.join(tmp_dir, 'disagg-results',
                                    'job-%s' % job_id)
        os.makedirs(expected_dir)

        result_dir = disagg_core.DisaggHazardCalculator.create_result_dir(
            tmp_dir, job_id)

        self.assertEqual(expected_dir, result_dir)
        self.assertTrue(os.path.exists(result_dir))
        self.assertTrue(os.path.isdir(result_dir))

    def test_create_result_dir_already_exists_as_file(self):
        # Test create_result_dir when a file exists where we're attempting to
        # create a directory.
        tmp_dir = tempfile.mkdtemp()
        job_id = 1234

        file_path = os.path.join(tmp_dir, 'disagg-results', 'job-%s' % job_id)

        # 'touch' the file
        os.makedirs(os.path.dirname(file_path))
        open(file_path, 'w').close()

        self.assertRaises(
            OSError, disagg_core.DisaggHazardCalculator.create_result_dir,
            tmp_dir, job_id)
