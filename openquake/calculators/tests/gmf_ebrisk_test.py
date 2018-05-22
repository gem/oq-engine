# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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

import sys
import unittest
import numpy
from nose.plugins.attrib import attr
from openquake.baselib.general import gettemp
from openquake.calculators.views import view
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.qa_tests_data.gmf_ebrisk import case_1, case_2, case_3, case_4
from openquake.qa_tests_data.event_based_risk import (
    case_master, case_2 as ebr_2)

aae = numpy.testing.assert_almost_equal


def check_csm_info(calc1, calc2):
    data1 = (calc1['csm_info/sg_data'].value, calc1['csm_info/sm_data'].value)
    data2 = (calc2['csm_info/sg_data'].value, calc2['csm_info/sm_data'].value)
    for val1, val2 in zip(data1, data2):
        for name in val1.dtype.names:
            if name not in ('name', 'path'):  # avoid comparing strings
                aae(val1[name], val2[name])


class GmfEbRiskTestCase(CalculatorTestCase):
    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1(self):
        self.run_calc(case_1.__file__, 'job_risk.ini')
        num_events = len(self.calc.datastore['losses_by_event'])
        self.assertEqual(num_events, 10)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        # case with 3 sites but gmvs only on 2 sites
        self.run_calc(case_2.__file__, 'job.ini')
        alt = self.calc.datastore['losses_by_event']
        self.assertEqual(len(alt), 3)
        self.assertEqual(set(alt['rlzi']), set([0]))  # single rlzi
        totloss = alt['loss'].sum()
        aae(totloss, 1.5788584)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        # case with 13 sites, 10 eids, and several 0 values
        self.run_calc(case_3.__file__, 'job.ini')
        alt = self.calc.datastore['losses_by_event']
        self.assertEqual(len(alt), 8)
        self.assertEqual(set(alt['rlzi']), set([0]))  # single rlzi
        totloss = alt['loss'].sum(axis=0)
        aae(totloss, [7717694.], decimal=0)

        # avg_losses-rlzs has shape (A, R, LI)
        avglosses = self.calc.datastore['avg_losses-rlzs'][:, 0, :].sum(axis=0)
        aae(avglosses, [7717694.], decimal=0)

    @attr('qa', 'risk', 'event_based_risk')
    def test_ebr_2(self):
        self.run_calc(ebr_2.__file__, 'job_ebrisk.ini', exports='csv')
        fname = gettemp(view('mean_avg_losses', self.calc.datastore))
        self.assertEqualFiles('expected/avg_losses.txt', fname)
        alt = self.calc.datastore['losses_by_event']
        self.assertEqual(len(alt), 20)
        self.assertEqual(set(alt['rlzi']), set([0]))  # single rlzi
        totloss = alt['loss'].sum()
        aae(totloss, 20210.27, decimal=2)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_4(self):
        # a simple test with 1 asset and two source models
        # this is also a test with preimported exposure
        self.run_calc(case_4.__file__, 'job_haz.ini')
        calc0 = self.calc.datastore  # event_based
        self.run_calc(case_4.__file__, 'job_risk.ini',
                      concurrent_tasks='0',  # avoid for bug
                      hazard_calculation_id=str(calc0.calc_id))
        calc1 = self.calc.datastore  # event_based_risk
        [fname] = export(('agg_loss_table', 'csv'), calc1)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=1E-5)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_master(self):
        self.run_calc(case_master.__file__, 'job.ini', insured_losses='false')
        calc0 = self.calc.datastore  # single file event_based_risk
        self.run_calc(case_master.__file__, 'job.ini', insured_losses='false',
                      calculation_mode='event_based',
                      concurrent_tasks='0')
        calc1 = self.calc.datastore  # event_based
        self.run_calc(case_master.__file__, 'job.ini', insured_losses='false',
                      hazard_calculation_id=str(calc1.calc_id),
                      source_model_logic_tree_file='',
                      gsim_logic_tree_file='',
                      concurrent_tasks='0')  # to avoid fork bug
        calc2 = self.calc.datastore  # two files event_based_risk

        check_csm_info(calc0, calc2)  # the csm_info arrays must be equal

        if sys.platform == 'darwin':
            raise unittest.SkipTest('MacOSX')

        # compare the average losses for an event_based_risk
        # case_master calculation from ruptures
        f0 = gettemp(view('mean_avg_losses', calc0))
        self.assertEqualFiles('expected/avg_losses.txt', f0, delta=1E-5)

        # the two-lines below may break on Jenkins
        f2 = gettemp(view('mean_avg_losses', calc2))
        self.assertEqualFiles('expected/avg_losses.txt', f2, delta=1E-4)

        # compare the event loss table generated by a event_based_risk
        # case_master calculation from ruptures
        f0 = gettemp(view('elt', calc0))
        self.assertEqualFiles('expected/elt.txt', f0, delta=1E-5)
        f2 = gettemp(view('elt', calc2))
        self.assertEqualFiles('expected/elt.txt', f2, delta=1E-5)
