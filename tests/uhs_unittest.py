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
import shutil
import tempfile
import unittest

from openquake import java
from openquake.shapes import Site
from openquake.utils import list_to_jdouble_array
from openquake.hazard.uhs.core import touch_result_file, write_uhs_results

from tests.utils.helpers import patch


class UHSCoreTestCase(unittest.TestCase):
    """Tests for core UHS tasks and other functions."""

    def test_touch_result_file(self):
        """Call the :function:`openquake.hazard.uhs.core.touch_result_file` and
        verify that the result file is properly created with the correct number
        of datasets.

        We also want to verify the name (since it is associated with a specific
        site of interest) as well as the size and datatype of each dataset.
        """
        _, path = tempfile.mkstemp()

        fake_job_id = 1  # The job_id doesn't matter in this test.
        sites = [Site(-122.000, 38.113), Site(-122.114, 38.113)]
        n_samples = 4
        n_periods = 3

        with patch('openquake.utils.tasks.check_job_status') as cjs:
            print dir(cjs)
            touch_result_file(fake_job_id, path, sites, n_samples, n_periods)

        # Does the resulting file exist?
        self.assertTrue(os.path.exists(path))

        # Read the file and check the names, sizes, and datatypes of each
        # dataset.
        with h5py.File(path, 'r') as h5_file:
            # There should be exactly 2 datasets.
            self.assertEquals(2, len(h5_file))

            for site in sites:
                ds_name = 'lon:%s-lat:%s' % (site.longitude, site.latitude)
                ds = h5_file.get(ds_name)
                self.assertIsNotNone(ds)
                self.assertEquals(numpy.float64, ds.dtype)
                self.assertEquals((n_samples, n_periods), ds.shape)

        # Clean up the test file.
        os.unlink(path)

    def test_write_uhs_results(self):
        """Given some mocked up UHS calc results, write them to some temporary
        HDF5 files. We need to verify that the result file paths are correct,
        as well as the contents.

        The results should be written to separate directories (depending on the
        PoE)."""
        uhs_result_data = [
            (0.1, [0.2774217067746703,
                   0.32675005743942004,
                   0.05309858927852786]),
            (0.02, [0.5667404129191248,
                    0.6185688023781438,
                    0.11843417899553109])]

        uhs_results = []  # The results we want to write to HDF5
        uhs_result = java.jvm().JClass('org.gem.calc.UHSResult')

        for poe, uhs in uhs_result_data:
            uhs_results.append(uhs_result(poe, list_to_jdouble_array(uhs)))

        result_dir = tempfile.mkdtemp()

        result_files = write_uhs_results(result_dir, uhs_results)

        for i, res_file in enumerate(result_files):
            self.assertTrue(os.path.exists(res_file))

            expected_dir = os.path.join(result_dir,
                                        'poe:%s' % uhs_result_data[i][0])
            self.assertEquals(expected_dir, os.path.split(res_file)[0])

            with h5py.File(res_file, 'r') as h5_file:
                self.assertTrue(numpy.allclose(uhs_result_data[i][1],
                                               h5_file['uhs'].value))

        shutil.rmtree(result_dir)
