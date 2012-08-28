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
            retcode = helpers.run_hazard_job(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            self.assertEqual(4, len(outputs))

            # Just to be thorough, let's make sure we can export everything:
            exported_files = []
            for o in outputs:
                files = hazard.export(o.id, target_dir)
                exported_files.extend(files)

            self.assertEqual(4, len(exported_files))
            for f in exported_files:
                self.assertTrue(os.path.exists(f))
                self.assertTrue(os.path.isabs(f))
                self.assertTrue(os.path.getsize(f) > 0)
        finally:
            shutil.rmtree(target_dir)


class EventBasedGMFExportTestCase(unittest.TestCase):

    @attr('slow')
    def test_export_ses_and_gmf(self):
        # Run an event-based hazard calculation to compute SESs and GMFs
        # Call the exporters for both SES and GMF results  and verify that
        # files were created
        # Since the XML writers (in `nrml.writers`) are concerned with
        # correctly generating the XML, we don't test that here...
        # but we should still have an end-to-end QA test.
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('event_based_hazard/job.ini')
            calc_args = ['bin/openquake', '--run-hazard', cfg]

            # run the calculation to create something to export
            retcode = helpers.run_hazard_job(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            # 2 GMFs, 2 SESs, and 1 complete logic tree SES
            self.assertEqual(5, len(outputs))

            #######
            # SESs:
            ses_outputs = outputs.filter(output_type='ses')
            self.assertEqual(2, len(ses_outputs))

            exported_files = []
            for ses_output in ses_outputs:
                files = hazard.export(ses_output.id, target_dir)
                exported_files.extend(files)

            self.assertEqual(2, len(exported_files))

            for f in exported_files:
                self.assertTrue(os.path.exists(f))
                self.assertTrue(os.path.isabs(f))
                self.assertTrue(os.path.getsize(f) > 0)

            ##################
            # Complete LT SES:
            # TODO:
            [complete_lt_ses] = outputs.filter(output_type='complete_lt_ses')

            [exported_file] = hazard.export(complete_lt_ses.id, target_dir)

            self.assertTrue(os.path.exists(exported_file))
            self.assertTrue(os.path.isabs(exported_file))
            self.assertTrue(os.path.getsize(exported_file) > 0)

            #######
            # GMFs:
            gmf_outputs = outputs.filter(output_type='gmf')
            self.assertEqual(2, len(gmf_outputs))

            exported_files = []
            for gmf_output in gmf_outputs:
                files = hazard.export(gmf_output.id, target_dir)
                exported_files.extend(files)

            self.assertEqual(2, len(exported_files))
            # Check the file paths exist, are absolute, and the files aren't
            # empty.
            for f in exported_files:
                self.assertTrue(os.path.exists(f))
                self.assertTrue(os.path.isabs(f))
                self.assertTrue(os.path.getsize(f) > 0)
        finally:
            shutil.rmtree(target_dir)
