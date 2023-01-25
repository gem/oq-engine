# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

import gzip
import unittest
import numpy
from openquake.baselib import parallel, general, config
from openquake.baselib.python3compat import decode
from openquake.hazardlib import InvalidFile, contexts, nrml
from openquake.hazardlib.source.rupture import get_ruptures
from openquake.hazardlib.sourcewriter import write_source_model
from openquake.calculators.views import view, text_table
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.tests import (
    CalculatorTestCase, NOT_DARWIN, strip_calc_id)
from openquake.qa_tests_data.classical import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8, case_9,
    case_10, case_11, case_12, case_13, case_14, case_15, case_16, case_17,
    case_18, case_19, case_20, case_21, case_22, case_23, case_24, case_25,
    case_26, case_27, case_28, case_29, case_30, case_31, case_32, case_33,
    case_34, case_35, case_36, case_37, case_38, case_39, case_40, case_41,
    case_42, case_43, case_44, case_45, case_46, case_47, case_48, case_49,
    case_50, case_51, case_52, case_53, case_54, case_55, case_56, case_57,
    case_58, case_59, case_60, case_61, case_62, case_63, case_64, case_65,
    case_66, case_67, case_68, case_69, case_70, case_71, case_72, case_73,
    case_74, case_75, case_76, case_77, case_78, case_79, case_80, case_81)

ae = numpy.testing.assert_equal
aac = numpy.testing.assert_allclose


