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


import shutil
import tempfile
import unittest

from lxml import etree
from nose.plugins.attrib import attr

from openquake.db import models
from openquake.export import core as export_core
from openquake.export import hazard

from tests.export.core_test import BaseExportTestCase, number_of
from tests.utils import helpers


class UtilsTestCase(unittest.TestCase):

    def test__get_end_branch_export_path(self):
        class FakeLtRealization(object):
            def __init__(self, gsim_lt_path):
                self.gsim_lt_path = gsim_lt_path
        class FakeResult(object):
            def __init__(self, lt_realization, imt, sa_period):
                self.lt_realization = lt_realization
                self.imt = imt
                self.sa_period = sa_period
        class FakeGMPE(object):
            pass
        class FakeGMPELTBranch(object):
            value = FakeGMPE()
        class FakeGMPELT(object):
            branches = dict(b1=FakeGMPELTBranch())
        class FakeLogicTreeProcessor(object):
            gmpe_lt = FakeGMPELT()

        target_dir = '/tmp/oq/'
        lt_rlz = FakeLtRealization(['b1'])
        ltp = FakeLogicTreeProcessor()

        # PGA:
        result = FakeResult(lt_rlz, 'PGA', None)
        expected = '/tmp/oq/FakeGMPE/PGA'
        actual = hazard._get_end_branch_export_path(target_dir, result, ltp)
        self.assertEqual(expected, actual)

        # SA:
        result = FakeResult(lt_rlz, 'SA', '0.025')
        expected = '/tmp/oq/FakeGMPE/SA[0025]'
        actual = hazard._get_end_branch_export_path(target_dir, result, ltp)
        self.assertEqual(expected, actual)


class ClassicalExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_classical_hazard_export(self):
        # Run a hazard calculation to compute some curves and maps
        # Call the exporter and verify that files were created
        # Since the hazard curve XML writer is concerned with correctly
        # generating XML, we won't test that here.
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')

            # run the calculation to create something to export
            retcode = helpers.run_hazard_job_sp(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            expected_outputs = 18  # 6 hazard curves + 12 hazard maps
            self.assertEqual(expected_outputs, len(outputs))

            # Export the hazard curves:
            curves = outputs.filter(output_type='hazard_curve')
            hc_files = []
            for curve in curves:
                hc_files.extend(hazard.export(curve.id, target_dir))

            self.assertEqual(6, len(hc_files))

            for f in hc_files:
                self._test_exported_file(f)

            # Test hazard map export as well.
            maps = outputs.filter(output_type='hazard_map')
            hm_files = []
            for haz_map in maps:
                hm_files.extend(hazard.export(haz_map.id, target_dir))

            self.assertEqual(12, len(hm_files))

            for f in hm_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)


class EventBasedExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_export_for_event_based(self):
        # Run an event-based hazard calculation to compute SESs and GMFs
        # Call the exporters for both SES and GMF results  and verify that
        # files were created
        # Since the XML writers (in `nrml.writers`) are concerned with
        # correctly generating the XML, we don't test that here...
        # but we should still have an end-to-end QA test.
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('event_based_hazard/job.ini')

            # run the calculation to create something to export
            retcode = helpers.run_hazard_job_sp(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            # 2 GMFs, 2 SESs, 1 complete logic tree SES, 1 complete LT GMF,
            # and 4 hazard curve collections
            self.assertEqual(18, len(outputs))

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
                self._test_exported_file(f)

            ##################
            # Complete LT SES:
            [complete_lt_ses] = outputs.filter(output_type='complete_lt_ses')

            [exported_file] = hazard.export(complete_lt_ses.id, target_dir)

            self._test_exported_file(exported_file)

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
                self._test_exported_file(f)

            ##################
            # Complete LT GMF:
            [complete_lt_gmf] = outputs.filter(output_type='complete_lt_gmf')

            [exported_file] = hazard.export(complete_lt_gmf.id, target_dir)

            self._test_exported_file(exported_file)

            # Check for the correct number of GMFs in the file:
            tree = etree.parse(exported_file)
            self.assertEqual(442, number_of('nrml:gmf', tree))

            ################
            # Hazard curves:
            haz_curves = outputs.filter(output_type='hazard_curve')
            for curve in haz_curves:
                [exported_file] = hazard.export(curve.id, target_dir)
                self._test_exported_file(exported_file)

        finally:
            shutil.rmtree(target_dir)


class ScenarioExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_export_for_scenario(self):
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('scenario_hazard/job.ini')

            # run the calculation to create something to export
            retcode = helpers.run_hazard_job_sp(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)

            self.assertEqual(1, len(outputs))  # 1 GMF

            gmf_outputs = outputs.filter(output_type='gmf_scenario')
            self.assertEqual(1, len(gmf_outputs))

            exported_files = hazard.export(gmf_outputs[0].id, target_dir)

            self.assertEqual(1, len(exported_files))
            # Check the file paths exist, is absolute, and the file isn't
            # empty.
            f = exported_files[0]
            self._test_exported_file(f)

            # Check for the correct number of GMFs in the file:
            tree = etree.parse(f)
            self.assertEqual(3, number_of('nrml:gmf', tree))
            # 3 because there are 3 sites in the job.ini file
        finally:
            shutil.rmtree(target_dir)


class DisaggExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_disagg_hazard_export(self):
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('disaggregation/job.ini')

            retcode = helpers.run_hazard_job_sp(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)

            # Test curve export:
            curves = outputs.filter(output_type='hazard_curve')
            self.assertEqual(4, len(curves))
            curve_files = []
            for curve in curves:
                curve_files.extend(hazard.export(curve.id, target_dir))

            self.assertEqual(4, len(curve_files))
            for f in curve_files:
                self._test_exported_file(f)

            # Test disagg matrix export:
            matrices = outputs.filter(output_type='disagg_matrix')
            self.assertEqual(8, len(matrices))
            disagg_files = []
            for matrix in matrices:
                disagg_files.extend(hazard.export(matrix.id, target_dir))

            self.assertEqual(8, len(disagg_files))
            for f in disagg_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)
