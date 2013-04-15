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

from collections import namedtuple
from lxml import etree
from nose.plugins.attrib import attr

from openquake.engine.db import models
from openquake.engine.export import core as export_core
from openquake.engine.export import hazard

from tests.export.core_test import BaseExportTestCase, number_of
from tests.utils import helpers


def check_export(output_id, target_dir):
    """
    Call hazard.export by checking that the exported file is valid
    according to our XML schema.
    """
    return hazard.export(output_id, target_dir, check_schema=True)


class GetResultExportPathTestCase(unittest.TestCase):

    def setUp(self):
        self.FakeHazardCurve = namedtuple(
            'HazardCurve',
            'output, lt_realization, imt, sa_period, statistics, quantile'
        )
        self.FakeHazardMap = namedtuple(
            'HazardMap',
            'output, lt_realization, imt, sa_period, statistics, quantile'
        )
        self.FakeUHS = namedtuple(
            'UHS',
            'output, lt_realization, statistics, quantile'
        )
        self.FakeDisagg = namedtuple(
            'Disagg',
            'output, lt_realization, imt, sa_period'
        )
        self.FakeGMF = namedtuple(
            'GMF',
            'output, lt_realization'
        )
        self.FakeSES = namedtuple(
            'SES',
            'output, lt_realization'
        )
        self.FakeCLTGMF = namedtuple(
            'CompleteLogicTreeGMF',
            'output'
        )
        self.FakeCLTSES = namedtuple(
            'CompleteLogicTreeSES',
            'output'
        )
        self.FakeOutput = namedtuple(
            'Output',
            'output_type'
        )
        self.FakeLTR = namedtuple(
            'LtRealization',
            'sm_lt_path, gsim_lt_path, ordinal, weight'
        )

        self.ltr_mc = self.FakeLTR(['B1', 'B3'], ['B2', 'B4'], 3, None)
        self.ltr_enum = self.FakeLTR(['B10', 'B9'], ['B7', 'B8'], 0, 0.6)

        self.target_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.target_dir)

    def test_hazard_curve(self):
        output = self.FakeOutput('hazard_curve')

        curves = [
            self.FakeHazardCurve(output, self.ltr_mc, 'PGA', None, None, None),
            self.FakeHazardCurve(output, self.ltr_enum, 'SA', 0.025, None,
                                 None),
            self.FakeHazardCurve(output, None, 'SA', 0.025, 'mean', None),
            self.FakeHazardCurve(output, None, 'SA', 0.025, 'quantile', 0.85),
        ]
        expected_paths = [
            '%s/calc_7/hazard_curve/PGA/'
            'hazard_curve-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/hazard_curve/SA-0.025/'
            'hazard_curve-smltp_B10_B9-gsimltp_B7_B8.xml',
            '%s/calc_7/hazard_curve/SA-0.025/'
            'hazard_curve-mean.xml',
            '%s/calc_7/hazard_curve/SA-0.025/'
            'hazard_curve-quantile_0.85.xml',
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, curve in enumerate(curves):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_path(7, self.target_dir, curve)
            )

    def test_hazard_map(self):
        output = self.FakeOutput('hazard_map')

        maps = [
            self.FakeHazardMap(output, self.ltr_mc, 'PGA', None, None, None),
            self.FakeHazardMap(output, self.ltr_mc, 'SA', 0.025, None, None),
            self.FakeHazardMap(output, None, 'SA', 0.025, 'mean', None),
            self.FakeHazardMap(output, None, 'SA', 0.025, 'quantile', 0.85),
        ]
        expected_paths = [
            '%s/calc_7/hazard_map/PGA/'
            'hazard_map-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/hazard_map/SA-0.025/'
            'hazard_map-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/hazard_map/SA-0.025/'
            'hazard_map-mean.xml',
            '%s/calc_7/hazard_map/SA-0.025/'
            'hazard_map-quantile_0.85.xml',
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, hmap in enumerate(maps):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_path(7, self.target_dir, hmap)
            )

    def test_uhs(self):
        output = self.FakeOutput('uh_spectra')

        uh_spectra = [
            self.FakeUHS(output, self.ltr_mc, None, None),
            self.FakeUHS(output, None, 'mean', None),
            self.FakeUHS(output, None, 'quantile', 0.85),
        ]
        expected_paths = [
            '%s/calc_7/uh_spectra/'
            'uh_spectra-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/uh_spectra/uh_spectra-mean.xml',
            '%s/calc_7/uh_spectra/uh_spectra-quantile_0.85.xml',
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, uhs in enumerate(uh_spectra):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_path(7, self.target_dir, uhs)
            )

    def test_disagg(self):
        output = self.FakeOutput('disagg_matrix')

        matrices = [
            self.FakeDisagg(output, self.ltr_mc, 'PGA', None),
            self.FakeDisagg(output, self.ltr_mc, 'SA', 0.025),
        ]

        expected_paths = [
            '%s/calc_7/disagg_matrix/PGA/'
            'disagg_matrix-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/disagg_matrix/SA-0.025/'
            'disagg_matrix-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, matrix in enumerate(matrices):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_path(7, self.target_dir, matrix)
            )

    def test_gmf(self):
        output = self.FakeOutput('gmf')

        gmf = self.FakeGMF(output, self.ltr_enum)
        expected_path = (
            '%s/calc_8/gmf/gmf-smltp_B10_B9-gsimltp_B7_B8.xml'
            % self.target_dir
        )

        self.assertEqual(
            expected_path,
            hazard._get_result_export_path(8, self.target_dir, gmf)
        )

    def test_ses(self):
        output = self.FakeOutput('ses')

        ses = self.FakeGMF(output, self.ltr_enum)
        expected_path = (
            '%s/calc_8/ses/ses-smltp_B10_B9-gsimltp_B7_B8.xml'
            % self.target_dir
        )

        self.assertEqual(
            expected_path,
            hazard._get_result_export_path(8, self.target_dir, ses)
        )

    def test_clt_gmf(self):
        output = self.FakeOutput('complete_lt_gmf')

        gmf = self.FakeCLTGMF(output)

        expected_path = '%s/calc_9/gmf/complete_lt_gmf.xml'
        expected_path %= self.target_dir

        self.assertEqual(
            expected_path,
            hazard._get_result_export_path(9, self.target_dir, gmf)
        )

    def test_clt_ses(self):
        output = self.FakeOutput('complete_lt_ses')

        ses = self.FakeCLTSES(output)

        expected_path = '%s/calc_10/ses/complete_lt_ses.xml'
        expected_path %= self.target_dir

        self.assertEqual(
            expected_path,
            hazard._get_result_export_path(10, self.target_dir, ses)
        )


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
                hc_files.extend(check_export(curve.id, target_dir))

            self.assertEqual(10, len(hc_files))

            # Test multi hazard curve export:
            hc_files = []
            for curve in multi_curves:
                hc_files.extend(hazard.export(curve.id, target_dir))

            self.assertEqual(5, len(hc_files))

            for f in hc_files:
                self._test_exported_file(f)

            # Test hazard map export:
            hm_files = []
            for haz_map in maps:
                hm_files.extend(check_export(haz_map.id, target_dir))

            self.assertEqual(20, len(hm_files))

            for f in hm_files:
                self._test_exported_file(f)

            # Test UHS export:
            uhs_files = []
            for u in uhs:
                uhs_files.extend(check_export(u.id, target_dir))
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
            # ((2 imts * 2 realizations)
            # + ((2 imts + 1 multi) * (1 mean + 3 quantiles))
            # hazard curves,
            # (2 poes * 2 imts * 2 realizations)
            # + (2 poes * 2 imts * (1 mean + 3 quantiles)) hazard maps
            # Total: 42
            self.assertEqual(46, len(outputs))

            #######
            # SESs:
            ses_outputs = outputs.filter(output_type='ses')
            self.assertEqual(2, len(ses_outputs))

            exported_files = []
            for ses_output in ses_outputs:
                files = check_export(ses_output.id, target_dir)
                exported_files.extend(files)

            self.assertEqual(2, len(exported_files))

            for f in exported_files:
                self._test_exported_file(f)

            ##################
            # Complete LT SES:
            [complete_lt_ses] = outputs.filter(output_type='complete_lt_ses')

            [exported_file] = check_export(complete_lt_ses.id, target_dir)

            self._test_exported_file(exported_file)

            #######
            # GMFs:
            gmf_outputs = outputs.filter(output_type='gmf')
            self.assertEqual(2, len(gmf_outputs))

            exported_files = []
            for gmf_output in gmf_outputs:
                files = check_export(gmf_output.id, target_dir)
                exported_files.extend(files)

            self.assertEqual(2, len(exported_files))
            # Check the file paths exist, are absolute, and the files aren't
            # empty.
            for f in exported_files:
                self._test_exported_file(f)

            ##################
            # Complete LT GMF:
            [complete_lt_gmf] = outputs.filter(output_type='complete_lt_gmf')

            [exported_file] = check_export(complete_lt_gmf.id, target_dir)

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
                [exported_file] = check_export(curve.id, target_dir)
                self._test_exported_file(exported_file)

            ##############
            # Hazard maps:
            haz_maps = outputs.filter(output_type='hazard_map')
            self.assertEqual(24, haz_maps.count())
            for hmap in haz_maps:
                [exported_file] = check_export(hmap.id, target_dir)
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

            exported_files = check_export(gmf_outputs[0].id, target_dir)

            self.assertEqual(1, len(exported_files))
            # Check the file paths exist, is absolute, and the file isn't
            # empty.
            f = exported_files[0]
            self._test_exported_file(f)

            # Check for the correct number of GMFs in the file:
            tree = etree.parse(f)
            self.assertEqual(20, number_of('nrml:gmf', tree))
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
                curve_files.extend(check_export(curve.id, target_dir))

            self.assertEqual(4, len(curve_files))
            for f in curve_files:
                self._test_exported_file(f)

            # Test disagg matrix export:
            matrices = outputs.filter(output_type='disagg_matrix')
            self.assertEqual(8, len(matrices))
            disagg_files = []
            for matrix in matrices:
                disagg_files.extend(check_export(matrix.id, target_dir))

            self.assertEqual(8, len(disagg_files))
            for f in disagg_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)
