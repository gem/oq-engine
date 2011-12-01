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

from openquake.shapes import Site
from openquake.hazard.uhs.core import touch_result_file


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
        sites = [Site(-122.000, 38.113), Site(-122.114, 38.113)]
        n_samples = 4
        n_periods = 3

        touch_result_file(path, sites, n_samples, n_periods)

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
