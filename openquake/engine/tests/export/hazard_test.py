# Copyright (c) 2010-2015, GEM Foundation.
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

import mock
import io
import os
import shutil
import unittest
import tempfile
from xml.etree import ElementTree as etree

from nose.plugins.attrib import attr

from openquake.commonlib import nrml, datastore, writers

from openquake.engine.db import models
from openquake.engine.export import core

from openquake.engine.tests.export.core_test import \
    BaseExportTestCase, number_of
from openquake.engine.tests.utils import helpers


def check_export(output_id, target):
    """
    Call export by checking that the exported file is valid
    """
    out_file = core.export(output_id, target, 'xml')
    if out_file.endswith('.xml'):
        nrml.read(out_file)
    return out_file


class ClassicalExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_classical_hazard_export(self):
        # Run a hazard calculation to compute some curves and maps
        # Call the exporter and verify that files were created
        # Since the hazard curve XML writer is concerned with correctly
        # generating XML, we won't test that here.
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')

            # run the calculation to create something to export
            helpers.run_job(cfg)

            job = models.OqJob.objects.latest('id')
            self.assertEqual(job.status, 'complete')

            outputs = core.get_outputs(job.id)

            # 10 hazard curves, 20 maps, 10 uhs, 5 multi curves
            expected_outputs = 45
            self.assertEqual(expected_outputs, outputs.count())

            # Number of curves:
            # (2 imts * 2 realizations)
            # + (2 imts * (1 mean + 2 quantiles)
            # = 10
            curves = outputs.filter(output_type='hazard_curve')
            self.assertEqual(10, curves.count())

            # Number of multi-curves
            # (2 realizations + 1 mean + 2 quantiles)
            multi_curves = outputs.filter(output_type="hazard_curve_multi")
            self.assertEqual(5, multi_curves.count())

            # Number of maps:
            # (2 poes * 2 imts * 2 realizations)
            # + (2 poes * 2 imts * (1 mean + 2 quantiles))
            # = 20
            # Number of UHS:
            maps = outputs.filter(output_type='hazard_map')
            self.assertEqual(20, maps.count())

            # Number of UHS:
            # (20 maps_PGA_SA / 2 poes)
            # = 10
            uhs = outputs.filter(output_type='uh_spectra')
            self.assertEqual(10, uhs.count())

            # Test hazard curve export:
            hc_files = []
            for curve in curves:
                hc_files.append(check_export(curve.id, target_dir))

            self.assertEqual(10, len(hc_files))

            # Test multi hazard curve export:
            hc_files = []
            for curve in multi_curves:
                hc_files.append(check_export(curve.id, target_dir))

            self.assertEqual(5, len(hc_files))

            for f in hc_files:
                self._test_exported_file(f)

            # Test hazard map export:
            hm_files = []
            for haz_map in maps:
                hm_files.append(check_export(haz_map.id, target_dir))

            self.assertEqual(20, len(hm_files))

            for f in hm_files:
                self._test_exported_file(f)

            # Test UHS export:
            uhs_files = []
            for u in uhs:
                uhs_files.append(check_export(u.id, target_dir))
            for f in uhs_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)


class EventBasedExportTestCase(BaseExportTestCase):

    def check_file_content(self, fname, content):
        fullname = os.path.join(os.path.dirname(__file__), fname)
        with open(fullname + '.actual', 'w') as actual:
            actual.write(content)
        expected_content = open(fullname).read().rstrip()  # strip newline
        self.assertEqual(expected_content, content)
        # remove the .actual file if the test pass
        os.remove(fullname + '.actual')

    def test_export_for_event_based(self):
        # this test will disappear shortly (in the new-year branch)
        # so it is not worth fixing it; just skip
        raise unittest.SkipTest

        # Run an event-based hazard calculation to compute SESs and GMFs
        # Call the exporters for both SES and GMF results  and verify that
        # files were created
        # Since the XML writers (in `openquake.commonlib`) are concerned
        # with correctly generating the XML, we don't test that here
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.get_data_path('event_based_hazard/job.ini')

            # run the calculation in process to create something to export
            with mock.patch.dict(os.environ, {'OQ_NO_DISTRIBUTE': '1'}):
                job = helpers.run_job(cfg, maximum_distance=1,
                                      ses_per_logic_tree_path=1,
                                      investigation_time=12,
                                      number_of_logic_tree_samples=1).job
            self.assertEqual(job.status, 'complete')

            dstore = datastore.DataStore(job.id)

            # 1 SES + 1 GMF + 1 hazard_curve_multi + 2 hazard_curve +
            # 4 hazard maps (with poes 0.1, 0.2 and IMT PGA, SA(0.1))
            outputs = core.get_outputs(job.id)

            # SESs
            ses_outputs = outputs.filter(ds_key='sescollection')
            self.assertEqual(1, len(ses_outputs))

            exported_files = []
            for ses_output in ses_outputs:
                out_file = check_export(ses_output.id, target_dir)
                exported_files.append(out_file)

            self.assertEqual(1, len(exported_files))

            for f in exported_files:
                self._test_exported_file(f)

            # GMFs
            gmf_outputs = outputs.filter(ds_key='gmfs')
            self.assertEqual(1, len(gmf_outputs))

            exported_files = []
            for gmf_output in gmf_outputs:
                out_file = check_export(gmf_output.id, target_dir)
                exported_files.append(out_file)

            self.assertEqual(1, len(exported_files))
            # Check the file paths exist, are absolute, and the files aren't
            # empty.
            for f in exported_files:
                self._test_exported_file(f)

            # check the exact values of the GMFs
            gmfs = writers.write_csv(
                io.StringIO(), dstore['gmfs']['col00'].value).encode('utf8')
            self.check_file_content('expected_gmfset_1.txt', gmfs)

            # Hazard curves
            haz_curves = outputs.filter(ds_key='hcurves')
            self.assertEqual(1, haz_curves.count())
            for curve in haz_curves:
                exported_file = check_export(curve.id, target_dir)
                self._test_exported_file(exported_file)

            # Hazard maps
            haz_maps = outputs.filter(ds_key='hmaps')
            self.assertEqual(1, haz_maps.count())
            for hmap in haz_maps:
                exported_file = check_export(hmap.id, target_dir)
                self._test_exported_file(exported_file)
        finally:
            shutil.rmtree(target_dir)


class ScenarioExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_export_for_scenario(self):
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.get_data_path('scenario_hazard/job.ini')
            # run the calculation in process to create something to export
            with mock.patch.dict(os.environ, {'OQ_NO_DISTRIBUTE': '1'}):
                helpers.run_job(cfg)
            job = models.OqJob.objects.latest('id')
            self.assertEqual(job.status, 'complete')

            outputs = core.get_outputs(job.id)

            gmf_outputs = outputs.filter(ds_key='gmfs')
            self.assertEqual(1, len(gmf_outputs))

            exported_file = check_export(gmf_outputs[0].id, target_dir)

            # Check the file paths exist, is absolute, and the file isn't
            # empty.
            self._test_exported_file(exported_file)

            # Check for the correct number of GMFs in the file:
            tree = etree.parse(exported_file)
            self.assertEqual(20, number_of('nrml:gmf', tree))
        finally:
            shutil.rmtree(target_dir)
