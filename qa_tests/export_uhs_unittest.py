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
        ]

        try:
            ret_code = helpers.run_job(uhs_cfg)
            self.assertEqual(0, ret_code)

            calculation = models.OqCalculation.objects.latest('id')
            [output] = models.Output.objects.filter(
                oq_calculation=calculation.id)

            # Split into a list, 1 result for each row in the output.
            # The first row of output (the table header) is discarded.
            listed_calcs = helpers.prepare_cli_output(subprocess.check_output(
                ['bin/openquake', '--list-calculations']))

            check_list_calcs(self, listed_calcs, calculation.id)

            listed_outputs = helpers.prepare_cli_output(
                subprocess.check_output(['bin/openquake', '--list-outputs',
                                         str(calculation.id)]))

            check_list_outputs(self, listed_outputs, output.id, 'uh_spectra')

            listed_exports = helpers.prepare_cli_output(
                subprocess.check_output(['bin/openquake', '--export',
                                         str(output.id), export_target_dir]))

            self.assertEqual(expected_export_files, listed_exports)
        finally:
            shutil.rmtree(export_target_dir)
