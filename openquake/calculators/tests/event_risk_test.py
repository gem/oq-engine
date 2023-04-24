# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2023 GEM Foundation
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
from openquake.commonlib.datastore import read
from openquake.calculators.views import view
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.qa_tests_data.gmf_ebrisk import case_1, case_2, case_3, case_4
from openquake.qa_tests_data.event_based_risk import (
    case_master, case_2 as ebr_2)

aae = numpy.testing.assert_almost_equal


def check_full_lt(calc1, calc2):
    val1 = calc1['full_lt/sm_data'][()]
    val2 = calc2['full_lt/sm_data'][()]
    for name in val1.dtype.names:
        if name not in ('name', 'path'):  # avoid comparing strings
            aae(val1[name], val2[name])


class GmfEbRiskTestCase(CalculatorTestCase):
    def test_case_1(self):
        self.run_calc(case_1.__file__, 'job_risk.ini')
        text = view('portfolio_loss', self.calc.datastore)
        self.assertIn('avg  | 4_322', text)

        # test the HDF5 importer
        self.run_calc(case_1.__file__, 'job.ini')
        text = view('portfolio_loss', self.calc.datastore)
        self.assertIn('avg  | 4_322', text)

    def test_case_2(self):
        # case with 3 sites but gmvs only on 2 sites
        self.run_calc(case_2.__file__, 'job.ini')
        alt = self.calc.datastore.read_df('risk_by_event', 'agg_id')
        self.assertEqual(len(alt), 3)
        totloss = alt.loss.sum()
        aae(totloss, 1.82, decimal=4)

    def test_case_3(self):
        # case with 13 sites, 10 eids, and several 0 values
        self.run_calc(case_3.__file__, 'job.ini')
        alt = self.calc.datastore.read_df('risk_by_event', 'agg_id')
        self.assertEqual(len(alt), 10)
        totloss = alt.loss.sum()

        avglosses = self.calc.datastore[
            'avg_losses-rlzs/structural'][:, 0].sum(axis=0)
        aae(avglosses / 1E6, totloss / 1E6, decimal=4)

    def test_ebr_2(self):
        self.run_calc(ebr_2.__file__, 'job_ebrisk.ini', exports='csv')
        alt = self.calc.datastore.read_df('risk_by_event', 'agg_id')
        self.assertEqual(len(alt), 8)
        totloss = alt.loss.sum()
        aae(totloss, 15911.156, decimal=2)

    def test_case_4(self):
        # a simple test with 3 assets and two source models
        # this is also a test with preimported exposure and aggr by site_id
        self.run_calc(case_4.__file__, 'job_haz.ini')
        calc0 = self.calc.datastore  # event_based
        self.run_calc(case_4.__file__, 'job_risk.ini',
                      hazard_calculation_id=str(calc0.calc_id))
        calc1 = self.calc.datastore  # event_based_risk
        [fname] = export(('risk_by_event', 'csv'), calc1)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=1E-5)

        # checking avg_losses-stats with collect_rlzs
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=1E-5)

        # checking aggrisk
        for fname in export(('aggrisk', 'csv'), self.calc.datastore):
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-5)

        # checking aggcurves
        for fname in export(('aggcurves', 'csv'), self.calc.datastore):
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-5)

    def test_case_master(self):
        self.run_calc(case_master.__file__, 'job.ini')
        calc0 = self.calc.datastore  # single file event_based_risk
        self.run_calc(case_master.__file__, 'job.ini',
                      calculation_mode='event_based')
        calc1 = self.calc.datastore  # event_based
        self.run_calc(case_master.__file__, 'job.ini',
                      hazard_calculation_id=str(calc1.calc_id),
                      source_model_logic_tree_file='',
                      gsim_logic_tree_file='')
        calc2 = self.calc.datastore  # two files event_based_risk

        check_full_lt(calc0, calc1)  # the full_lt arrays must be equal
        check_full_lt(calc0, calc2)  # the full_lt arrays must be equal

    def test_read_old(self):
        # check GMFs in v3.11 format are readable
        d = os.path.dirname(case_master.__file__)
        ds = read(os.path.join(d, 'calc_311.hdf5'))
        gmf_df = ds.read_df('gmf_data', 'eid')
        self.assertEqual(len(gmf_df), 314)
