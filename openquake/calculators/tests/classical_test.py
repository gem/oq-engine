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
import os
import gzip
import numpy
from openquake.baselib import parallel, general
from openquake.baselib.python3compat import decode
from openquake.hazardlib import InvalidFile, nrml
from openquake.hazardlib.source.rupture import get_ruptures
from openquake.hazardlib.sourcewriter import write_source_model
from openquake.calculators.views import view, text_table
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.classical import (
    case_01, case_12, case_18, case_22, case_23,
    case_24, case_25, case_26, case_27, case_29, case_32, case_33,
    case_34, case_35, case_37, case_38, case_40, case_41,
    case_42, case_43, case_44, case_47, case_48, case_49,
    case_50, case_51, case_53, case_54, case_55, case_57,
    case_60, case_61, case_62, case_63, case_64, case_65,
    case_66, case_69, case_70, case_72, case_74, case_75, case_76, case_77,
    case_78, case_80, case_81, case_82, case_84)

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

    def test_case_01(self):
        self.assert_curves_ok(
            ['hazard_curve-PGA.csv', 'hazard_curve-SA(0.1).csv'],
            case_01.__file__)

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
            self.run_calc(case_01.__file__, 'job.ini', minimum_magnitude='4.5')
        self.assertIn('All sources were discarded', str(ctx.exception))

    def test_wrong_smlt(self):
        with self.assertRaises(InvalidFile):
            self.run_calc(case_01.__file__, 'job_wrong.ini')

    def test_sa_period_too_big(self):
        imtls = '{"SA(4.1)": [0.1, 0.4, 0.6]}'
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(
                case_01.__file__, 'job.ini',
                intensity_measure_types_and_levels=imtls)
        self.assertEqual(
            'SA(4.1) is out of the period range defined for [SadighEtAl1997]',
            str(ctx.exception))

    def test_case_12(self):
        # test Modified GMPE
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1_b2.csv'],
            case_12.__file__)

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

        # check override_vs30
        sitecol = self.calc.datastore['sitecol']
        aac(sitecol.vs30, [800, 800])
        aac(sitecol.z1pt0, [31.070149, 31.070149], atol=1e-6)
        aac(sitecol.z2pt5, [0.572241, 0.572241], atol=1e-6)

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

    def test_case_57(self):
        # AvgPoeGMPE
        self.run_calc(case_57.__file__, 'job.ini')
        f1, f2 = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve_PGA.csv', f1)
        self.assertEqualFiles('expected/hcurve_SA.csv', f2)

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
        # multiFaultSource with infer_occur_rates=true
        self.run_calc(case_65.__file__, 'job.ini')
        rates = self.calc.datastore['rup/occurrence_rate'][:]
        aac(rates, [0.356675, 0.105361], atol=5e-7)

        [f] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-mean.csv', f, delta=1E-5)

        # reading/writing a multiFaultSource
        csm = self.calc.datastore['_csm']
        tmpname = general.gettemp()
        [src] = csm.src_groups[0].sources
        src.rupture_idxs = [tuple(map(str, idxs)) for idxs in src.rupture_idxs]
        out = write_source_model(tmpname, csm.src_groups)
        self.assertEqual(out[0], tmpname)
        self.assertEqual(out[1], tmpname + '.hdf5')

        # test disaggregation
        hc_str = str(self.calc.datastore.calc_id)
        self.run_calc(
            case_65.__file__, 'job.ini',
            calculation_mode='disaggregation',
            disagg_outputs='Mag',
            disagg_bin_edges='{"mag": [5.6, 6.0, 6.4, 6.8, 7.0, 7.2]}',
            hazard_calculation_id=hc_str)
        dbm = view('disagg:Mag', self.calc.datastore)
        fname = general.gettemp(text_table(dbm, ext='org'))
        self.assertEqualFiles('expected/disagg_by_mag_true.org', fname)

        # multiFaultSource with infer_occur_rates=false
        self.run_calc(
            case_65.__file__, 'job.ini',
            calculation_mode='disaggregation',
            infer_occur_rates='false',
            disagg_outputs='Mag',
            disagg_bin_edges='{"mag": [5.6, 6.0, 6.4, 6.8, 7.0, 7.2]}')
        dbm = view('disagg:Mag', self.calc.datastore)
        fname = general.gettemp(text_table(dbm, ext='org'))
        self.assertEqualFiles('expected/disagg_by_mag_false.org', fname)

    def test_case_66(self):
        # sites_slice
        self.run_calc(case_66.__file__, 'job.ini')  # sites_slice=50:100
        [fname1] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hmap1.csv', fname1, delta=1E-4)
        self.run_calc(case_66.__file__, 'job.ini', sites_slice='0:50')
        [fname2] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hmap2.csv', fname2, delta=1E-4)

        # check that you can specify both a site and a site model and the
        # engine will automatically get the closest site model parameters
        self.run_calc(case_66.__file__, 'job1.ini',
                      calculation_mode='preclassical')
        self.assertEqual(self.calc.sitecol.vs30, [810.])

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

    def test_case_72(self):
        # reduced USA model
        self.run_calc(case_72.__file__, 'job.ini')
        # rlz#2 corresponds to the CambellBozorgnia2014
        [f] = export(('hcurves/rlz-002', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurve-002.csv', f)

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
        # CanadaSHM6 GMPEs
        self.run_calc(case_76.__file__, 'job.ini')
        branches = self.calc.datastore['full_lt/gsim_lt'].branches
        gsims = [br.gsim for br in branches]
        df = self.calc.datastore.read_df('_poes')
        del df['sid']
        L = self.calc.oqparam.imtls.size  # 25 levels x 8 IMTs
        for gid, gsim in enumerate(gsims):
            df_for_gid = df[df.gid == gid]
            poes = numpy.zeros(L)
            poes[df_for_gid.lid] = df_for_gid.poe
            csv = general.gettemp('\r\n'.join('%.6f' % poe for poe in poes))
            gsim_str = gsim.__class__.__name__
            if 'submodel' in gsim._toml:
                gsim_str += '_' + gsim.kwargs['submodel']
            expected_csv = os.path.join(os.path.dirname(os.path.abspath(case_76.__file__)), 'expected/', '%s.csv' % gsim_str)
            with open(expected_csv, 'r') as f:
                expected_poes = numpy.array([float(line.strip()) for line in f])
            for i in range(len(poes)):
                self.assertAlmostEqual(poes[i], expected_poes[i], delta = 0.01)

    def test_case_77(self):
        # test calculation for modifiable GMPE with original tabular GMM
        self.run_calc(case_77.__file__, 'job.ini')
        [f1] = export(('uhs/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/uhs-mean.csv', f1)

    def test_case_78(self):
        # test calculation for modifiable GMPE with original tabular GMM
        # NB: this is using a NegativeBinomialTOM
        self.run_calc(case_78.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_curve-mean-PGA_NegBinomTest.csv', f1)

        # also test disaggregation with NegativeBinomialTOM
        # the model has only 2 ruptures
        hc_str = str(self.calc.datastore.calc_id)
        self.run_calc(
            case_78.__file__, 'job.ini',
            calculation_mode='disaggregation',
            disagg_outputs='Dist',
            disagg_bin_edges='{"dist": [0, 15, 30]}',
            hazard_calculation_id=hc_str)
        dbm = view('disagg:Dist', self.calc.datastore)
        fname = general.gettemp(text_table(dbm, ext='org'))
        self.assertEqualFiles('expected/disagg_by_dist.org', fname)

    def test_case_80(self):
        # New Madrid cluster with rup_mutex
        self.run_calc(case_80.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_curve-mean-PGA.csv', f1)

        # test sampling
        self.run_calc(case_80.__file__, 'job.ini',
                      calculation_mode='event_based',
                      ground_motion_fields='false')
        rups = self.calc.datastore['ruptures'][()]
        tbl = text_table(rups[['source_id', 'n_occ', 'mag']], ext='org')
        self.assertEqualFiles('expected/rups.org', general.gettemp(tbl))

    def test_case_81(self):
        # collapse_level=2
        self.run_calc(case_81.__file__, 'job.ini')
        [f1] = export(('hcurves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-mean.csv', f1)

    def test_case_82(self):
        # two mps, only one should be collapsed and use reqv
        self.run_calc(case_82.__file__, 'job.ini')
        [f1] = export(('rates_by_src', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/rates_by_src.csv', f1)

    def test_case_84(self):
        # three sources are identical except for their source_ids.
        # one is collapsed using reqv, while the other two are specified 
        # as 'not collapsed' in the job file field reqv_ignore_sources
        self.run_calc(case_84.__file__, 'job.ini')
        [f] = export(('rates_by_src', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/rbs.csv', f)
