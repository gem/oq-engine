# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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

from openquake.baselib.general import fast_agg3
from openquake.hazardlib import InvalidFile
from openquake.commonlib.writers import write_csv
from openquake.qa_tests_data.scenario_damage import (
    case_1, case_1c, case_2, case_3, case_4, case_4b, case_5, case_5a,
    case_6, case_7, case_8, case_9, case_10)
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.extract import extract
from openquake.calculators.export import export
from openquake.calculators.views import view

aac = numpy.testing.assert_allclose


class ScenarioDamageTestCase(CalculatorTestCase):
    def assert_ok(self, pkg, job_ini, exports='csv', kind='dmg'):
        test_dir = os.path.dirname(pkg.__file__)
        out = self.run_calc(test_dir, job_ini, exports=exports,
                            collapse_threshold='0')
        got = out[kind + '_by_asset', exports]
        expected_dir = os.path.join(test_dir, 'expected')
        expected = sorted(f for f in os.listdir(expected_dir)
                          if f.endswith(exports) and 'by_taxon' not in f)
        self.assertEqual(len(got), len(expected))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual)
        #self.check_dmg_by_event()

    def check_dmg_by_event(self):
        number = self.calc.datastore['assetcol/array']['number']
        data = self.calc.datastore['dd_data/data'][()]
        if len(data):
            data_by_eid = fast_agg3(data, 'eid', ['dd'], number[data['aid']])
            dmg_by_event = self.calc.datastore['dmg_by_event'][()]
            for rec1, rec2 in zip(data_by_eid, dmg_by_event):
                aac(rec1['dd'], rec2['dmg'][:, 1:], atol=.1)

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
        test_dir = os.path.dirname(case_1c.__file__)
        self.run_calc(test_dir, 'job.ini', exports='csv')
        [fname] = export(('dmg_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        # check dmg_by_asset
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

        [fname] = export(('losses_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        fnames = export(('losses_by_asset', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 2)  # one per realization
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

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
        [npz] = export(('dmg_by_asset', 'npz'), self.calc.datastore)
        self.assertEqual(strip_calc_id(npz), 'dmg_by_asset.npz')

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

        fnames = export(('dmg_by_asset', 'csv'), self.calc.datastore)
        for i, fname in enumerate(fnames):
            self.assertEqualFiles('expected/dmg_by_asset-%d.csv' % i, fname)

        fnames = export(('losses_by_asset', 'csv'), self.calc.datastore)
        for i, fname in enumerate(fnames):
            self.assertEqualFiles('expected/losses_asset-%d.csv' % i, fname)

    def test_case_10(self):
        # case with more IMTs in the imported GMFs than required
        self.run_calc(case_10.__file__, 'job.ini')

        fnames = export(('dmg_by_asset', 'csv'), self.calc.datastore)
        for i, fname in enumerate(fnames):
            self.assertEqualFiles('expected/dmg_by_asset-%d.csv' % i, fname)
