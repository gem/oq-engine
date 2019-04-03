# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import mock
import numpy
from openquake.baselib import parallel
from openquake.hazardlib import InvalidFile
from openquake.calculators.views import view
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.tests import CalculatorTestCase, NOT_DARWIN
from openquake.qa_tests_data.classical import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8, case_9,
    case_10, case_11, case_12, case_13, case_14, case_15, case_16, case_17,
    case_18, case_19, case_20, case_21, case_22, case_23, case_24, case_25,
    case_26, case_27, case_28, case_29, case_30, case_31, case_32, case_33,
    case_34, case_35, case_36, case_37)


class ClassicalTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, delta=None, **kw):
        kind = kw.pop('kind', '')
        self.run_calc(test_dir, 'job.ini', **kw)
        ds = self.calc.datastore
        got = (export(('hcurves/' + kind, 'csv'), ds) +
               export(('hmaps/' + kind, 'csv'), ds) +
               export(('uhs/' + kind, 'csv'), ds))
        self.assertEqual(len(expected), len(got), str(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual,
                                  delta=delta)
        return got

    def test_case_1(self):
        self.assert_curves_ok(
            ['hazard_curve-PGA.csv', 'hazard_curve-SA(0.1).csv'],
            case_1.__file__)

        if parallel.oq_distribute() != 'no':
            info = view('job_info', self.calc.datastore)
            self.assertIn('task', info)
            self.assertIn('sent', info)
            self.assertIn('received', info)

        # there is a single source
        self.assertEqual(len(self.calc.datastore['source_info']), 1)

        # check npz export
        export(('hcurves', 'npz'), self.calc.datastore)

        # check extraction
        sitecol = extract(self.calc.datastore, 'sitecol')
        self.assertEqual(len(sitecol.array), 1)

        # check minimum_magnitude discards the source
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_1.__file__, 'job.ini', minimum_magnitude='4.5')
        self.assertEqual(str(ctx.exception), 'All sources were filtered away!')

    def test_wrong_smlt(self):
        with self.assertRaises(InvalidFile):
            self.run_calc(case_1.__file__, 'job_wrong.ini')

    def test_sa_period_too_big(self):
        imtls = '{"SA(4.1)": [0.1, 0.4, 0.6]}'
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(
                case_1.__file__, 'job.ini',
                intensity_measure_types_and_levels=imtls)
        self.assertEqual(
            'SA(4.1) is out of the period range defined for [SadighEtAl1997]',
            str(ctx.exception))

    def test_case_2(self):
        self.run_calc(case_2.__file__, 'job.ini')

        # check view_pmap for a single realization
        got = view('pmap:grp-00', self.calc.datastore)
        self.assertEqual(got, '''\
{0: <ProbabilityCurve
[[2.26776679e-03 0.00000000e+00]
 [1.67915423e-05 0.00000000e+00]
 [0.00000000e+00 0.00000000e+00]
 [0.00000000e+00 0.00000000e+00]]>}''')

        # check view inputs
        lines = view('inputs', self.calc.datastore).splitlines()
        self.assertEqual(len(lines), 9)

        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve.csv', fname)

    def test_case_3(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_3.__file__)

    def test_case_4(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_4.__file__)

    def test_case_5(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_5.__file__)

    def test_case_6(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_6.__file__)

    def test_case_7(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_curve-smltp_b1-gsimltp_b1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1.csv'],
            case_7.__file__)

        # exercising extract/mean_std_curves
        extract(self.calc.datastore, 'mean_std_curves')

        # exercise the warning for no output when mean_hazard_curves='false'
        self.run_calc(
            case_7.__file__, 'job.ini', mean_hazard_curves='false',
            calculation_mode='preclassical',  poes='0.1')

    def test_case_8(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b4-gsimltp_b1.csv'],
            case_8.__file__)

    def test_case_9(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv'],
            case_9.__file__)

    def test_case_10(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv'],
            case_10.__file__)

    def test_case_11(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b4-gsimltp_b1.csv',
             'quantile_curve-0.1.csv',
             'quantile_curve-0.9.csv'],
            case_11.__file__)

    def test_case_12(self):
        # test Modified GMPE
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1_b2.csv'],
            case_12.__file__)

    def test_case_13(self):
        self.assert_curves_ok(
            ['hazard_curve-mean_PGA.csv', 'hazard_curve-mean_SA(0.2).csv',
             'hazard_map-mean.csv'], case_13.__file__)

        # test recomputing the hazard maps
        self.run_calc(
            case_13.__file__, 'job.ini', exports='csv',
            hazard_calculation_id=str(self.calc.datastore.calc_id),
            gsim_logic_tree_file='', source_model_logic_tree_file='')
        [fname] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname,
                              delta=1E-5)

        # test extract/hcurves/rlz-0, used by the npz exports
        haz = vars(extract(self.calc.datastore, 'hcurves'))
        self.assertEqual(sorted(haz), ['all', 'investigation_time'])
        self.assertEqual(
            haz['all'].dtype.names, ('lon', 'lat', 'depth', 'mean'))
        array = haz['all']['mean']
        self.assertEqual(array.dtype.names, ('PGA', 'SA(0.2)'))
        self.assertEqual(array['PGA'].dtype.names,
                         ('0.005', '0.007', '0.0098', '0.0137', '0.0192',
                          '0.0269', '0.0376', '0.0527', '0.0738', '0.103',
                          '0.145', '0.203', '0.284'))

    def test_case_14(self):
        # test preclassical and OQ_SAMPLE_SOURCES
        with mock.patch.dict(os.environ, OQ_SAMPLE_SOURCES='1'):
            self.run_calc(
                case_14.__file__, 'job.ini', calculation_mode='preclassical')
        rpt = view('ruptures_per_trt', self.calc.datastore)
        self.assertEqual(rpt, """\
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
simple_fault.xml 0      Active Shallow Crust 55           447         
================ ====== ==================== ============ ============""")
        # test classical
        self.assert_curves_ok([
            'hazard_curve-smltp_simple_fault-gsimltp_AbrahamsonSilva2008.csv',
            'hazard_curve-smltp_simple_fault-gsimltp_CampbellBozorgnia2008.csv'
        ], case_14.__file__)

    def test_case_15(self):
        # this is a case with both splittable and unsplittable sources
        self.assert_curves_ok('''\
hazard_curve-max-PGA.csv,
hazard_curve-max-SA(0.1).csv
hazard_curve-mean-PGA.csv
hazard_curve-mean-SA(0.1).csv
hazard_curve-std-PGA.csv
hazard_curve-std-SA(0.1).csv
hazard_uhs-max.csv
hazard_uhs-mean.csv
hazard_uhs-std.csv
'''.split(), case_15.__file__, delta=1E-6)

        # test UHS XML export
        fnames = [f for f in export(('uhs', 'xml'), self.calc.datastore)
                  if 'mean' in f]
        self.assertEqualFiles('expected/hazard_uhs-mean-0.01.xml', fnames[0])
        self.assertEqualFiles('expected/hazard_uhs-mean-0.1.xml', fnames[1])
        self.assertEqualFiles('expected/hazard_uhs-mean-0.2.xml', fnames[2])

        # npz exports
        [fname] = export(('hmaps', 'npz'), self.calc.datastore)
        arr = numpy.load(fname)['all']
        self.assertEqual(arr['mean'].dtype.names, ('PGA', 'SA(0.1)'))
        [fname] = export(('uhs', 'npz'), self.calc.datastore)
        arr = numpy.load(fname)['all']
        self.assertEqual(arr['mean'].dtype.names, ('0.01', '0.1', '0.2'))

        # here is the size of assoc_by_grp for a complex logic tree
        # grp_id gsim_idx rlzis
        # 0	0	 {0, 1}
        # 0	1	 {2, 3}
        # 1	0	 {0, 2}
        # 1	1	 {1, 3}
        # 2	0	 {4}
        # 2	1	 {5}
        # 3	0	 {6}
        # 3	1	 {7}
        # nbytes = (2 + 2 + 8) * 8 + 4 * 4 + 4 * 2 = 120

        # full source model logic tree
        cinfo = self.calc.datastore['csm_info']
        ra0 = cinfo.get_rlzs_assoc()
        self.assertEqual(
            sorted(ra0.by_grp()), ['grp-00', 'grp-01', 'grp-02', 'grp-03'])

        # reduction of the source model logic tree
        ra = cinfo.get_rlzs_assoc(sm_lt_path=['SM2', 'a3b1'])
        self.assertEqual(len(ra.by_grp()), 1)
        numpy.testing.assert_equal(
            len(ra.by_grp()['grp-02']),
            len(ra0.by_grp()['grp-02']))

        # more reduction of the source model logic tree
        ra = cinfo.get_rlzs_assoc(sm_lt_path=['SM1'])
        self.assertEqual(sorted(ra.by_grp()), ['grp-00', 'grp-01'])
        numpy.testing.assert_equal(
            ra.by_grp()['grp-00'], ra0.by_grp()['grp-00'])
        numpy.testing.assert_equal(
            ra.by_grp()['grp-01'], ra0.by_grp()['grp-01'])

        # reduction of the gsim logic tree
        ra = cinfo.get_rlzs_assoc(trts=['Stable Continental Crust'])
        self.assertEqual(sorted(ra.by_grp()), ['grp-00', 'grp-01'])
        numpy.testing.assert_equal(ra.by_grp()['grp-00'], [[0, 1]])

    def test_case_16(self):   # sampling
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'quantile_curve-0.1.csv',
             'quantile_curve-0.9.csv'],
            case_16.__file__)

        # test that the single realization export fails because
        # individual_curves was false
        with self.assertRaises(KeyError) as ctx:
            export(('hcurves/rlz-3', 'csv'), self.calc.datastore)
        self.assertIn("No 'hcurves-rlzs' found", str(ctx.exception))

    def test_case_17(self):  # oversampling
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_2.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv'],
            case_17.__file__)

    def test_case_18(self):  # GMPEtable
        self.assert_curves_ok(
            ['hazard_curve-mean_PGA.csv',
             'hazard_curve-mean_SA(0.2).csv',
             'hazard_curve-mean_SA(1.0).csv',
             'hazard_map-mean.csv',
             'hazard_uhs-mean.csv'],
            case_18.__file__, kind='stats', delta=1E-7)
        [fname] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/realizations.csv', fname)

        # check exporting a single realization in XML and CSV
        [fname] = export(('uhs/rlz-001', 'xml'),  self.calc.datastore)
        if NOT_DARWIN:  # broken on macOS
            self.assertEqualFiles('expected/uhs-rlz-1.xml', fname)
        [fname] = export(('uhs/rlz-001', 'csv'),  self.calc.datastore)
        self.assertEqualFiles('expected/uhs-rlz-1.csv', fname)

        # extracting hmaps
        hmaps = extract(self.calc.datastore, 'hmaps')['all']['mean']
        self.assertEqual(hmaps.dtype.names, ('PGA', 'SA(0.2)', 'SA(1.0)'))

    def test_case_19(self):
        # this test is a lot faster without parallelism (from 89s to 25s)
        self.assert_curves_ok([
            'hazard_curve-mean_PGA.csv',
            'hazard_curve-mean_SA(0.1).csv',
            'hazard_curve-mean_SA(0.15).csv',
        ], case_19.__file__, delta=1E-5, concurrent_tasks='0')

    def test_case_20(self):  # Source geometry enumeration
        self.assert_curves_ok([
            'hazard_curve-smltp_sm1_sg1_cog1_char_complex-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg1_cog1_char_plane-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg1_cog1_char_simple-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg1_cog2_char_complex-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg1_cog2_char_plane-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg1_cog2_char_simple-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg2_cog1_char_complex-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg2_cog1_char_plane-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg2_cog1_char_simple-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg2_cog2_char_complex-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg2_cog2_char_plane-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_sm1_sg2_cog2_char_simple-gsimltp_Sad1997.csv'],
            case_20.__file__, delta=1E-7)

    def test_case_21(self):  # Simple fault dip and MFD enumeration
        self.assert_curves_ok([
            'hazard_curve-smltp_b1_mfd1_high_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_high_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_high_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_low_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_low_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_low_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_mid_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_mid_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd1_mid_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_high_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_high_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_high_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_low_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_low_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_low_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_mid_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_mid_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd2_mid_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_high_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_high_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_high_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_low_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_low_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_low_dip_dip60-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_mid_dip_dip30-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_mid_dip_dip45-gsimltp_Sad1997.csv',
            'hazard_curve-smltp_b1_mfd3_mid_dip_dip60-gsimltp_Sad1997.csv'],
            case_21.__file__, delta=1E-7)
        [fname] = export(('sourcegroups', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/sourcegroups.csv', fname)

    def test_case_22(self):  # crossing date line calculation for Alaska
        # this also tests the splitting of the source model in two files
        self.assert_curves_ok([
            '/hazard_curve-mean-PGA.csv', 'hazard_curve-mean-SA(0.1)',
            'hazard_curve-mean-SA(0.2).csv', 'hazard_curve-mean-SA(0.5).csv',
            'hazard_curve-mean-SA(1.0).csv', 'hazard_curve-mean-SA(2.0).csv',
        ], case_22.__file__)

    def test_case_23(self):  # filtering away on TRT
        self.assert_curves_ok(['hazard_curve.csv'], case_23.__file__)
        checksum = self.calc.datastore['/'].attrs['checksum32']
        self.assertEqual(checksum, 3211843635)

    def test_case_24(self):  # UHS
        self.assert_curves_ok([
            'hazard_curve-PGA.csv', 'hazard_curve-PGV.csv',
            'hazard_curve-SA(0.025).csv', 'hazard_curve-SA(0.05).csv',
            'hazard_curve-SA(0.1).csv', 'hazard_curve-SA(0.2).csv',
            'hazard_curve-SA(0.5).csv', 'hazard_curve-SA(1.0).csv',
            'hazard_curve-SA(2.0).csv', 'hazard_uhs.csv'], case_24.__file__)

    def test_case_25(self):  # negative depths
        self.assert_curves_ok(['hazard_curve-smltp_b1-gsimltp_b1.csv'],
                              case_25.__file__)

    def test_case_26(self):  # split YoungsCoppersmith1985MFD
        self.assert_curves_ok(['hazard_curve-rlz-000.csv'], case_26.__file__)

    def test_case_27(self):  # Nankai mutex model
        self.assert_curves_ok(['hazard_curve.csv'], case_27.__file__)

    def test_case_28(self):  # North Africa
        # MultiPointSource with modify MFD logic tree
        self.assert_curves_ok([
            'hazard_curve-mean-PGA.csv', 'hazard_curve-mean-SA(0.05).csv',
            'hazard_curve-mean-SA(0.1).csv', 'hazard_curve-mean-SA(0.2).csv',
            'hazard_curve-mean-SA(0.5)', 'hazard_curve-mean-SA(1.0).csv',
            'hazard_curve-mean-SA(2.0).csv'], case_28.__file__)

    def test_case_29(self):  # non parametric source
        # check the high IMLs are zeros: this is a test for
        # NonParametricProbabilisticRupture.get_probability_no_exceedance
        self.assert_curves_ok(['hazard_curve-PGA.csv'], case_29.__file__)

    def test_case_30(self):  # point on the international data line
        if NOT_DARWIN:  # broken on macOS
            self.assert_curves_ok(['hazard_curve-PGA.csv',
                                   'hazard_curve-SA(1.0).csv'],
                                  case_30.__file__)
            # check rupdata
            nruptures = []
            for grp, rupdata in sorted(self.calc.datastore['rup'].items()):
                nruptures.append((grp, len(rupdata)))
            self.assertEqual(nruptures, [('grp-00', 700), ('grp-01', 1117),
                                         ('grp-02', 1385)])

            # check best_rlz on 5 sites
            best_rlz = self.calc.datastore['best_rlz'].value
            numpy.testing.assert_equal(best_rlz, [2, 9, 2, 3, 1])

    def test_case_31(self):
        # source specific logic tree
        self.assert_curves_ok(['hazard_curve-mean-PGA.csv',
                               'hazard_curve-std-PGA.csv'], case_31.__file__,
                              delta=1E-5)

    def test_case_32(self):
        # source specific logic tree
        self.assert_curves_ok(['hazard_curve-mean-PGA.csv'], case_32.__file__)

    def test_case_33(self):
        # directivity
        self.assert_curves_ok(['hazard_curve-mean-PGA.csv'], case_33.__file__)

    def test_case_34(self):
        # spectral averaging
        self.assert_curves_ok([
            'hazard_curve-mean-AvgSA.csv'], case_34.__file__)

    def test_case_35(self):
        # cluster
        self.assert_curves_ok(['hazard_curve-rlz-000-PGA.csv'],
                              case_35.__file__)

    def test_case_36(self):
        # test with advanced applyToSources and preclassical
        self.run_calc(case_36.__file__, 'job.ini')

    def test_case_37(self):
        # chch gsims
        self.assert_curves_ok(['hazard_curve-mean-PGA.csv'], case_37.__file__)
