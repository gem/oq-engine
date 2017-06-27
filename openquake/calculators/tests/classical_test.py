# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

from nose.plugins.attrib import attr
from openquake.baselib import parallel
from openquake.baselib.python3compat import decode
from openquake.hazardlib import InvalidFile
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.classical import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8, case_9,
    case_10, case_11, case_12, case_13, case_14, case_15, case_16, case_17,
    case_18, case_19, case_20, case_21, case_22, case_23, case_24, case_25,
    case_26, case_27, case_28)


class ClassicalTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, delta=None, **kw):
        self.run_calc(test_dir, 'job.ini', **kw)
        ds = self.calc.datastore
        kind = kw.get('kind', '')  # 'all' or ''
        got = (export(('hcurves/' + kind, 'csv'), ds) +
               export(('hmaps/' + kind, 'csv'), ds) +
               export(('uhs/' + kind, 'csv'), ds))
        self.assertEqual(len(expected), len(got), str(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual,
                                  delta=delta)
        return got

    @attr('qa', 'hazard', 'classical')
    def test_case_1(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_1.__file__)

        if parallel.oq_distribute() != 'no':
            # make sure we saved the data transfer information in job_info
            keys = {decode(key) for key in dict(
                self.calc.datastore['job_info'])}
            self.assertIn('classical.received', keys)
            self.assertIn('classical.sent', keys)

        # there is a single source
        self.assertEqual(len(self.calc.datastore['source_info']), 1)

        # check npz export
        export(('hcurves', 'npz'), self.calc.datastore)

    @attr('qa', 'hazard', 'classical')
    def test_wrong_smlt(self):
        with self.assertRaises(InvalidFile):
            self.run_calc(case_1.__file__, 'job_wrong.ini')

    @attr('qa', 'hazard', 'classical')
    def test_sa_period_too_big(self):
        imtls = '{"SA(4.1)": [0.1, 0.4, 0.6]}'
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(
                case_1.__file__, 'job.ini',
                intensity_measure_types_and_levels=imtls)
        self.assertEqual(
            'SA(4.1) is out of the period range defined for SadighEtAl1997()',
            str(ctx.exception))

    @attr('qa', 'hazard', 'classical')
    def test_case_2(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_2.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_3(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_3.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_4(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_4.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_5(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_5.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_6(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_6.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_7(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_curve-smltp_b1-gsimltp_b1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1.csv'],
            case_7.__file__, kind='all')

    @attr('qa', 'hazard', 'classical')
    def test_case_8(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b4-gsimltp_b1.csv'],
            case_8.__file__, kind='all')

    @attr('qa', 'hazard', 'classical')
    def test_case_9(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv'],
            case_9.__file__, kind='all')

    @attr('qa', 'hazard', 'classical')
    def test_case_10(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv'],
            case_10.__file__, kind='all')

    @attr('qa', 'hazard', 'classical')
    def test_case_11(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b4-gsimltp_b1.csv',
             'quantile_curve-0.1.csv',
             'quantile_curve-0.9.csv'],
            case_11.__file__, kind='all')

    @attr('qa', 'hazard', 'classical')
    def test_case_12(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1_b2.csv'],
            case_12.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_13(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv', 'hazard_map-mean.csv'],
            case_13.__file__)

        # test recomputing the hazard maps, i.e. with --hc
        # must be run sequentially to avoid the usual heisenbug
        self.run_calc(
            case_13.__file__, 'job.ini', exports='csv', poes='0.2',
            hazard_calculation_id=str(self.calc.datastore.calc_id),
            concurrent_tasks='0')
        [fname] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_map-mean2.csv', fname,
                              delta=1E-5)

    @attr('qa', 'hazard', 'classical')
    def test_case_14(self):
        self.assert_curves_ok([
            'hazard_curve-smltp_simple_fault-gsimltp_AbrahamsonSilva2008.csv',
            'hazard_curve-smltp_simple_fault-gsimltp_CampbellBozorgnia2008.csv'
        ], case_14.__file__, kind='all')

    @attr('qa', 'hazard', 'classical')
    def test_case_15(self):  # full enumeration
        self.assert_curves_ok('''\
hazard_curve-max.csv
hazard_curve-mean.csv
hazard_curve-smltp_SM1-gsimltp_BA2008_C2003.csv
hazard_curve-smltp_SM1-gsimltp_BA2008_T2002.csv
hazard_curve-smltp_SM1-gsimltp_CB2008_C2003.csv
hazard_curve-smltp_SM1-gsimltp_CB2008_T2002.csv
hazard_curve-smltp_SM2_a3b1-gsimltp_BA2008_@.csv
hazard_curve-smltp_SM2_a3b1-gsimltp_CB2008_@.csv
hazard_curve-smltp_SM2_a3pt2b0pt8-gsimltp_BA2008_@.csv
hazard_curve-smltp_SM2_a3pt2b0pt8-gsimltp_CB2008_@.csv
hazard_uhs-max.csv
hazard_uhs-mean.csv
hazard_uhs-smltp_SM1-gsimltp_BA2008_C2003.csv
hazard_uhs-smltp_SM1-gsimltp_BA2008_T2002.csv
hazard_uhs-smltp_SM1-gsimltp_CB2008_C2003.csv
hazard_uhs-smltp_SM1-gsimltp_CB2008_T2002.csv
hazard_uhs-smltp_SM2_a3b1-gsimltp_BA2008_@.csv
hazard_uhs-smltp_SM2_a3b1-gsimltp_CB2008_@.csv
hazard_uhs-smltp_SM2_a3pt2b0pt8-gsimltp_BA2008_@.csv
hazard_uhs-smltp_SM2_a3pt2b0pt8-gsimltp_CB2008_@.csv'''.split(),
                              case_15.__file__, kind='all', delta=1E-6)

        # test UHS XML export
        fnames = [f for f in export(('uhs', 'xml'), self.calc.datastore)
                  if 'mean' in f]
        self.assertEqualFiles('expected/hazard_uhs-mean-0.01.xml', fnames[0])
        self.assertEqualFiles('expected/hazard_uhs-mean-0.1.xml', fnames[1])
        self.assertEqualFiles('expected/hazard_uhs-mean-0.2.xml', fnames[2])

        # test hmaps geojson export
        fnames = [f for f in export(('hmaps', 'geojson'), self.calc.datastore)
                  if 'mean' in f]
        self.assertEqualFiles(
            'expected/hazard_map-mean-0.01-PGA.geojson', fnames[0])
        self.assertEqualFiles(
            'expected/hazard_map-mean-0.01-SA(0.1).geojson', fnames[1])
        self.assertEqualFiles(
            'expected/hazard_map-mean-0.1-PGA.geojson', fnames[2])
        self.assertEqualFiles(
            'expected/hazard_map-mean-0.1-SA(0.1).geojson', fnames[3])
        self.assertEqualFiles(
            'expected/hazard_map-mean-0.2-PGA.geojson', fnames[4])
        self.assertEqualFiles(
            'expected/hazard_map-mean-0.2-SA(0.1).geojson', fnames[5])

        # npz exports
        export(('hmaps', 'npz'), self.calc.datastore)
        export(('uhs', 'npz'), self.calc.datastore)

        # check the size of assoc_by_grp for a complex logic tree
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
        nbytes = self.calc.datastore.get_attr(
            'csm_info/assoc_by_grp', 'nbytes')
        self.assertEqual(nbytes, 120)

    @attr('qa', 'hazard', 'classical')
    def test_case_16(self):   # sampling
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'quantile_curve-0.1.csv',
             'quantile_curve-0.9.csv'],
            case_16.__file__)

        # test single realization export
        [fname] = export(('hcurves/rlz-3', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-rlz-003.csv', fname)

    @attr('qa', 'hazard', 'classical')
    def test_case_17(self):  # oversampling
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_2.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv'],
            case_17.__file__, kind='all')

    @attr('qa', 'hazard', 'classical')
    def test_case_18(self):  # GMPEtable
        self.assert_curves_ok(
            ['hazard_curve-mean.csv', 'hazard_map-mean.csv',
             'hazard_uhs-mean.csv'],
            case_18.__file__, delta=1E-7)
        [fname] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/realizations.csv', fname)

    @attr('qa', 'hazard', 'classical')
    def test_case_19(self):
        self.assert_curves_ok([
            'hazard_curve-mean.csv',
            'hazard_curve-smltp_b1-gsimltp_@_@_@_@_b51_@_@.csv',
            'hazard_curve-smltp_b1-gsimltp_@_@_@_@_b52_@_@.csv',
            'hazard_curve-smltp_b1-gsimltp_@_@_@_@_b53_@_@.csv',
            'hazard_curve-smltp_b1-gsimltp_@_@_@_@_b54_@_@.csv',
        ], case_19.__file__, kind='all', delta=1E-7)

    @attr('qa', 'hazard', 'classical')
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
            case_20.__file__, kind='all', delta=1E-7)

    @attr('qa', 'hazard', 'classical')
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
            case_21.__file__, kind='all', delta=1E-7)
        [fname] = export(('sourcegroups', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/sourcegroups.csv', fname)

    @attr('qa', 'hazard', 'classical')
    def test_case_22(self):  # crossing date line calculation for Alaska
        # this also tests the splitting of the source model in two files
        self.assert_curves_ok(['hazard_curve-mean.csv'], case_22.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_23(self):  # filtering away on TRT
        self.assert_curves_ok(['hazard_curve.csv'], case_23.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_24(self):  # UHS
        self.assert_curves_ok(['hazard_curve.csv', 'hazard_uhs.csv'],
                              case_24.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_25(self):  # negative depths
        self.assert_curves_ok(['hazard_curve-smltp_b1-gsimltp_b1.csv'],
                              case_25.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_26(self):  # split YoungsCoppersmith1985MFD
        self.assert_curves_ok(['hazard_curve-rlz-000.csv'], case_26.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_27(self):  # Nankai mutex model
        self.assert_curves_ok(['hazard_curve.csv'], case_27.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_28(self):  # North Africa
        # MultiPointSource with modify MFD logic tree
        self.assert_curves_ok(['hazard_curve_mean.csv'], case_28.__file__)