def get_dists(dstore):
    dic = general.AccumDict(accum=[])  # site_id -> distances
    rup = dstore['rup']
    for sid, dst in zip(rup['sids'], rup['rrup']):
        dic[sid].append(round(dst, 1))
    return {sid: sorted(dsts, reverse=True) for sid, dsts in dic.items()}


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
            info = text_table(view('job_info', self.calc.datastore))
            self.assertIn('task', info)
            self.assertIn('sent', info)
            self.assertIn('received', info)

            slow = view('task:classical:-1', self.calc.datastore)
            self.assertIn('taskno', slow)
            self.assertIn('duration', slow)

        # there is a single source
        self.assertEqual(len(self.calc.datastore['source_info']), 1)

        # check npz export
        export(('hcurves', 'npz'), self.calc.datastore)

        # check extraction
        sitecol = extract(self.calc.datastore, 'sitecol')
        self.assertEqual(len(sitecol.array), 4)

        # check minimum_magnitude discards the source
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_1.__file__, 'job.ini', minimum_magnitude='4.5')
        self.assertEqual(str(ctx.exception), 'All sources were discarded!?')

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

        # check view inputs
        lines = text_table(view('inputs', self.calc.datastore)).splitlines()
        self.assertEqual(len(lines), 13)  # rst table with 13 rows

        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve.csv', fname)

    def test_case_3(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_3.__file__)

        # checking sitecol as DataFrame
        self.calc.datastore.read_df('sitecol', 'sids')

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
        # this is a case with duplicated sources
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_curve-smltp_b1-gsimltp_b1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1.csv'],
            case_7.__file__)

        # check the weights of the sources, a simple fault and a complex fault
        info = self.calc.datastore.read_df('source_info', 'source_id')
        self.assertEqual(info.loc[b'1'].weight, 184)
        self.assertEqual(info.loc[b'2'].weight, 118)

        # checking the individual hazard maps are nonzero
        iml = self.calc.datastore.sel(
            'hmaps-rlzs', imt="PGA", site_id=0).squeeze()
        aac(iml, [0.167078, 0.134646], atol=.0001)  # for the two realizations

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

        # test disagg_by_grp
        df = self.calc.datastore.read_df('disagg_by_grp')
        fname = general.gettemp(text_table(df))
        self.assertEqualFiles('expected/disagg_by_grp.rst', fname)

    def test_case_13(self):
        self.assert_curves_ok(
            ['hazard_curve-mean_PGA.csv', 'hazard_curve-mean_SA(0.2).csv',
             'hazard_map-mean.csv'], case_13.__file__, delta=1E-5)

        # test recomputing the hazard maps
        self.run_calc(
            case_13.__file__, 'job.ini', exports='csv',
            hazard_calculation_id=str(self.calc.datastore.calc_id),
            gsim_logic_tree_file='', source_model_logic_tree_file='')
        [fname] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname,
                              delta=1E-5)

        csv = general.gettemp(
            text_table(view('extreme_sites', self.calc.datastore)))
        self.assertEqualFiles('expected/extreme_sites.rst', csv)

        # test extract/hcurves/rlz-0, used by the npz exports
        haz = vars(extract(self.calc.datastore, 'hcurves'))
        self.assertEqual(sorted(haz), ['_extra', 'all', 'investigation_time'])
        self.assertEqual(
            haz['all'].dtype.names, ('lon', 'lat', 'depth', 'mean'))
        array = haz['all']['mean']
        self.assertEqual(array.dtype.names, ('PGA', 'SA(0.2)'))
        self.assertEqual(array['PGA'].dtype.names,
                         ('0.005', '0.007', '0.0098', '0.0137', '0.0192',
                          '0.0269', '0.0376', '0.0527', '0.0738', '0.103',
                          '0.145', '0.203', '0.284'))

    def test_case_14(self):
        # test classical with 2 gsims and 1 sample
        self.assert_curves_ok(['hazard_curve-rlz-000_PGA.csv'],
                              case_14.__file__)

    def test_case_15(self):
        # this is a case with both splittable and unsplittable sources
        self.assert_curves_ok('''\
hazard_curve-max-PGA.csv,
hazard_curve-mean-PGA.csv
hazard_curve-std-PGA.csv
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
        self.assertEqual(arr['mean'].dtype.names, ('PGA',))
        [fname] = export(('uhs', 'npz'), self.calc.datastore)
        arr = numpy.load(fname)['all']
        self.assertEqual(arr['mean'].dtype.names,
                         ('0.010000', '0.100000', '0.200000'))

        # check deserialization of source_model_lt
        r0, r1, r2 = self.calc.datastore['full_lt/source_model_lt']
        self.assertEqual(repr(r0),
                         "<Realization #0 ['source_model_1.xml', None], "
                         "path=SM1~., weight=0.5>")
        self.assertEqual(repr(r1), "<Realization #1 ['source_model_2.xml', "
                         "(3.2, 0.8)], path=SM2~a3pt2b0pt8, "
                         "weight=0.25>")
        self.assertEqual(repr(r2), "<Realization #2 ['source_model_2.xml', "
                         "(3.0, 1.0)], path=SM2~a3b1, weight=0.25>")

    def test_case_16(self):   # sampling
        with unittest.mock.patch.dict(config.memory, limit=240):
            self.assert_curves_ok(
                ['hazard_curve-mean.csv',
                 'quantile_curve-0.1.csv',
                 'quantile_curve-0.9.csv'],
                case_16.__file__)

        # test that the single realization export fails because
        # individual_rlzs was false
        with self.assertRaises(KeyError) as ctx:
            export(('hcurves/rlz-3', 'csv'), self.calc.datastore)
        self.assertIn('hcurves-rlzs', str(ctx.exception))

    def test_case_17(self):  # oversampling
        # this is a test with 4 sources A and B with the same ID
        # sources A's are false duplicates, while the B's are true duplicates
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_2.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv'],
            case_17.__file__)
        ids = decode(self.calc.datastore['source_info']['source_id'])
        numpy.testing.assert_equal(ids, ['A;0', 'A;1', 'B'])

    def test_case_18(self):  # GMPEtable, PointMSR, 3 hypodepths
        self.run_calc(case_18.__file__, 'job.ini',
                      calculation_mode='preclassical')
        hc_id = str(self.calc.datastore.calc_id)
        # check also that I can start from preclassical with GMPETables
        self.assert_curves_ok(
            ['hazard_curve-mean_PGA.csv',
             'hazard_curve-mean_SA(0.2).csv',
             'hazard_curve-mean_SA(1.0).csv',
             'hazard_map-mean.csv',
             'hazard_uhs-mean.csv'],
            case_18.__file__,
            kind='stats', delta=1E-7, hazard_calculation_id=hc_id)
        [fname] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/realizations.csv', fname)
        self.calc.datastore.close()
        self.calc.datastore.open('r')

        # check exporting a single realization in CSV and XML
        [fname] = export(('uhs/rlz-001', 'csv'),  self.calc.datastore)
        self.assertEqualFiles('expected/uhs-rlz-1.csv', fname)
        [fname] = export(('uhs/rlz-001', 'xml'),  self.calc.datastore)
        self.assertEqualFiles('expected/uhs-rlz-1.xml', fname)

        # extracting hmaps
        hmaps = extract(self.calc.datastore, 'hmaps')['all']['mean']
        self.assertEqual(hmaps.dtype.names, ('PGA', 'SA(0.2)', 'SA(1.0)'))

    def test_case_19(self):
        # test for AvgGMPE
        self.assert_curves_ok([
            'hazard_curve-mean_PGA.csv',
            'hazard_curve-mean_SA(0.1).csv',
            'hazard_curve-mean_SA(0.15).csv',
        ], case_19.__file__, delta=1E-5)

    def test_case_20(self):
        # Source geometry enumeration, apply_to_sources
        self.assert_curves_ok([
            'hazard_curve-mean-PGA.csv',
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
        # there are 3 sources x 12 sm_rlzs
        sgs = self.calc.csm.src_groups  # 7 source groups with 1 source each
        self.assertEqual(len(sgs), 7)
        dupl = sum(len(sg.sources[0].trt_smrs) - 1 for sg in sgs)
        self.assertEqual(dupl, 29)  # there are 29 duplicated sources

        # another way to look at the duplicated sources; protects against
        # future refactorings breaking the pandas readability of source_info
        df = self.calc.datastore.read_df('source_info', 'source_id')
        numpy.testing.assert_equal(
            decode(list(df.index)),
            ['CHAR1;0', 'CHAR1;1', 'CHAR1;2', 'COMFLT1;0', 'COMFLT1;1',
             'SFLT1;0', 'SFLT1;1'])

        # check pandas readability of hcurves-rlzs and hcurves-stats
        df = self.calc.datastore.read_df('hcurves-rlzs', 'lvl')
        self.assertEqual(list(df.columns),
                         ['site_id', 'rlz_id', 'imt', 'value'])
        df = self.calc.datastore.read_df('hcurves-stats', 'lvl')
        self.assertEqual(list(df.columns),
                         ['site_id', 'stat', 'imt', 'value'])

    def test_case_21(self):
        # Simple fault dip and MFD enumeration
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

    def test_case_22(self):  # crossing date line calculation for Alaska
        # this also tests the splitting of the source model in two files
        self.assert_curves_ok([
            '/hazard_curve-mean-PGA.csv', 'hazard_curve-mean-SA(0.1)',
            'hazard_curve-mean-SA(0.2).csv', 'hazard_curve-mean-SA(0.5).csv',
            'hazard_curve-mean-SA(1.0).csv', 'hazard_curve-mean-SA(2.0).csv',
        ], case_22.__file__, delta=1E-6)

    def test_case_23(self):  # filtering away on TRT
        self.assert_curves_ok(['hazard_curve.csv'],
                              case_23.__file__, delta=1e-5)
        attrs = dict(self.calc.datastore['/'].attrs)
        self.assertIn('checksum32', attrs)
        self.assertIn('input_size', attrs)

    def test_case_24(self):  # UHS
        # this is a case with rjb, an hypocenter distribution, and collapse
        self.assert_curves_ok([
            'hazard_curve-PGA.csv', 'hazard_curve-PGV.csv',
            'hazard_curve-SA(0.025).csv', 'hazard_curve-SA(0.05).csv',
            'hazard_curve-SA(0.1).csv', 'hazard_curve-SA(0.2).csv',
            'hazard_curve-SA(0.5).csv', 'hazard_curve-SA(1.0).csv',
            'hazard_curve-SA(2.0).csv', 'hazard_uhs.csv'],
                              case_24.__file__, delta=1E-3)
        total = sum(src.num_ruptures for src in self.calc.csm.get_sources())
        self.assertEqual(total, 780)  # 260 x 3; 2 sites => 1560 contexts
        self.assertEqual(len(self.calc.datastore['rup/mag']), 1560)
        numpy.testing.assert_equal(self.calc.cfactor, [502, 1560, 5])
        # test that the number of ruptures is at max 1/3 of the the total
        # due to the collapsing of the hypocenters (rjb is depth-independent)

    def test_case_25(self):  # negative depths
        self.assert_curves_ok(['hazard_curve-smltp_b1-gsimltp_b1.csv'],
                              case_25.__file__)

    def test_case_26(self):  # split YoungsCoppersmith1985MFD
        self.assert_curves_ok(['hazard_curve-rlz-000.csv'], case_26.__file__)

    def test_case_27(self):  # Nankai mutex model
        self.assert_curves_ok(['hazard_curve.csv'], case_27.__file__,
                              delta=1E-5)
        # make sure probs_occur are stored as expected
        probs_occur = self.calc.datastore['rup/probs_occur'][:]
        tot_probs_occur = sum(len(po) for po in probs_occur)
        self.assertEqual(tot_probs_occur, 4)  # 2 x 2

        # make sure the disaggregation works
        hc_id = str(self.calc.datastore.calc_id)
        self.run_calc(case_27.__file__, 'job.ini',
                      hazard_calculation_id=hc_id,
                      calculation_mode='disaggregation',
                      truncation_level="3",
                      poes_disagg="0.02",
                      mag_bin_width="0.1",
                      distance_bin_width="10.0",
                      coordinate_bin_width="1.0",
                      num_epsilon_bins="6")

    def test_case_28(self):  # North Africa
        # MultiPointSource with modify MFD logic tree
        out = self.run_calc(case_28.__file__, 'job.ini', exports='csv')
        for f in out['uhs', 'csv']:
            self.assertEqualFiles('expected/' + strip_calc_id(f), f)

        # checking that source_info is stored correctly
        info = self.calc.datastore['source_info'][:]
        ae(info['source_id'], [b'21;0', b'21;1', b'22'])
        ae(info['grp_id'], [0, 1, 2])
        ae(info['weight'] > 0, [True, True, True])
        ae(info['trti'], [0, 0, 1])

    def test_case_29(self):  # non parametric source with 2 KiteSurfaces
        check = False

        # first test that the exported ruptures can be re-imported
        self.run_calc(case_29.__file__, 'job.ini',
                      calculation_mode='event_based',
                      ses_per_logic_tree_path='10')
        csv = extract(self.calc.datastore, 'ruptures').array
        rups = get_ruptures(general.gettemp(csv))
        self.assertEqual(len(rups), 1)

        # check what QGIS will be seeing
        aw = extract(self.calc.datastore, 'rupture_info')
        poly = gzip.decompress(aw.boundaries).decode('ascii')
        expected = '''POLYGON((0.17961 0.00000, 0.13492 0.00000, 0.08980 0.00000, 0.04512 0.00000, 0.00000 0.00000, 0.00000 0.04006, 0.00000 0.08013, 0.00000 0.12019, 0.00000 0.16025, 0.00000 0.20032, 0.00000 0.24038, 0.00000 0.28045, 0.04512 0.28045, 0.08980 0.28045, 0.13492 0.28045, 0.17961 0.28045, 0.17961 0.24038, 0.17961 0.20032, 0.17961 0.16025, 0.17961 0.12019, 0.17961 0.08013, 0.17961 0.04006, 0.17961 0.00000, 0.00000 0.10000, 0.04512 0.10000, 0.08980 0.10000, 0.13492 0.10000, 0.17961 0.10000, 0.17961 0.14006, 0.17961 0.18013, 0.17961 0.22019, 0.17961 0.26025, 0.17961 0.30032, 0.17961 0.34038, 0.17961 0.38045, 0.13492 0.38045, 0.08980 0.38045, 0.04512 0.38045, 0.00000 0.38045, 0.00000 0.34038, 0.00000 0.30032, 0.00000 0.26025, 0.00000 0.22019, 0.00000 0.18013, 0.00000 0.14006, 0.00000 0.10000))'''
        self.assertEqual(poly, expected)

        # This is for checking purposes. It creates a .txt file that can be
        # read with QGIS
        if check:
            import pandas as pd
            df = pd.DataFrame({'geometry': [poly, expected]})
            fname = general.gettemp(suffix='.csv')
            print('Saving %s' % fname)
            df.to_csv(fname)

        # then perform a classical calculation
        self.assert_curves_ok(['hazard_curve-PGA.csv'], case_29.__file__)

    def test_case_30(self):
        # point on the international data line
        # this is also a test with IMT-dependent weights
        if NOT_DARWIN:  # broken on macOS
            self.assert_curves_ok(['hazard_curve-PGA.csv',
                                   'hazard_curve-SA(1.0).csv'],
                                  case_30.__file__)

    def test_case_30_sampling(self):
        # IMT-dependent weights with sampling by cheating
        self.assert_curves_ok(
            ['hcurve-PGA.csv', 'hcurve-SA(1.0).csv'],
            case_30.__file__, number_of_logic_tree_samples='10', delta=1E-5)

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
        # test with advanced applyToSources and disordered gsim_logic_tree
        self.run_calc(case_36.__file__, 'job.ini')
        hc_id = str(self.calc.datastore.calc_id)
        self.run_calc(case_36.__file__, 'job.ini', hazard_calculation_id=hc_id,
                      calculation_mode='classical')
        self.assertEqual(self.calc.R, 9)  # there are 9 realizations

        tbl = general.gettemp(text_table(view('rlz:8', self.calc.datastore)))
        self.assertEqualFiles('expected/show-rlz8.org', tbl)

    def test_case_37(self):
        # Christchurch
        self.assert_curves_ok(["hazard_curve-mean-PGA.csv",
                               "quantile_curve-0.16-PGA.csv",
                               "quantile_curve-0.5-PGA.csv",
                               "quantile_curve-0.84-PGA.csv"],
                              case_37.__file__)

    def test_case_38(self):
        # BC Hydro GMPEs with epistemic adjustments
        self.assert_curves_ok(["hazard_curve-mean-PGA.csv",
                               "hazard_uhs-mean.csv"],
                              case_38.__file__)

    def test_case_39(self):
        # 0-IMT-weights, pointsource_distance=0 and iruptures collapsing
        self.assert_curves_ok([
            'hazard_curve-mean-PGA.csv', 'hazard_curve-mean-SA(0.1).csv',
            'hazard_curve-mean-SA(0.5).csv', 'hazard_curve-mean-SA(2.0).csv',
            'hazard_map-mean.csv'], case_39.__file__, delta=2E-5)

    def test_case_40(self):
        # NGA East
        self.assert_curves_ok([
            'hazard_curve-mean-PGV.csv', 'hazard_map-mean.csv'],
                              case_40.__file__, delta=1E-6)

        # checking fullreport can be exported, see https://
        # groups.google.com/g/openquake-users/c/m5vH4rGMWNc/m/8bcBexXNAQAJ
        [fname] = export(('fullreport', 'rst'), self.calc.datastore)

    def test_case_41(self):
        # SERA Site Amplification Models including EC8 Site Classes and Geology
        self.assert_curves_ok(["hazard_curve-mean-PGA.csv",
                               "hazard_curve-mean-SA(1.0).csv"],
                              case_41.__file__)

    def test_case_42(self):
        # split/filter a long complex fault source with maxdist=1000 km
        self.assert_curves_ok(["hazard_curve-mean-PGA.csv",
                               "hazard_map-mean-PGA.csv"], case_42.__file__)

        # check pandas readability of hmaps-stats
        df = self.calc.datastore.read_df('hmaps-stats', 'site_id',
                                         dict(imt='PGA', stat='mean'))
        self.assertEqual(list(df.columns), ['stat', 'imt', 'poe', 'value'])

    def test_case_43(self):
        # this is a test for pointsource_distance and ps_grid_spacing
        # it also checks running a classical after a preclassical
        self.run_calc(case_43.__file__, 'job.ini',
                      calculation_mode='preclassical', concurrent_tasks='4')
        hc_id = str(self.calc.datastore.calc_id)
        self.run_calc(case_43.__file__, 'job.ini',
                      hazard_calculation_id=hc_id)
        data = self.calc.datastore.read_df('source_data')
        self.assertGreater(data.nrupts.sum(), 0)
        [fname] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles("expected/hazard_curve-mean-PGA.csv", fname)
        [fname] = export(('hmaps/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles("expected/hazard_map-mean-PGA.csv", fname)

        # check CollapsedPointSources in source_info
        info = self.calc.datastore.read_df('source_info')
        source_ids = decode(list(info.source_id))
        num_cps = sum(1 for s in source_ids if s.startswith('cps-'))
        self.assertEqual(num_cps, 163)

    def test_case_44(self):
        # this is a test for shift_hypo. We computed independently the results
        # using the same input and a simpler calculator implemented in a
        # jupyter notebook
        self.assert_curves_ok(["hc-shift-hypo-PGA.csv"], case_44.__file__,
                              shift_hypo='true')
        self.assert_curves_ok(["hazard_curve-mean-PGA.csv"], case_44.__file__,
                              shift_hypo='false')

    def test_case_45(self):
        # this is a test for MMI with disagg_by_src and sampling
        self.assert_curves_ok(["hazard_curve-mean-MMI.csv"], case_45.__file__)

    def test_case_46(self):
        # SMLT with applyToBranches
        self.assert_curves_ok(["hazard_curve-mean.csv"], case_46.__file__,
                              delta=1E-6)

    def test_case_47(self):
        # Mixture Model for Sigma using PEER (2018) Test Case 2.5b
        self.assert_curves_ok(["hazard_curve-rlz-000-PGA.csv",
                               "hazard_curve-rlz-001-PGA.csv"],
                              case_47.__file__, delta=1E-5)

    def test_case_48(self):
        # pointsource_distance effects on a simple point source.
        # This is case with 10 magnitudes and 2 hypodepths.
        # The maximum_distance is 110 km and the pointsource_distance 50 km.
        # Originally the distances weew was chosen very carefully, so that
        # after the approximation 3 ruptures got distances around 111 km and
        # were discarded even if their true distances were around 109 km!
        self.run_calc(case_48.__file__, 'job.ini')
        # 20 exact rrup distances for site 0 and site 1 respectively
        expect = numpy.array([[54.3, 109.8],
                             [54.1, 109.7],
                             [53.9, 109.4],
                             [53.7, 109.3],
                             [53.3, 108.9],
                             [53.3, 108.8],
                             [52.7, 108.3],
                             [52.7, 108.2],
                             [52.0, 107.5],
                             [51.9, 107.5],
                             [50.5, 106.1],
                             [50.4, 106.0],
                             [47.8, 103.2],
                             [47.7, 103.1],
                             [43.7, 98.8],
                             [43.6, 98.6],
                             [38.2, 92.0],
                             [38.0, 91.9],
                             [33.0, 82.3],
                             [32.8, 82.2]])
        dst = get_dists(self.calc.datastore)
        aac(dst[0], expect[:, 0], atol=.05)  # site 0
        aac(dst[1], expect[:, 1], atol=.05)  # site 1

        # This test shows in detail what happens to the distances
        # in presence of a pointsource_distance
        self.run_calc(case_48.__file__, 'job.ini', pointsource_distance='50')

        # 15 approx rrup distances for site 0 and site 1 respectively
        approx = numpy.array([[54.2, 109.7],
                              [53.8, 109.3],
                              [53.3, 108.8],
                              [52.7, 108.2],
                              [51.9, 107.5],
                              [50.5, 106.1],
                              [50.4, 106.0],
                              [47.8, 103.2],
                              [47.7, 103.1],
                              [43.7, 98.8],
                              [43.6, 98.6],
                              [38.2, 92.0],
                              [38.0, 91.9],
                              [33.0, 82.3],
                              [32.8, 82.2]])

        # approx distances from site 0 and site 1 respectively
        dst = get_dists(self.calc.datastore)
        aac(dst[0], approx[:, 0], atol=.05)  # site 0
        aac(dst[1], approx[:, 1], atol=.05)  # site 1

    def test_case_49(self):
        # serious test of amplification + uhs
        self.assert_curves_ok(['hcurves-PGA.csv', 'hcurves-SA(0.21).csv',
                               'hcurves-SA(1.057).csv', 'uhs.csv'],
                              case_49.__file__, delta=1E-5)

    def test_case_50(self):
        # serious test of amplification + uhs
        self.assert_curves_ok(['hcurves-PGA.csv', 'hcurves-SA(1.0).csv',
                               'uhs.csv'], case_50.__file__, delta=1E-5)

    def test_case_51(self):
        # Modifiable GMPE
        self.assert_curves_ok(['hcurves-PGA.csv', 'hcurves-SA(0.2).csv',
                               'hcurves-SA(2.0).csv', 'uhs.csv'],
                              case_51.__file__)

    def test_case_52(self):
        # case with 2 GSIM realizations b1 (w=.9) and b2 (w=.1), 10 samples

        # late_weights
        self.run_calc(case_52.__file__, 'job.ini')
        haz = self.calc.datastore['hcurves-stats'][0, 0, 0, 6]
        aac(haz, 0.563831, rtol=1E-6)
        ws = extract(self.calc.datastore, 'weights')
        # sampled 8 times b1 and 2 times b2
        aac(ws, [0.029412, 0.029412, 0.029412, 0.264706, 0.264706, 0.029412,
                 0.029412, 0.264706, 0.029412, 0.029412], rtol=1E-5)

        # early_weights
        self.run_calc(case_52.__file__, 'job.ini',
                      sampling_method='early_weights')
        haz = self.calc.datastore['hcurves-stats'][0, 0, 0, 6]
        aac(haz, 0.56355, rtol=1E-6)
        ws = extract(self.calc.datastore, 'weights')
        aac(ws, [0.1] * 10)  # all equal

        # full enum, rlz-0: 0.554007, rlz-1: 0.601722
        self.run_calc(case_52.__file__, 'job.ini',
                      number_of_logic_tree_samples='0')
        haz = self.calc.datastore['hcurves-stats'][0, 0, 0, 6]
        aac(haz, 0.558779, rtol=1E-6)
        ws = extract(self.calc.datastore, 'weights')
        aac(ws, [0.9, 0.1])

    def test_case_52_bis(self):
        self.run_calc(case_52.__file__, 'job.ini',
                      sampling_method='late_latin')
        haz = self.calc.datastore['hcurves-stats'][0, 0, 0, 6]
        aac(haz, 0.558779, rtol=1E-6)
        ws = extract(self.calc.datastore, 'weights')
        # sampled 5 times b1 and 5 times b2
        aac(ws, [0.18, 0.02, 0.18, 0.18, 0.02, 0.02, 0.02, 0.02, 0.18, 0.18])

        self.run_calc(case_52.__file__, 'job.ini',
                      sampling_method='early_latin')
        haz = self.calc.datastore['hcurves-stats'][0, 0, 0, 6]
        aac(haz, 0.558779, rtol=1E-6)
        ws = extract(self.calc.datastore, 'weights')
        aac(ws, [0.1] * 10)  # equal weights

    def test_case_53(self):
        # Test case with 4-branch scaled backbone logic tree
        # (2 median, 2 stddev adjustments) using the ModifiableGMPE and the
        # period-independent adjustment factors
        self.assert_curves_ok(["hazard_curve-rlz-000-PGA.csv",
                               "hazard_curve-rlz-000-SA(0.5).csv",
                               "hazard_curve-rlz-001-PGA.csv",
                               "hazard_curve-rlz-001-SA(0.5).csv",
                               "hazard_curve-rlz-002-PGA.csv",
                               "hazard_curve-rlz-002-SA(0.5).csv",
                               "hazard_curve-rlz-003-PGA.csv",
                               "hazard_curve-rlz-003-SA(0.5).csv"],
                              case_53.__file__)

    def test_case_54(self):
        # Test case with 4-branch scaled backbone logic tree
        # (2 median, 2 stddev adjustments) using the ModifiableGMPE and the
        # period-dependent adjustment factors
        self.assert_curves_ok(["hazard_curve-rlz-000-PGA.csv",
                               "hazard_curve-rlz-000-SA(0.5).csv",
                               "hazard_curve-rlz-001-PGA.csv",
                               "hazard_curve-rlz-001-SA(0.5).csv",
                               "hazard_curve-rlz-002-PGA.csv",
                               "hazard_curve-rlz-002-SA(0.5).csv",
                               "hazard_curve-rlz-003-PGA.csv",
                               "hazard_curve-rlz-003-SA(0.5).csv"],
                              case_54.__file__)

    def test_case_55(self):
        # test with amplification function == 1
        self.assert_curves_ok(['hazard_curve-mean-PGA.csv'], case_55.__file__)
        hc_id = str(self.calc.datastore.calc_id)

        # test with amplification function == 2
        self.run_calc(case_55.__file__, 'job.ini',
                      hazard_calculation_id=hc_id,
                      amplification_csv='amplification2.csv')
        [fname] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ampl_curve-PGA.csv', fname)

        # test with amplification function == 2 and no levels
        self.run_calc(case_55.__file__, 'job.ini',
                      hazard_calculation_id=hc_id,
                      amplification_csv='amplification2bis.csv')
        [fname] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ampl_curve-bis.csv', fname)

    def test_case_56(self):
        # test with a discardable source model (#2)
        self.run_calc(case_56.__file__, 'job.ini', concurrent_tasks='0')
        [fname] = export(('uhs/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/uhs.csv', fname)

    def test_case_57(self):
        # AvgPoeGMPE
        self.run_calc(case_57.__file__, 'job.ini')
        f1, f2 = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve_PGA.csv', f1)
        self.assertEqualFiles('expected/hcurve_SA.csv', f2)

    def test_case_58(self):
        # Logic tree with SimpleFault uncertainty on geometry and MFD (from
        # slip)

        # First calculation
        self.run_calc(case_58.__file__, 'job.ini')
        f01, f02 = export(('hcurves/rlz-000', 'csv'), self.calc.datastore)
        f03, f04 = export(('hcurves/rlz-003', 'csv'), self.calc.datastore)

        # Second calculation. Same LT structure for case 1 but with only one
        # branch for each branch set
        self.run_calc(case_58.__file__, 'job_case01.ini')
        f11, f12 = export(('hcurves/', 'csv'), self.calc.datastore)

        # Third calculation. In this case we use a source model containing one
        # source with the geometry of branch b22 and slip rate of branch b32
        self.run_calc(case_58.__file__, 'job_case02.ini')
        f21, f22 = export(('hcurves/', 'csv'), self.calc.datastore)

        # First test
        self.assertEqualFiles(f01, f11)

        # Second test
        self.assertEqualFiles(f03, f21)

    def test_case_59(self):
        # test NRCan15SiteTerm
        self.run_calc(case_59.__file__, 'job.ini')
        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f)

    def test_case_60(self):
        # pointsource approx with CampbellBozorgnia2003NSHMP2007
        # the hazard curve MUST be zero; it was not originally
        # due to a wrong dip angle of 0 instead of 90
        self.run_calc(case_60.__file__, 'job.ini')
        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve.csv', f)

    def test_case_61(self):
        # kite fault
        self.run_calc(case_61.__file__, 'job.ini')
        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f, delta=1E-5)

    def test_case_62(self):
        # multisurface with kite faults
        self.run_calc(case_62.__file__, 'job.ini')
        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f, delta=1E-5)

    def test_case_63(self):
        # test soiltype
        self.run_calc(case_63.__file__, 'job.ini')
        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-mean-PGA.csv', f)

    def test_case_64(self):
        # LanzanoEtAl2016 with bas term
        self.run_calc(case_64.__file__, 'job.ini')
        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f)

    def test_case_65(self):
        # running the calculation
        self.run_calc(case_65.__file__, 'job.ini')

        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f, delta=1E-5)

        # reading/writing a multiFaultSource
        csm = self.calc.datastore['_csm']
        tmpname = general.gettemp()
        [src] = csm.src_groups[0].sources
        src.rupture_idxs = [tuple(map(str, idxs)) for idxs in src.rupture_idxs]
        out = write_source_model(tmpname, csm.src_groups)
        self.assertEqual(out[0], tmpname)
        # self.assertEqual(out[1], tmpname[:-4] + '_sections.xml')

        # make sure we are not breaking event_based
        self.run_calc(case_65.__file__, 'job_eb.ini')
        [f] = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', f, delta=1E-5)

        # make sure we are not storing far away ruptures
        r = self.calc.datastore['ruptures'][:]
        [lon] = self.calc.sitecol.lons
        [lat] = self.calc.sitecol.lats
        # check bounding box close to the site
        deltalon = (r['maxlon'] - lon).max()
        deltalat = (r['maxlat'] - lat).max()
        assert deltalon <= .65, deltalon
        assert deltalat <= .49, deltalat
        deltalon = (lon - r['minlon']).max()
        deltalat = (lat - r['minlat']).max()
        assert deltalon <= .35, deltalon
        assert deltalat == .0, deltalat

        # check ruptures.csv
        rups = extract(self.calc.datastore, 'ruptures')
        csv = general.gettemp(rups.array)
        self.assertEqualFiles('expected/full_ruptures.csv', csv, delta=1E-5)

        # check GMFs
        files = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf_data.csv', files[0], delta=1E-4)

    def test_case_66(self):
        # sites_slice
        self.run_calc(case_66.__file__, 'job.ini')  # sites_slice=50:100
        [fname1] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hmap1.csv', fname1, delta=1E-4)
        self.run_calc(case_66.__file__, 'job.ini', sites_slice='0:50')
        [fname2] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hmap2.csv', fname2, delta=1E-4)

    def test_case_67(self):
        # source specific logic tree with the following structure:
        # <CompositeSourceModel
        # grp_id=0 ['10;0']
        # grp_id=1 ['16']
        # grp_id=2 ['11;0']
        # grp_id=3 ['11;1']
        # grp_id=4 ['11;2']
        # grp_id=5 ['10;1']
        # grp_id=6 ['ACC;0']
        # grp_id=7 ['ALS;0']
        # grp_id=8 ['BMS;0']
        # grp_id=9 ['BMS;1']
        # grp_id=10 ['BMS;2']
        # grp_id=11 ['BMS;3']
        # grp_id=12 ['ALS;1']
        # grp_id=13 ['ALS;2']
        # grp_id=14 ['ACC;1']>
        # there are 2x2x3x2x3x4=288 realizations and 2+2+3+2+3+4=16 groups
        # 1 group has no sources so the engine sees 15 groups
        self.run_calc(case_67.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f1)

    def test_case_68(self):
        # expandModel feature
        self.run_calc(case_68.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f1)

    def test_case_69(self):
        # collapse areaSource with no nodal planes/hypocenters
        self.run_calc(case_69.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f1)

    def test_case_70(self):
        # test bug https://github.com/gem/oq-engine/pull/7158
        self.run_calc(case_70.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f1)

    def test_case_71(self):
        # test with oversampling
        # there are 6 potential paths 1A 1B 1C 2A 2B 2C
        # 10 rlzs are being sampled: 1C 1A 1B 1A 1C 1A 2B 2A 2B 2A
        # rlzs_by_g is 135 2 4, 79 68 i.e. 1A*3 1B*1 1C*1, 2A*2 2B*2
        self.run_calc(case_71.__file__, 'job.ini', concurrent_tasks='0')
        [fname] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurves.csv', fname)

        cmakers = contexts.read_cmakers(self.calc.datastore)
        ae(list(cmakers[0].gsims.values()), [[1, 3, 5], [2], [0, 4]])
        ae(list(cmakers[1].gsims.values()), [[7, 9], [6, 8]])
        # there are two slices 0:3 and 3:5 with length 3 and 2 respectively

    def test_case_72(self):
        # reduced USA model
        self.run_calc(case_72.__file__, 'job.ini')
        # rlz#2 corresponds to the CambellBozorgnia2014
        [f] = export(('hcurves/rlz-002', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-002.csv', f)

    def test_case_73(self):
        # test LT
        self.run_calc(case_73.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f1)

    def test_case_74(self):
        # test calculation with EAS
        self.run_calc(case_74.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f1)

    def test_case_75(self):
        # test calculation with multi-fault
        self.run_calc(case_75.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f1)

        # test for duplicated section IDs
        with self.assertRaises(nrml.DuplicatedID):
            self.run_calc(case_75.__file__, 'job.ini',
                          source_model_logic_tree_file='wrong_ssmLT.xml')

    def test_case_76(self):
        # reserving the test number for CanadaSHM6
        """
        self.run_calc(case_76.__file__, 'job.ini')
        branches = self.calc.datastore['full_lt/gsim_lt'].branches
        gsims = [br.gsim for br in branches]
        _poes = self.calc.datastore['_poes'][:, 0, :]  # shape (20, 200)
        for gsim, poes in zip(gsims, _poes):
            csv = general.gettemp('\r\n'.join('%.6f' % poe for poe in poes))
            gsim_str = gsim.__class__.__name__
            if hasattr(gsim, 'submodel'):
                gsim_str += '_' + gsim.submodel
            self.assertEqualFiles('expected/%s.csv' % gsim_str, csv)
        """

    def test_case_77(self):
        # test calculation for modifiable GMPE with original tabular GMM
        self.run_calc(case_77.__file__, 'job.ini')
        [f1] = export(('uhs/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/uhs-mean.csv', f1)

    def test_case_78(self):
        # test calculation for modifiable GMPE with original tabular GMM
        self.run_calc(case_78.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_curve-mean-PGA_NegBinomTest.csv', f1)

    def test_case_79(self):
        # disagg_by_src with semicolon sources
        self.run_calc(case_79.__file__, 'job.ini')

    def test_case_80(self):
        # New Madrid cluster with rup_mutex
        self.run_calc(case_80.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_curve-mean-PGA.csv', f1)

    def test_case_81(self):
        # collapse_level=2
        self.run_calc(case_81.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-mean.csv', f1)
