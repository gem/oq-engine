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


class ExportAggLossCurvesTestCase(unittest.TestCase):
    """Exercises the full end-to-end functionality for running an Event-Based
    Risk calculation and exporting Aggregate Loss curve results from the
    database to file."""

    def test_export_agg_loss_curve(self):
        eb_cfg = helpers.get_data_path(
            'demos/event_based_risk_small/config.gem')
        export_target_dir = tempfile.mkdtemp()

        expected_export_files = [
            os.path.join(export_target_dir, 'aggregate_loss_curve.xml'),
        ]

        try:
            ret_code = helpers.run_job(eb_cfg)
            self.assertEqual(0, ret_code)

            calculation = models.OqJob.objects.latest('id')
            [output] = models.Output.objects.filter(
                oq_job=calculation.id, output_type='agg_loss_curve')

            listed_calcs = helpers.prepare_cli_output(subprocess.check_output(
                ['bin/openquake', '--list-calculations']))

            check_list_calcs(self, listed_calcs, calculation.id)

            listed_outputs = helpers.prepare_cli_output(
                subprocess.check_output(
                    ['bin/openquake', '--list-outputs', str(calculation.id)]))

            check_list_outputs(self, listed_outputs, output.id,
                               'agg_loss_curve')

            listed_exports = helpers.prepare_cli_output(
                subprocess.check_output([
                    'bin/openquake', '--export', str(output.id),
                    export_target_dir]))

            self.assertEqual(expected_export_files, listed_exports)
        finally:
            shutil.rmtree(export_target_dir)
