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

from tests.utils import helpers


def _prepare_cli_output(raw_output, discard_header=True):
    """Given a huge string of output from a `subprocess.check_output` call,
    split on newlines, strip, and discard empty lines.

    If ``discard_header`` is `True`, drop the first row in the output.

    Returns a `list` of strings, 1 for each row in the CLI output.
    """
    lines = raw_output.split('\n')
    # strip and drop empty lines
    lines = [x.strip() for x in lines if len(x.strip()) > 0]

    if discard_header:
        lines.pop(0)

    return lines


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
            listed_calcs = _prepare_cli_output(subprocess.check_output(
                ['bin/openquake', '--list-calculations']))

            for c in listed_calcs:
                # We get back:
                # calc_id <tab> status <tag> description
                # description is optional so we cannot always assume it will be
                # present.
                calc_id, status = c.split('\t')[:2]
                if int(calc_id) == calculation.id:
                    self.assertEqual('succeeded', status)
                    break
            else:
                # We didn't find the calculation we just ran in the
                # --list-calculations output.
                self.fail('`openquake --list-calculations` did not print the'
                          ' expected calculation with id %s' % calculation.id)

            listed_outputs = _prepare_cli_output(subprocess.check_output(
                ['bin/openquake', '--list-outputs',
                 str(calculation.id)]))

            for o in listed_outputs:
                output_id, output_type = o.split('\t')
                if int(output_id) == output.id:
                    self.assertEqual('uh_spectra', output_type)
                    break
            else:
                # We didn't find the output we expected with --list-outputs.
                self.fail('`openquake --list-outputs` CALCULATION_ID did not'
                          ' print the expected output with id %s' % output.id)

            listed_exports = _prepare_cli_output(subprocess.check_output(
                ['bin/openquake', '--export', str(output.id),
                 export_target_dir]))

            self.assertEqual(expected_export_files, listed_exports)
        finally:
            shutil.rmtree(export_target_dir)
