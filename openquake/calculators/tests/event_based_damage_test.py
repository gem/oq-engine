# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
import sys
import unittest
from types import SimpleNamespace
import numpy
import pandas
from openquake.baselib.general import gettemp
from openquake.qa_tests_data.event_based_damage import (
    case_11, case_12, case_13, case_14, case_15, case_16)
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.getters import NotFound
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.views import view, text_table
from openquake.calculators.checkers import assert_close
from openquake.calculators.event_based_damage import (
    DamageCalculator, fix_totals)


def test_fix_no_damage():
    # tiny negative damages are zeroed, clearly negative ones are an error
    fake = SimpleNamespace(
        R=1, crmodel=SimpleNamespace(damage_states=['no_damage', 'ds1']),
        assetcol={'value-number': numpy.array([10., 10.])})
    prc = SimpleNamespace(num_events=numpy.array([1]))
    fake.dmgcsq = numpy.zeros((1, 2, 1, 1, 2), numpy.float32)  # P,A,R,L,Dc
    fake.dmgcsq[0, 0, 0, 0, 1] = -1E-9
    DamageCalculator._fix_no_damage(fake, prc)
    numpy.testing.assert_equal(fake.dmgcsq[0, 0, 0, 0, 1], 0)

    fake.dmgcsq[0, 0, 0, 0, 1] = -1E-3
    with unittest.TestCase().assertRaises(AssertionError):
        DamageCalculator._fix_no_damage(fake, prc)


def test_fix_totals():
    # two assets (agg_id 0 and 1) and their total (agg_id 2), two loss types
    df = pandas.DataFrame(dict(
        agg_id=[0, 1, 2, 0, 1, 2],
        loss_id=[3, 3, 3, 4, 4, 4],
        non_operational_inter=[1., 1., 0., 0., 1., 0.],
        non_operational=[1., 1., 0., 0., 1., 0.]),
        index=pandas.Index([0] * 6, name='event_id'))
    fix_totals(df)
    # the totals are per loss type: 1+1 for loss 3, 0+1 for loss 4
    expected = [1, 1, 2, 0, 1, 1]
    numpy.testing.assert_equal(df.non_operational_inter.to_numpy(), expected)
    numpy.testing.assert_equal(df.non_operational.to_numpy(), expected)


class EventBasedDamageTestCase(CalculatorTestCase):

    def check_damages(self, f1, f2):
        df = self.calc.datastore.read_df(
            'risk_by_event', ['event_id', 'agg_id', 'loss_id']).sort_index()
        for col in df.columns:
            df[col] = numpy.around(df[col])
        self.assertEqualFiles('expected/' + f1, gettemp(str(df)))
        if 'aggcurves' in self.calc.datastore:
            df = self.calc.datastore.read_df(
                'aggcurves', ['agg_id', 'loss_id']).sort_index()
            for col in df.columns:
                df[col] = numpy.around(df[col])
            self.assertEqualFiles('expected/' + f2, gettemp(str(df)))

    def test_case_11(self):
        # test with double aggregate_by by Catalina
        self.run_calc(case_11.__file__, 'job.ini')

        # check damages-rlzs, sensitive to shapely version
        [f] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=1E-3)

        # check aggcurves, sensitive to shapely version
        [_, f] = export(('aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=2E-3)

    def test_case_12a(self):
        # test event_based_damage, no aggregate_by,
        # discrete_damage_distribution = true
        self.run_calc(case_12.__file__, 'job_a.ini')
        self.check_damages('a_damage_table.txt', 'a_damages.txt')

        # since there are not ruptures, exporting the ruptures is an error
        with self.assertRaises(NotFound):
            export(('ruptures', 'csv'), self.calc.datastore)

    def test_case_12b(self):
        # test event_based_damage, aggregate_by=taxonomy
        self.run_calc(case_12.__file__, 'job_b.ini')
        self.check_damages('b_damage_table.txt', 'b_damages.txt')

    def test_case_12c(self):
        # test event_based_damage, aggregate_by=taxonomy, policy
        self.run_calc(case_12.__file__, 'job_c.ini')
        self.check_damages('c_damage_table.txt', 'c_damages.txt')

        # check aggrisk output
        fnames = export(('aggrisk', 'csv'), self.calc.datastore)
        for f in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=1E-5)

    def test_case_12d(self):
        # test event_based_damage, aggregate_by=id
        self.run_calc(case_12.__file__, 'job_d.ini')
        self.check_damages('d_damage_table.txt', 'd_damages.txt')

    def test_case_13a(self):
        # test event_based_damage, no aggregate_by
        self.run_calc(case_13.__file__, 'job_a.ini')
        [f] = export(('aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=5E-5)

    def test_case_13b(self):
        # test event_based_damage, aggregate_by=taxonomy
        self.run_calc(case_13.__file__, 'job_b.ini')
        self.check_damages('b_damage_table.txt', 'b_damages.txt')

        [f] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=5E-5)

    def test_case_13c(self):
        # test event_based_damage, aggregate_by=taxonomy, policy
        self.run_calc(case_13.__file__, 'job_c.ini')
        self.check_damages('c_damage_table.txt', 'c_damages.txt')

    def test_case_13d(self):
        # test event_based_damage, aggregate_by=id
        self.run_calc(case_13.__file__, 'job_d.ini')
        self.check_damages('d_damage_table.txt', 'd_damages.txt')

    def test_case_14(self):
        # test event_based_damage, aggregate_by=NAME_1
        self.run_calc(case_14.__file__, 'job.ini')
        [_, f] = export(('aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=5E-5)

    @unittest.skipIf(sys.platform == "darwin", "numbers slightly different")
    def test_case_15(self):
        # test full enumeration with both fatalities and losses
        self.run_calc(case_15.__file__, 'job.ini')

        # check damages-stats
        [f] = export(('damages-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_risk-mean.csv', f, delta=5E-5)

        # check aggcurves
        [f] = export(('aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=5E-5)

        # check extract
        dic = vars(extract(self.calc.datastore, 'damages-rlzs'))
        self.assertEqual(
            list(dic),
            ['rlz-000', 'rlz-001', 'rlz-002', 'rlz-003', 'rlz-004', 'extra'])

        # check risk_by_event
        [f] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(f), f, delta=5E-5)

    def test_case_16(self):
        # test sampling with collect_rlzs
        self.run_calc(case_16.__file__, 'job.ini')
        pdd = view('portfolio_dmgdist', self.calc.datastore)
        assert_close(text_table(pdd, ext='org'),
                     os.path.join(self.testdir, 'dmgdist.txt'),
                     rtol=.00012)
