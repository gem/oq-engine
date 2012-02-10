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

from openquake import java
from openquake.java import list_to_jdouble_array
from openquake.shapes import Site
from openquake.calculators.hazard.uhs.core import compute_uhs
from openquake.calculators.hazard.uhs.core import touch_result_file
from openquake.calculators.hazard.uhs.core import write_uhs_results

from tests.utils import helpers


UHS_DEMO_CONFIG_FILE = helpers.demo_file('uhs/config.gem')


class UHSCoreTestCase(unittest.TestCase):
    """Tests for core UHS tasks and other functions."""

    # Sample UHS result data
    UHS_RESULTS = [
        (0.1, [0.2774217067746703,
               0.32675005743942004,
               0.05309858927852786]),
        (0.02, [0.5667404129191248,
                0.6185688023781438,
                0.11843417899553109])]

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

        with helpers.patch('openquake.utils.tasks.get_running_calculation'):
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

    def test_compute_uhs(self):
        """Test the :function:`openquake.hazard.uhs.core.compute_uhs`
        function. This function makes use of the Java `UHSCalculator` and
        performs the main UHS computation.

        The results of the computation are a sequence of Java `UHSResult`
        objects."""
        the_job = helpers.job_from_file(UHS_DEMO_CONFIG_FILE)

        site = Site(0.0, 0.0)

        helpers.store_hazard_logic_trees(the_job)

        uhs_results = compute_uhs(the_job, site)

        for i, result in enumerate(uhs_results):
            poe = result.getPoe()
            uhs = result.getUhs()

            self.assertEquals(self.UHS_RESULTS[i][0], poe)
            self.assertTrue(numpy.allclose(self.UHS_RESULTS[i][1],
                                           [x.value for x in uhs]))

    def test_write_uhs_results(self):
        """Given some mocked up UHS calc results, write them to some temporary
        HDF5 files. We need to verify that the result file paths are correct,
        as well as the contents.

        The results should be written to separate directories (depending on the
        PoE)."""
        # Both result files should have the same file name,
        # just a different directory location.
        expected_file_name = 'sample:1-lon:0.0-lat:0.0.h5'

        uhs_results = []  # The results we want to write to HDF5
        uhs_result = java.jvm().JClass('org.gem.calc.UHSResult')

        for poe, uhs in self.UHS_RESULTS:
            uhs_results.append(uhs_result(poe, list_to_jdouble_array(uhs)))

        result_dir = tempfile.mkdtemp()

        result_files = write_uhs_results(result_dir, 1, Site(0.0, 0.0),
                                         uhs_results)

        for i, res_file in enumerate(result_files):
            print res_file
            self.assertTrue(os.path.exists(res_file))

            expected_dir = os.path.join(result_dir,
                                        'poe:%s' % self.UHS_RESULTS[i][0])
            actual_dir, actual_file_name = os.path.split(res_file)
            self.assertEquals(expected_dir, actual_dir)
            self.assertEquals(expected_file_name, actual_file_name)

            with h5py.File(res_file, 'r') as h5_file:
                self.assertTrue(numpy.allclose(self.UHS_RESULTS[i][1],
                                               h5_file['uhs'].value))

        shutil.rmtree(result_dir)
