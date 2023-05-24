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
import numpy
from openquake.hazardlib import InvalidFile
from openquake.baselib.writers import write_csv
from openquake.baselib.general import gettemp
from openquake.qa_tests_data.scenario_damage import (
    case_1, case_1c, case_2, case_3, case_4, case_4b, case_5, case_5a,
    case_6, case_7, case_8, case_9, case_10, case_11, case_12, case_13,
    case_14, case_15, case_16)
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
        [dmg] = extract(self.calc.datastore, 'agg_damages/structural?'
                        'taxonomy=RC&CRESTA=01.1')
        aac([1482., 489., 29.], dmg, atol=1E-4)
        # test no intersection
        dmg = extract(self.calc.datastore, 'agg_damages/structural?'
                      'taxonomy=RM&CRESTA=01.1')
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
        df = self.calc.datastore.read_df('damages-rlzs', 'asset_id')
        self.assertEqual(list(df.columns),
                         ['rlz', 'loss_type', 'dmg_state', 'value'])

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

        return  # TODO: fix avg_losses
        fnames = export(('avg_losses-rlzs', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 2)  # one per realization
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=2E-4)

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
            [0.68279, 0.632278, 0.309294, 0.155964, 0.219674], atol=1E-5)

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
        self.assertEqual(dmg.dmg_1.sum(), 135)
        self.assertEqual(dmg.dmg_2.sum(), 10)
        self.assertEqual(dmg.dmg_3.sum(), 0)
        self.assertEqual(dmg.dmg_4.sum(), 0)

        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk.csv', fname, delta=1E-4)

    def test_case_10(self):
        # test with GMVs = 0 on the sites of the exposure
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(case_10.__file__, 'job.ini')
        self.assertIn('The sites in gmf_data are disjoint', str(ctx.exception))

    def test_case_11(self):
        # secondary perils without secondary simulations
        self.run_calc(case_11.__file__, 'job.ini',
                      secondary_simulations="{}")
        calc1 = self.calc.datastore
        [fname] = export(('risk_by_event', 'csv'), calc1)
        self.assertEqualFiles('expected/risk_by_event_1.csv', fname)

        # secondary perils with secondary simulations
        self.run_calc(case_11.__file__, 'job.ini')
        calc2 = self.calc.datastore
        [fname] = export(('risk_by_event', 'csv'), calc2)
        self.assertEqualFiles('expected/risk_by_event_2.csv', fname)

        # check mean_perils
        fname = gettemp(text_table(view('mean_perils', self.calc.datastore)))
        self.assertEqualFiles('expected/mean_perils.rst', fname)

        # check damages-rlzs
        [fname] = export(('damages-rlzs', 'csv'), calc1)
        self.assertEqualFiles('expected/avg_damages1.csv', fname)
        [fname] = export(('damages-rlzs', 'csv'), calc2)
        self.assertEqualFiles('expected/avg_damages2.csv', fname)

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
        with self.assertRaises(NameError) as ctx:
            self.run_calc(case_14.__file__, 'job.ini')
        self.assertIn(
            "['CR+PC/LDUAL/HBET:8.19/m', 'CR+PC/LDUAL/HBET:8.19/m ']",
            str(ctx.exception))

    def test_case_15(self):
        # infrastructure risk
        self.run_calc(case_15.__file__, 'job.ini')
        nodes = self.calc.datastore.read_df('functional_demand_nodes')
        got = dict(zip(nodes.id, nodes.number))
        expected = {'D1': 36, 'D10': 26, 'D11': 26, 'D12': 25, 'D2': 36,
                    'D3': 36, 'D4': 36, 'D5': 36, 'D6': 36, 'D7': 28,
                    'D8': 28, 'D9': 28}
        self.assertEqual(got, expected)

    def test_case_16(self):
        # inconsistent IDs between fragility and consequence in set_tmap
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(case_16.__file__, 'job.ini')
        self.assertIn("Missing 'UNM/C_LR/GOV2' in", str(ctx.exception))


def losses(aid, alt):
    E = len(alt.event_id.unique())
    losses = numpy.zeros(E, int)
    df = alt.loc[aid]
    losses[df.event_id.to_numpy()] = df.loss.to_numpy()
    return losses
