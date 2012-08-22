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

from nose.plugins.attrib import attr

from openquake.db import models
from openquake.export import core as export_core
from openquake.export import hazard

from tests.utils import helpers


class HazardCurveExportTestCase(unittest.TestCase):

    @attr('slow')
    def test_export_hazard_curves(self):
        # Run a hazard calculation to compute some curves
        # Call the exporter and verify that files were created
        # Since the hazard curve XML writer is concerned with correctly
        # generating XML, we won't test that here.
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
            calc_args = ['bin/openquake', '--run-hazard', cfg]

            # run the calculation to create something to export
            with open(os.devnull, 'wb') as silence:
                retcode = subprocess.check_call(
                    calc_args, stdout=silence, stderr=silence)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            expected_outputs = 6
            self.assertEqual(expected_outputs, len(outputs))

            # Just to be thorough, let's make sure we can export everything:
            exported_files = []
            for o in outputs:
                files = hazard.export(o.id, target_dir)
                exported_files.extend(files)

            self.assertEqual(expected_outputs, len(exported_files))
            for f in exported_files:
                self.assertTrue(os.path.exists(f))
                self.assertTrue(os.path.isabs(f))
                self.assertTrue(os.path.getsize(f) > 0)
        finally:
            shutil.rmtree(target_dir)
