# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import numpy
from openquake.hazardlib import InvalidFile
from openquake.baselib.writers import write_csv
from openquake.baselib.general import gettemp
from openquake.qa_tests_data.scenario_damage import (
    case_1, case_1c, case_2, case_3, case_4, case_4b, case_5, case_5a,
    case_6, case_7, case_8, case_9, case_10, case_11, case_12, case_13,
    case_14, case_16, case_17, case_18, case_19, case_20, case_22)
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.extract import extract
from openquake.calculators.export import export
from openquake.calculators.views import view, text_table

aac = numpy.testing.assert_allclose


class ScenarioDamageTestCase(CalculatorTestCase):

    def assert_ok(self, pkg, job_ini, exports='csv', kind='damages'):
        test_dir = os.path.dirname(pkg.__file__)
        out = self.run_calc(test_dir, job_ini, exports=exports)
        try:
            got = out['%s-rlzs' % kind, exports]
        except KeyError:  # in case_5a
            got = out['%s-stats' % kind, exports]
        expected_dir = os.path.join(test_dir, 'expected')
        expected = sorted(f for f in os.listdir(expected_dir)
                          if f.endswith(exports) and 'by_taxon' not in f)
        self.assertEqual(len(got), len(expected))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual, delta=1E-5)

    def test_case_1(self):
        # test with a single event and a missing tag
        self.assert_ok(case_1, 'job_risk.ini')
        view('num_units', self.calc.datastore)

        # test agg_damages, 1 realization x 3 damage states
        # checking that passing a fake loss type works,
        # for compatibility with the past
        dmg = extract(self.calc.datastore,
                      'agg_damages/structural?taxonomy=RC&CRESTA=01.1')
        aac([[1482., 489., 29.]], dmg, atol=1E-4)

        # test no intersection
        dmg = extract(self.calc.datastore, 'agg_damages/structural?taxonomy=RM&CRESTA=01.1')
        self.assertEqual(dmg.shape, ())

        # missing fragility functions
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_1.__file__, 'job_bad.ini')
        self.assertIn('Missing fragility files', str(ctx.exception))

    def test_case_1c(self):
        # this is a case with more hazard sites than exposure sites
        # it is also a case with asset numbers > 65535 and < 1
        # and also a case with modal_damage_state
        test_dir = os.path.dirname(case_1c.__file__)
        self.run_calc(test_dir, 'job.ini', exports='csv')

        # check damages-rlzs
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        # check risk_by_event
        [fname] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=1E-5)

        # check agg_damages extraction
        total = extract(self.calc.datastore, 'agg_damages/structural')

        aac(total, [[27652.219, 28132.8, 9511.933, 2870.9312, 11832.913]],
            atol=.1)

        # check extract gmf_data works with a filtered site collection
        gmf_data = dict(extract(self.calc.datastore, 'gmf_data'))
        self.assertEqual(gmf_data['rlz-000'].shape, (2,))  # 2 assets

        pd = view('portfolio_damage', self.calc.datastore)
        self.assertEqual(pd.dtype.names, (
            'structural-no_damage', 'structural-slight', 'structural-moderate',
            'structural-extreme', 'structural-complete'))


    def test_case_2(self):
        self.assert_ok(case_2, 'job_risk.ini')

    def test_case_3(self):
        self.assert_ok(case_3, 'job_risk.ini')

    def test_case_4(self):
        self.assert_ok(case_4, 'job_haz.ini,job_risk.ini')

    def test_case_4b(self):
        # sensitive to shapely version
        self.run_calc(case_4b.__file__, 'job_haz.ini,job_risk.ini')

        [fname] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=5E-4)

        aw = extract(self.calc.datastore, 'damages-stats')
        self.assertEqual(aw.mean.dtype.names,
                         ('id', 'taxonomy', 'lon', 'lat', 'contents-no_damage',
                          'contents-ds1', 'contents-ds2', 'contents-ds3',
                          'contents-ds4', 'contents-losses',
                          'nonstructural-no_damage', 'nonstructural-ds1',
                          'nonstructural-ds2', 'nonstructural-ds3',
                          'nonstructural-ds4', 'nonstructural-losses',
                          'structural-no_damage', 'structural-ds1', 'structural-ds2',
                          'structural-ds3', 'structural-ds4', 'structural-losses'))

    def test_wrong_gsim_lt(self):
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(os.path.dirname(case_4b.__file__), 'job_err.ini')
        self.assertIn('must contain a single branchset, found 2!',
                      str(ctx.exception))

    def test_case_5(self):
        # this is a test for the rupture filtering
        # NB: the exposure file is imported twice on purpose, to make
        # sure that nothing changes; the case is very tricky since the
        # hazard site collection is filtered by the maximum_distance,
        # there is no region_constraint in hazard and there is in risk
        self.assert_ok(case_5, 'job_haz.ini,job_risk.ini')

    def test_case_5a(self):
        # this is a case with two gsims and one asset
        self.assert_ok(case_5a, 'job_haz.ini,job_risk.ini')
        dmg = extract(self.calc.datastore, 'agg_damages/structural?taxonomy=*')
        self.assertEqual(dmg.array.shape, (1, 2, 5))  # (T, R, D)
        aac(dmg.array[0].sum(axis=0),
            [0.68951, 0.623331, 0.305033, 0.155678, 0.22645], atol=1E-5)

    def test_case_6(self):
        # this is a case with 5 assets on the same point
        self.assert_ok(case_6, 'job_h.ini,job_r.ini')
        dmg = extract(self.calc.datastore, 'agg_damages/structural?taxonomy=*')
        tmpname = write_csv(None, dmg, fmt='%.5E')  # (T, R, D) == (5, 1, 5)
        self.assertEqualFiles('expected/dmg_by_taxon.csv', tmpname,
                              delta=1E-5)

    def test_case_7(self):
        # this is a case with three loss types
        self.assert_ok(case_7, 'job_h.ini,job_r.ini', exports='csv')

        # just run the npz export
        [npz] = export(('damages-rlzs', 'npz'), self.calc.datastore)
        self.assertEqual(strip_calc_id(npz), 'damages-rlzs.npz')

        # check the risk_by_event is readable by pandas
        K = self.calc.datastore.get_attr('risk_by_event', 'K')
        df = self.calc.datastore.read_df(
            'risk_by_event', ['event_id', 'loss_id', 'agg_id'],
            dict(agg_id=K))
        self.assertEqual(len(df), 300)
        self.assertEqual(len(df[df.dmg_1 > 0]), 72)  # only 72/300 are nonzero

    def test_case_8(self):
        # case with a shakemap
        self.run_calc(case_8.__file__, 'prejob.ini')
        self.run_calc(case_8.__file__, 'job.ini',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))
        [fname] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/risk_by_event.csv', fname)

    def test_case_9(self):
        # case with noDamageLimit==0 that had NaNs in the past
        self.run_calc(case_9.__file__, 'job.ini')

        [fname] = export(('damages-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damages.csv', fname, delta=2E-5)

        # check risk_by_event
        K = self.calc.datastore.get_attr('risk_by_event', 'K')
        df = self.calc.datastore.read_df('risk_by_event', 'event_id',
                                         {'agg_id': K})
        dmg = df.loc[1937]  # damage caused by the event 1937
        self.assertEqual(dmg.dmg_1.sum(), 133)
        self.assertEqual(dmg.dmg_2.sum(), 84)
        self.assertEqual(dmg.dmg_3.sum(), 21)
        self.assertEqual(dmg.dmg_4.sum(), 22)

        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk.csv', fname, delta=1E-4)

    def test_case_10(self):
        # test with GMVs = 0 on the sites of the exposure
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(case_10.__file__, 'job.ini')
        self.assertIn('The sites in gmf_data are disjoint', str(ctx.exception))

    def test_case_11(self):
        # secondary perils
        self.run_calc(case_11.__file__, 'job.ini')
        calc1 = self.calc.datastore
        [fname] = export(('risk_by_event', 'csv'), calc1)
        self.assertEqualFiles('expected/risk_by_event_1.csv', fname)

        # check mean_perils
        fname = gettemp(text_table(view('mean_perils', self.calc.datastore)))
        self.assertEqualFiles('expected/mean_perils.rst', fname)

        # check damages-rlzs
        [fname] = export(('damages-rlzs', 'csv'), calc1)
        self.assertEqualFiles('expected/avg_damages1.csv', fname)

    def test_case_12(self):
        # secondary perils from rupture
        self.run_calc(case_12.__file__, 'job.ini')
        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk.csv', fname)
        hc_id = str(self.calc.datastore.calc_id)

        # same with discrete damage distribution
        self.run_calc(case_12.__file__, 'job.ini',
                      discrete_damage_distribution='true',
                      hazard_calculation_id=hc_id)
        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk2.csv', fname)

    def test_case_13(self):
        # 3 realizations and consequences
        self.run_calc(case_13.__file__, 'job.ini')
        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk.csv', fname)
        [fname] = export(('aggrisk-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk-stats.csv', fname)

    def test_case_14(self):
        # inconsistent IDs between fragility and consequence
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_14.__file__, 'job_wrong.ini')
        self.assertIn(
            "{'CR+PC/LDUAL/HBET:8.19/m'} not in the CompositeRiskModel",
            str(ctx.exception))

    def test_case_16(self):
        # inconsistent IDs between fragility and consequence in set_tmap
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_16.__file__, 'job.ini')
        self.assertIn("{'MUR-CLBRS-LWAL-HBET-1;2/GOV2'} are in the exposure "
                      "but not in the taxonomy mapping ", str(ctx.exception))

    def test_case_17_no_time_event(self):
        out = self.run_calc(
            case_17.__file__,  'job_no_time_event.ini', exports='csv')
        [fname] = out[('aggrisk', 'csv')]
        self.assertEqualFiles('expected/aggrisk-_no_time_event.csv', fname)
        [fname] = out[('damages-rlzs', 'csv')]
        self.assertEqualFiles(
            'expected/avg_damages-rlz-000_no_time_event.csv', fname)

    def test_case_17_time_event_day(self):
        out = self.run_calc(
            case_17.__file__,  'job_time_event_day.ini', exports='csv')
        [fname] = out[('aggrisk', 'csv')]
        self.assertEqualFiles('expected/aggrisk-_time_event_day.csv', fname)
        [fname] = out[('damages-rlzs', 'csv')]
        self.assertEqualFiles(
            'expected/avg_damages-rlz-000_time_event_day.csv', fname)

    def test_case_18(self):
        # Exposure model mapping 2 oq fields to the same column
        out = self.run_calc(case_18.__file__, 'job.ini', exports='csv')
        [fname] = out[('aggrisk', 'csv')]
        self.assertEqualFiles('expected/aggrisk.csv', fname)

    def test_case_19(self):
        # conditioned GMFs with assets on top of a station
        out = self.run_calc(case_19.__file__, 'job.ini', exports='csv')
        [fname] = out[('aggrisk', 'csv')]
        self.assertEqualFiles('expected/aggrisk.csv', fname)

    def test_case_20(self):
        # conditioned GMFs with nontrivial site parameter associations
        out = self.run_calc(case_20.__file__, 'job.ini', exports='csv')
        [fname] = out[('aggrisk', 'csv')]
        self.assertEqualFiles('expected/aggrisk.csv', fname)

    def test_case_22(self):
        # losses with liquefaction and landslides
        self.run_calc(case_22.__file__, 'job_h.ini')

        # checking avg_gmf
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf.csv', f)

        # doing the risk
        hc_id = str(self.calc.datastore.calc_id)
        out = self.run_calc(case_22.__file__, 'job_r.ini',
                            hazard_calculation_id=hc_id, exports='csv')
        [dmg_csv] = out[('damages-rlzs', 'csv')]
        self.assertEqualFiles('expected/dmg.csv', dmg_csv,
                              delta=4E-5)
        [agg_csv] = out[('aggrisk', 'csv')]
        self.assertEqualFiles('expected/aggrisk.csv', agg_csv)


def losses(aid, alt):
    E = len(alt.event_id.unique())
    losses = numpy.zeros(E, int)
    df = alt.loc[aid]
    losses[df.event_id.to_numpy()] = df.loss.to_numpy()
    return losses
