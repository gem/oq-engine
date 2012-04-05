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

            job = models.OqJob.objects.latest('id')
            [output] = models.Output.objects.filter(
                oq_job=job.id, output_type='agg_loss_curve')

            listed_calcs = helpers.prepare_cli_output(subprocess.check_output(
                ['bin/openquake', '--list-calculations']))

            check_list_calcs(self, listed_calcs, job.id)

            listed_outputs = helpers.prepare_cli_output(
                subprocess.check_output(
                    ['bin/openquake', '--list-outputs', str(job.id)]))

            check_list_outputs(self, listed_outputs, output.id,
                               'agg_loss_curve')

            listed_exports = helpers.prepare_cli_output(
                subprocess.check_output([
                    'bin/openquake', '--export', str(output.id),
                    export_target_dir]))

            self.assertEqual(expected_export_files, listed_exports)
        finally:
            shutil.rmtree(export_target_dir)


class ExportDmgDistPerAssetTestCase(unittest.TestCase):
    """
    Exercises the full end-to-end functionality for running a
    Scenario Damage Assessment calculation and exporting the
    resulting damage distribution per asset.
    """

    def test_export_dmg_dist_per_asset(self):
        cfg = helpers.demo_file("scenario_damage_risk/config.gem")
        export_target_dir = tempfile.mkdtemp()

        try:
            ret_code = helpers.run_job(cfg)
            self.assertEqual(0, ret_code)

            job = models.OqJob.objects.latest("id")
            expected_file = os.path.join(export_target_dir,
                    "dmg-dist-asset-%s.xml" % job.id)

            [output] = models.Output.objects.filter(
                oq_job=job.id, output_type="dmg_dist_per_asset")

            calcs = helpers.prepare_cli_output(subprocess.check_output(
                ["bin/openquake", "--list-calculations"]))

            # we have the calculation...
            check_list_calcs(self, calcs, job.id)

            outputs = helpers.prepare_cli_output(
                subprocess.check_output(["bin/openquake", "--list-outputs",
                str(job.id)]))

            # and the damage distribution per asset as output...
            check_list_outputs(self, outputs, output.id, "dmg_dist_per_asset")

            exports = helpers.prepare_cli_output(
                subprocess.check_output(["bin/openquake", "--export",
                str(output.id), export_target_dir]))

            # and also the exported file
            self.assertEqual([expected_file], exports)
        finally:
            shutil.rmtree(export_target_dir)
