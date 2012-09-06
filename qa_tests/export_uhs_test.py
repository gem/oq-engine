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


import os
import shutil
import subprocess
import tempfile
import unittest

from openquake.db import models

from qa_tests._export_test_utils import check_list_calcs
from qa_tests._export_test_utils import check_list_outputs
from tests.utils import helpers


class ExportUHSTestCase(unittest.TestCase):
    """Exercises the full end-to-end functionality for running a UHS
    calculation and exporting results from the database to files.
    """

    def test_export_uhs(self):
        # Tests the UHS calculation run and export end-to-end.
        # For the export, we only check the quantity, location, and names of
        # each exported file. We don't check the contents; that's covered in
        # other tests.
        uhs_cfg = helpers.demo_file('uhs/config.gem')
        export_target_dir = tempfile.mkdtemp()

        expected_export_files = [
            os.path.join(export_target_dir, 'uhs_poe:0.1.hdf5'),
            os.path.join(export_target_dir, 'uhs_poe:0.02.hdf5'),
            os.path.join(export_target_dir, 'uhs.xml'),
        ]

        # Sanity check and precondition: these files should not exist yet
        for f in expected_export_files:
            self.assertFalse(os.path.exists(f))

        try:
            ret_code = helpers.run_job(uhs_cfg)
            self.assertEqual(0, ret_code)

            job = models.OqJob.objects.latest('id')
            [output] = models.Output.objects.filter(
                oq_job=job.id)

            # Split into a list, 1 result for each row in the output.
            # The first row of output (the table header) is discarded.
            listed_calcs = helpers.prepare_cli_output(subprocess.check_output(
                ['openquake/bin/oqscript.py', '--list-calculations']))

            check_list_calcs(self, listed_calcs, job.id)

            listed_outputs = helpers.prepare_cli_output(
                subprocess.check_output(
                    ['openquake/bin/oqscript.py', '--list-outputs', str(job.id)]))

            check_list_outputs(self, listed_outputs, output.id, 'uh_spectra')

            listed_exports = helpers.prepare_cli_output(
                subprocess.check_output(['openquake/bin/oqscript.py', '--export',
                                         str(output.id), export_target_dir]))

            self.assertEqual(expected_export_files, listed_exports)

            # Check that the files actually have been created,
            # and also verify that the paths are absolute:
            for f in listed_exports:
                self.assertTrue(os.path.exists(f))
                self.assertTrue(os.path.isabs(f))
        finally:
            shutil.rmtree(export_target_dir)
