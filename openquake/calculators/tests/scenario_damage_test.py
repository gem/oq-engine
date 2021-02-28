# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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

from openquake.baselib.hdf5 import read_csv
from openquake.baselib.general import gettemp
from openquake.hazardlib import InvalidFile
from openquake.commonlib.writers import write_csv
from openquake.qa_tests_data.scenario_damage import (
    case_1, case_1c, case_2, case_3, case_4, case_4b, case_5, case_5a,
    case_6, case_7, case_8, case_9, case_10, case_11)
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.extract import extract
from openquake.calculators.export import export
from openquake.calculators.views import view, rst_table

aac = numpy.testing.assert_allclose


class ScenarioDamageTestCase(CalculatorTestCase):
    def assert_ok(self, pkg, job_ini, exports='csv', kind='damages'):
        test_dir = os.path.dirname(pkg.__file__)
        out = self.run_calc(test_dir, job_ini, exports=exports,
                            collapse_threshold='0')
        try:
            got = out['%s-rlzs' % kind, exports]
        except KeyError:
            got = out['%s-stats' % kind, exports]
        expected_dir = os.path.join(test_dir, 'expected')
        expected = sorted(f for f in os.listdir(expected_dir)
                          if f.endswith(exports) and 'by_taxon' not in f)
        self.assertEqual(len(got), len(expected))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual)

    def test_case_1(self):
        # test with a single event and a missing tag
        self.assert_ok(case_1, 'job_risk.ini')
        got = view('num_units', self.calc.datastore)
        self.assertEqual('''\
======== =========
taxonomy num_units
======== =========
RC       2_000    
RM       4_000    
*ALL*    6_000    
======== =========''', got)

        # test agg_damages, 1 realization x 3 damage states
        [dmg] = extract(self.calc.datastore, 'agg_damages/structural?'
                        'taxonomy=RC&CRESTA=01.1')
        aac([1528., 444., 28.], dmg, atol=1E-4)
        # test no intersection
        dmg = extract(self.calc.datastore, 'agg_damages/structural?'
                      'taxonomy=RM&CRESTA=01.1')
        self.assertEqual(dmg.shape, ())

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

        # check dmg_by_event
        [fname] = export(('dmg_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        # check agg_damages extraction
        total = extract(self.calc.datastore, 'agg_damages/structural')
        aac(total, [[37312.8, 30846.1, 4869.6, 1271.5, 5700.7]], atol=.1)

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
        self.run_calc(case_4b.__file__, 'job_haz.ini,job_risk.ini')

        [fname] = export(('dmg_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        [fname] = export(('agg_loss_table', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=5E-6)

        fnames = export(('avg_losses-rlzs', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 2)  # one per realization
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=5E-6)

        df = view('portfolio_damage_error', self.calc.datastore)
        fname = gettemp(rst_table(df))
        self.assertEqualFiles('expected/portfolio_damage.rst', fname)

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
        tmpname = write_csv(None, dmg)  # shape (T, R, D) == (1, 2, 5)
        self.assertEqualFiles('expected/dmg_by_taxon.csv', tmpname)

    def test_case_6(self):
        # this is a case with 5 assets on the same point
        self.assert_ok(case_6, 'job_h.ini,job_r.ini')
        dmg = extract(self.calc.datastore, 'agg_damages/structural?taxonomy=*')
        tmpname = write_csv(None, dmg)  # shape (T, R, D) == (5, 1, 5)
        self.assertEqualFiles('expected/dmg_by_taxon.csv', tmpname)

    def test_case_7(self):
        # this is a case with three loss types
        self.assert_ok(case_7, 'job_h.ini,job_r.ini', exports='csv')

        # just run the npz export
        [npz] = export(('damages-rlzs', 'npz'), self.calc.datastore)
        self.assertEqual(strip_calc_id(npz), 'damages-rlzs.npz')

        # check dd_data is readable by pandas
        df = self.calc.datastore.read_df('dd_data', ['aid', 'eid', 'lid'])
        self.assertEqual(len(df), 221)
        self.assertEqual(len(df[df.ds1 > 0]), 76)  # only 76/300 are nonzero

    def test_case_8(self):
        # case with a shakemap
        self.run_calc(case_8.__file__, 'prejob.ini')
        self.run_calc(case_8.__file__, 'job.ini',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))
        [fname] = export(('dmg_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/dmg_by_event.csv', fname)

    def test_case_9(self):
        # case with noDamageLimit==0 that had NaNs in the past
        self.run_calc(case_9.__file__, 'job.ini')

        # export/import dmg_by_event and check the total nodamage
        [fname] = export(('dmg_by_event', 'csv'), self.calc.datastore)
        df = read_csv(fname, index='event_id')
        nodamage = df[df['rlz_id'] == 0]['structural~no_damage'].sum()
        self.assertEqual(nodamage, 1068763.0)

        [fname] = export(('damages-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damages.csv', fname)

        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/losses_asset.csv', fname)

        # check dd_data
        df = self.calc.datastore.read_df('dd_data', 'eid')
        dmg = df.loc[1937]  # damage caused by the event 1937
        self.assertEqual(dmg.slight.sum(), 54)  # breaks in github
        self.assertEqual(dmg.moderate.sum(), 59)
        self.assertEqual(dmg.extensive.sum(), 31)
        self.assertEqual(dmg.complete.sum(), 25)

    def test_case_10(self):
        # error case: there a no RiskInputs
        with self.assertRaises(RuntimeError):
            self.run_calc(case_10.__file__, 'job.ini')

    def test_case_11(self):
        # secondary perils without secondary simulations
        self.run_calc(case_11.__file__, 'job.ini')
        calc1 = self.calc.datastore
        df = calc1.read_df('dd_data', 'aid')
        df0 = df.loc[0]
        self.assertEqual(str(df0), '''\
     eid  lid  moderate  complete
aid                              
0      0    0  0.066928  9.932871
0      1    0  5.402263  4.364481
0      2    0  6.291139  3.325114
0      3    0  5.424275  0.065626
0      4    0  0.042872  9.957011
0      5    0  0.001594  9.998403
0      6    0  0.042872  9.957011
0      7    0  0.027247  9.972686''')
        df1 = df.loc[1]
        self.assertEqual(str(df1), '''\
     eid  lid   moderate   complete
aid                                
1      0    0   1.759441  18.215437
1      1    0   1.567887   0.000060
1      2    0   1.567887   0.000060
1      3    0  10.911393   0.131251
1      4    0  10.309752   9.147042
1      5    0   8.835979  10.788784
1      6    0  15.001849   1.981890''')
        df2 = df.loc[2]
        self.assertEqual(str(df2), '''\
     eid  lid   moderate   complete
aid                                
2      0    0  21.080206   7.058046
2      1    0   8.044790   0.010072
2      2    0  22.812601   2.637918
2      3    0   0.475818  29.522369
2      4    0  10.698418  19.052910''')

        # secondary perils with secondary simulations
        self.run_calc(case_11.__file__, 'job.ini',
                      secondary_simulations="{'LiqProb': 50}")
        calc2 = self.calc.datastore
        df = calc2.read_df('dd_data', 'aid')
        df0 = df.loc[0]
        self.assertEqual(str(df0), '''\
     eid  lid  moderate  complete
aid                              
0      1    0  0.540226  0.436448
0      2    0  1.761519  0.931032
0      3    0  0.216971  0.002625
0      4    0  0.001715  0.398280
0      5    0  0.000638  3.999361
0      6    0  0.005145  1.194841
0      7    0  0.004360  1.595630''')
        df1 = df.loc[1]
        self.assertEqual(str(df1), '''\
     eid  lid  moderate  complete
aid                              
1      0    0  0.281511  2.914470
1      1    0  0.125431  0.000005
1      2    0  0.846659  0.000032
1      3    0  4.801013  0.057750
1      4    0  0.824780  0.731763
1      5    0  3.004233  3.668187
1      6    0  4.200518  0.554929''')
        df2 = df.loc[2]
        self.assertEqual(str(df2), '''\
     eid  lid  moderate  complete
aid                              
2      0    0  5.480854  1.835092
2      1    0  4.022395  0.005036
2      3    0  0.085647  5.314026
2      4    0  1.069842  1.905291''')

        # check damages-rlzs
        [fname] = export(('damages-rlzs', 'csv'), calc1)
        self.assertEqualFiles('expected/avg_damages1.csv', fname)
        [fname] = export(('damages-rlzs', 'csv'), calc2)
        self.assertEqualFiles('expected/avg_damages2.csv', fname)

    def test_case_11_risk(self):
        # losses due to liquefaction
        self.run_calc(case_11.__file__, 'job_risk.ini')
        alt = self.calc.datastore.read_df('agg_loss_table', 'agg_id')

        aac(losses(0, alt), [0, 352, 905, 55, 199, 1999, 598, 798])
        aac(losses(1, alt), [4581, 0, 288, 2669, 2287, 6068, 3036, 0])
        aac(losses(2, alt), [4754, 0, 421, 7141, 3644, 0, 0, 0])

        self.run_calc(case_11.__file__, 'job_risk.ini',
                      secondary_simulations='{}')
        alt = self.calc.datastore.read_df('agg_loss_table', 'agg_id')
        aac(losses(0, alt), [4982, 3524, 3235, 1388, 4988, 4999, 4988, 4993])
        aac(losses(1, alt), [38175, 3, 903, 11122, 28599, 30341, 18978, 0])
        aac(losses(2, alt), [26412, 0, 21055, 44631, 36447, 0, 0, 0])


def losses(aid, alt):
    E = len(alt.event_id.unique())
    losses = numpy.zeros(E, numpy.uint32)
    df = alt.loc[aid]
    losses[df.event_id.to_numpy()] = df.structural.to_numpy()
    return losses
