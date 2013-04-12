# Copyright (c) 2010-2013, GEM Foundation.
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

from openquake.engine.db import models
from openquake.engine.export import core as export_core
from openquake.engine.export import hazard

from tests.export.core_test import BaseExportTestCase, number_of
from tests.utils import helpers


class UtilsTestCase(unittest.TestCase):

    def setUp(self):
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
            def __init__(self, branches):
                self.branches = branches

        class FakeLogicTreeProcessor(object):
            def __init__(self, gmpe_lt):
                self.gmpe_lt = gmpe_lt

        self.FakeResult = FakeResult
        self.FakeGMPELTBranch = FakeGMPELTBranch

        self.lt_rlz = FakeLtRealization(['b1'])
        branches = dict(b1=FakeGMPELTBranch())
        gmpe_lt = FakeGMPELT(branches)
        self.ltp = FakeLogicTreeProcessor(gmpe_lt)

        self.target_dir = '/tmp/oq/'

    def test__get_end_branch_export_path_one_gsim_bl(self):
        # Test with one GSIM branching level

        # PGA:
        result = self.FakeResult(self.lt_rlz, 'PGA', None)
        expected = '/tmp/oq/FakeGMPE/PGA'
        actual = hazard._get_end_branch_export_path(
            self.target_dir, result, self.ltp
        )
        self.assertEqual(expected, actual)

        # SA:
        result = self.FakeResult(self.lt_rlz, 'SA', '0.025')
        expected = '/tmp/oq/FakeGMPE/SA[0025]'
        actual = hazard._get_end_branch_export_path(
            self.target_dir, result, self.ltp
        )
        self.assertEqual(expected, actual)

    def test__get_end_branch_export_path_two_gsim_bls(self):
        # Same test as above but with multiple GSIM branching levels
        # In this case, we have two branching levels in the GSIM logic tree.
        # The GSIM names should be joined on a `_` to form the directory name.

        class FakeGMPE2(object):
            pass
        b2 = self.FakeGMPELTBranch()
        b2.value = FakeGMPE2()
        self.ltp.gmpe_lt.branches['b2'] = b2
        self.lt_rlz.gsim_lt_path.append('b2')

        # PGA:
        result = self.FakeResult(self.lt_rlz, 'PGA', None)
        expected = '/tmp/oq/FakeGMPE_FakeGMPE2/PGA'
        actual = hazard._get_end_branch_export_path(
            self.target_dir, result, self.ltp
        )
        self.assertEqual(expected, actual)

        # SA:
        result = self.FakeResult(self.lt_rlz, 'SA', '0.025')
        expected = '/tmp/oq/FakeGMPE_FakeGMPE2/SA[0025]'
        actual = hazard._get_end_branch_export_path(
            self.target_dir, result, self.ltp
        )
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
            helpers.run_hazard_job(cfg)

            job = models.OqJob.objects.latest('id')
            self.assertEqual(job.status, 'complete')

            outputs = export_core.get_outputs(job.id)

            expected_outputs = 40  # 10 hazard curves, 20 maps, 10 uhs
            self.assertEqual(expected_outputs, outputs.count())

            # Number of curves:
            # (2 imts * 2 realizations)
            # + (2 imts * (1 mean + 2 quantiles)
            # = 10
            curves = outputs.filter(output_type='hazard_curve')
            self.assertEqual(10, curves.count())

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
                hc_files.extend(hazard.export(curve.id, target_dir))

            self.assertEqual(10, len(hc_files))

            for f in hc_files:
                self._test_exported_file(f)

            # Test hazard map export:
            hm_files = []
            for haz_map in maps:
                hm_files.extend(hazard.export(haz_map.id, target_dir))

            self.assertEqual(20, len(hm_files))

            for f in hm_files:
                self._test_exported_file(f)

            # Test UHS export:
            uhs_files = []
            for u in uhs:
                uhs_files.extend(hazard.export(u.id, target_dir))

            for f in uhs_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)


class EventBasedExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_export_for_event_based(self):
        # Run an event-based hazard calculation to compute SESs and GMFs
        # Call the exporters for both SES and GMF results  and verify that
        # files were created
        # Since the XML writers (in `openquake.nrmllib.writers`) are concerned
        # with correctly generating the XML, we don't test that here...
        # but we should still have an end-to-end QA test.
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('event_based_hazard/job.ini')

            # run the calculation to create something to export
            helpers.run_hazard_job(cfg)

            job = models.OqJob.objects.latest('id')
            self.assertEqual(job.status, 'complete')

            outputs = export_core.get_outputs(job.id)
            # 2 GMFs, 2 SESs, 1 complete logic tree SES, 1 complete LT GMF,
            # ((2 imts * 2 realizations) + (2 imts * (1 mean + 3 quantiles))
            # hazard curves,
            # (2 poes * 2 imts * 2 realizations)
            # + (2 poes * 2 imts * (1 mean + 3 quantiles)) hazard maps
            # Total: 42
            self.assertEqual(42, len(outputs))

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
            # NB: the number of generated gmfs depends on the number
            # of ruptures, which is stochastic number; even having fixed
            # the seed, it will change by changing the order in which the
            # stochastic functions are called; a test relying on that
            # precise number would be fragile, this is why here we just
            # check that there are gmfs (MS)
            self.assertGreater(number_of('nrml:gmf', tree), 0)

            ################
            # Hazard curves:
            haz_curves = outputs.filter(output_type='hazard_curve')
            self.assertEqual(12, haz_curves.count())
            for curve in haz_curves:
                [exported_file] = hazard.export(curve.id, target_dir)
                self._test_exported_file(exported_file)

            ##############
            # Hazard maps:
            haz_maps = outputs.filter(output_type='hazard_map')
            self.assertEqual(24, haz_maps.count())
            for hmap in haz_maps:
                [exported_file] = hazard.export(hmap.id, target_dir)
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
            helpers.run_hazard_job(cfg)

            job = models.OqJob.objects.latest('id')
            self.assertEqual(job.status, 'complete')

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
            self.assertEqual(10, number_of('nrml:gmf', tree))
        finally:
            shutil.rmtree(target_dir)


class DisaggExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_disagg_hazard_export(self):
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('disaggregation/job.ini')

            helpers.run_hazard_job(cfg)

            job = models.OqJob.objects.latest('id')
            self.assertEqual(job.status, 'complete')

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
