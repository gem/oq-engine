# Copyright (c) 2010-2014, GEM Foundation.
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
import os
import shutil
import tempfile
import unittest

from collections import namedtuple
from lxml import etree
from nose.plugins.attrib import attr

from openquake.commonlib import nrml

from openquake.engine.db import models
from openquake.engine.export import core
from openquake.engine.export import hazard

from openquake.engine.tests.export.core_test import \
    BaseExportTestCase, number_of
from openquake.engine.tests.utils import helpers


def check_export(output_id, target):
    """
    Call export by checking that the exported file is valid
    """
    out_file = core.export(output_id, target, 'xml')
    nrml.read(out_file)
    return out_file


class GetResultExportDestTestCase(unittest.TestCase):

    def setUp(self):
        self.Location = namedtuple('Location', 'x, y')

        self.FakeHazardCurve = namedtuple(
            'HazardCurve',
            'output, lt_realization, imt, sa_period, statistics, quantile'
        )
        self.FakeHazardMap = namedtuple(
            'HazardMap',
            'output, lt_realization, imt, sa_period, poe, statistics, quantile'
        )
        self.FakeUHS = namedtuple(
            'UHS',
            'output, lt_realization, poe, statistics, quantile'
        )
        self.FakeDisagg = namedtuple(
            'Disagg',
            'output, lt_realization, imt, sa_period, location, poe'
        )
        self.FakeGMF = namedtuple(
            'GMF',
            'output, lt_realization'
        )
        self.FakeSES = namedtuple(
            'SES',
            'output, ordinal, sm_lt_path'
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
                hazard._get_result_export_dest(7, self.target_dir, curve)
            )

    def test_hazard_curve_multi(self):
        output = self.FakeOutput('hazard_curve_multi')

        curves = [
            self.FakeHazardCurve(output, self.ltr_mc, None, None, None, None),
            self.FakeHazardCurve(output, self.ltr_enum, None, None, None,
                                 None),
            self.FakeHazardCurve(output, None, None, None, 'mean', None),
            self.FakeHazardCurve(output, None, None, None, 'quantile', 0.85),
        ]
        expected_paths = [
            '%s/calc_7/hazard_curve_multi/'
            'hazard_curve_multi-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/hazard_curve_multi/'
            'hazard_curve_multi-smltp_B10_B9-gsimltp_B7_B8.xml',
            '%s/calc_7/hazard_curve_multi/'
            'hazard_curve_multi-mean.xml',
            '%s/calc_7/hazard_curve_multi/'
            'hazard_curve_multi-quantile_0.85.xml',
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, curve in enumerate(curves):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_dest(7, self.target_dir, curve)
            )

    def test_hazard_map(self):
        output = self.FakeOutput('hazard_map')

        maps = [
            self.FakeHazardMap(output, self.ltr_mc, 'PGA', None, 0.1,
                               None, None),
            self.FakeHazardMap(output, self.ltr_mc, 'SA', 0.025, 0.2,
                               None, None),
            self.FakeHazardMap(output, None, 'SA', 0.025, 0.3,
                               'mean', None),
            self.FakeHazardMap(output, None, 'SA', 0.025, 0.4,
                               'quantile', 0.85),
        ]
        expected_paths = [
            '%s/calc_7/hazard_map/PGA/'
            'hazard_map-poe_0.1-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/hazard_map/SA-0.025/'
            'hazard_map-poe_0.2-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/hazard_map/SA-0.025/'
            'hazard_map-poe_0.3-mean.xml',
            '%s/calc_7/hazard_map/SA-0.025/'
            'hazard_map-poe_0.4-quantile_0.85.xml',
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, hmap in enumerate(maps):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_dest(7, self.target_dir, hmap)
            )

    def test_uhs(self):
        output = self.FakeOutput('uh_spectra')

        uh_spectra = [
            self.FakeUHS(output, self.ltr_mc, 0.1, None, None),
            self.FakeUHS(output, None, 0.2, 'mean', None),
            self.FakeUHS(output, None, 0.3, 'quantile', 0.85),
        ]
        expected_paths = [
            '%s/calc_7/uh_spectra/'
            'uh_spectra-poe_0.1-smltp_B1_B3-gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/uh_spectra/uh_spectra-poe_0.2-mean.xml',
            '%s/calc_7/uh_spectra/uh_spectra-poe_0.3-quantile_0.85.xml',
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, uhs in enumerate(uh_spectra):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_dest(7, self.target_dir, uhs)
            )

    def test_disagg(self):
        output = self.FakeOutput('disagg_matrix')

        matrices = [
            self.FakeDisagg(output, self.ltr_mc, 'PGA', None,
                            self.Location(33.333, -89.999001), 0.1),
            self.FakeDisagg(output, self.ltr_enum, 'SA', 0.025,
                            self.Location(40.1, 10.1), 0.02),
        ]

        expected_paths = [
            '%s/calc_7/disagg_matrix/PGA/'
            'disagg_matrix(0.1)-lon_33.333-lat_-89.999001-smltp_B1_B3-'
            'gsimltp_B2_B4-ltr_3.xml',
            '%s/calc_7/disagg_matrix/SA-0.025/'
            'disagg_matrix(0.02)-lon_40.1-lat_10.1-'
            'smltp_B10_B9-gsimltp_B7_B8.xml'
        ]
        expected_paths = [x % self.target_dir for x in expected_paths]

        for i, matrix in enumerate(matrices):
            self.assertEqual(
                expected_paths[i],
                hazard._get_result_export_dest(7, self.target_dir, matrix)
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
            hazard._get_result_export_dest(8, self.target_dir, gmf)
        )

    def test_ses(self):
        output = self.FakeOutput('ses')

        ses = self.FakeSES(output, 1, self.ltr_mc.sm_lt_path)
        expected_path = (
            '%s/calc_8/ses/ses-1-smltp_B1_B3.xml'
            % self.target_dir
        )
        self.assertEqual(
            expected_path,
            hazard._get_result_export_dest(8, self.target_dir, ses)
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
    expected_gmfs = 'expected_gmfset_1.txt', 'expected_gmfset_2.txt'

    def check_file_content(self, fname, content):
        fullname = os.path.join(os.path.dirname(__file__), fname)
        with open(fullname + '.actual', 'w') as actual:
            actual.write(content)
        expected_content = open(fullname).read().rstrip()  # strip newline
        self.assertEqual(expected_content, content)
        # remove the .actual file if the test pass
        os.remove(fullname + '.actual')

    @attr('slow')
    def test_export_for_event_based(self):
        # Run an event-based hazard calculation to compute SESs and GMFs
        # Call the exporters for both SES and GMF results  and verify that
        # files were created
        # Since the XML writers (in `openquake.commonlib`) are concerned
        # with correctly generating the XML, we don't test that here...
        # but we should still have an end-to-end QA test.
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.get_data_path('event_based_hazard/job.ini')

            # run the calculation in process to create something to export
            with mock.patch.dict(os.environ, {'OQ_NO_DISTRIBUTE': '1'}):
                job = helpers.run_job(cfg, maximum_distance=1,
                                      ses_per_logic_tree_path=1).job
            self.assertEqual(job.status, 'complete')

            outputs = core.get_outputs(job.id)
            # 2 GMFs, 1 SES,
            # ((2 imts * 2 realizations)
            self.assertEqual(45, len(outputs))

            #######
            # SESs:
            ses_outputs = outputs.filter(output_type='ses')
            self.assertEqual(1, len(ses_outputs))

            exported_files = []
            for ses_output in ses_outputs:
                out_file = check_export(ses_output.id, target_dir)
                exported_files.append(out_file)

            self.assertEqual(1, len(exported_files))

            for f in exported_files:
                self._test_exported_file(f)

            #######
            # GMFs:
            gmf_outputs = outputs.filter(output_type='gmf')
            self.assertEqual(2, len(gmf_outputs))

            exported_files = []
            for gmf_output in gmf_outputs:
                out_file = check_export(gmf_output.id, target_dir)
                exported_files.append(out_file)

            self.assertEqual(2, len(exported_files))
            # Check the file paths exist, are absolute, and the files aren't
            # empty.
            for f in exported_files:
                self._test_exported_file(f)

            # check the exact values of the GMFs
            [gmfset1] = gmf_outputs[0].gmf
            [gmfset2] = gmf_outputs[1].gmf
            self.check_file_content('expected_gmfset_1.txt', str(gmfset1))
            self.check_file_content('expected_gmfset_2.txt', str(gmfset2))

            ################
            # Hazard curves:
            haz_curves = outputs.filter(output_type='hazard_curve')
            self.assertEqual(12, haz_curves.count())
            for curve in haz_curves:
                exported_file = check_export(curve.id, target_dir)
                self._test_exported_file(exported_file)

            ##############
            # Hazard maps:
            haz_maps = outputs.filter(output_type='hazard_map')
            self.assertEqual(24, haz_maps.count())
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

            self.assertEqual(2, len(outputs))  # 1 GMF, 1 SES

            gmf_outputs = outputs.filter(output_type='gmf_scenario')
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


class DisaggExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_disagg_hazard_export(self):
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.get_data_path('disaggregation/job.ini')

            # run the calculation in process to create something to export
            os.environ['OQ_NO_DISTRIBUTE'] = '1'
            try:
                helpers.run_job(cfg)
            finally:
                del os.environ['OQ_NO_DISTRIBUTE']

            job = models.OqJob.objects.latest('id')
            self.assertEqual(job.status, 'complete')

            outputs = core.get_outputs(job.id)

            # Test curve export:
            curves = outputs.filter(output_type='hazard_curve')
            self.assertEqual(4, len(curves))
            curve_files = []
            for curve in curves:
                curve_files.append(check_export(curve.id, target_dir))

            self.assertEqual(4, len(curve_files))
            for f in curve_files:
                self._test_exported_file(f)

            # Test disagg matrix export:
            matrices = outputs.filter(output_type='disagg_matrix')
            self.assertEqual(8, len(matrices))
            disagg_files = []
            for matrix in matrices:
                disagg_files.append(check_export(matrix.id, target_dir))

            self.assertEqual(8, len(disagg_files))
            for f in disagg_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)
