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
import numpy

from openquake.hazardlib import InvalidFile
from openquake.commonlib.writers import write_csv
from openquake.qa_tests_data.scenario_damage import (
    case_1, case_1c, case_1h, case_2, case_3, case_4, case_4b, case_5, case_5a,
    case_6, case_7, case_8)
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.extract import extract
from openquake.calculators.export import export
from openquake.calculators.views import view

aae = numpy.testing.assert_almost_equal


class ScenarioDamageTestCase(CalculatorTestCase):
    def assert_ok(self, pkg, job_ini, exports='csv', kind='dmg'):
        test_dir = os.path.dirname(pkg.__file__)
        out = self.run_calc(test_dir, job_ini, exports=exports)
        got = out[kind + '_by_asset', exports]
        expected_dir = os.path.join(test_dir, 'expected')
        expected = sorted(f for f in os.listdir(expected_dir)
                          if f.endswith(exports) and 'by_taxon' not in f)
        self.assertEqual(len(got), len(expected))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual)

    def test_case_1(self):
        # test with a single event
        self.assert_ok(case_1, 'job_risk.ini')
        got = view('num_units', self.calc.datastore)
        self.assertEqual('''\
======== =========
taxonomy num_units
======== =========
RC       2,000    
RM       4,000    
*ALL*    6,000    
======== =========''', got)

        # test agg_damages, 1 realization x 3 damage states
        [dmg] = extract(self.calc.datastore, 'agg_damages/structural?'
                        'taxonomy=RC&CRESTA=01.1')
        numpy.testing.assert_almost_equal(
            [1498.0121, 472.96616, 29.021801], dmg, decimal=4)
        # test no intersection
        dmg = extract(self.calc.datastore, 'agg_damages/structural?'
                      'taxonomy=RM&CRESTA=01.1')
        self.assertEqual(dmg.shape, ())

    def test_case_1c(self):
        # this is a case with more hazard sites than exposure sites
        test_dir = os.path.dirname(case_1c.__file__)
        self.run_calc(test_dir, 'job.ini', exports='csv')
        total = extract(self.calc.datastore, 'agg_damages/structural')
        aae([[0.4906653, 0.3249882, 0.0708492, 0.0211334, 0.092364]],
            total)  # shape (R, D) = (1, 5)

        # check extract gmf_data works with a filtered site collection
        gmf_data = dict(extract(self.calc.datastore, 'gmf_data'))
        self.assertEqual(gmf_data['rlz-000'].shape, (1,))

    def test_case_1h(self):
        # test for consequences with a single asset
        self.assert_ok(case_1h, 'job_risk.ini', exports='csv', kind='losses')

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
