# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2020 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from openquake.calculators.export import export
from openquake.calculators.views import view
from openquake.calculators import ucerf_base
from openquake.qa_tests_data import ucerf
from openquake.calculators.tests import CalculatorTestCase


class UcerfTestCase(CalculatorTestCase):

    def test_event_based(self):
        self.run_calc(ucerf.__file__, 'job.ini')
        gmv_uc = view('global_gmfs', self.calc.datastore)
        # check the distribution of the events
        self.assertEventsByRlz(
            [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0,
             1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0])

        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', fname, delta=2E-5)

        # run a regular event based on top of the UCERF ruptures and
        # check the generated hazard maps
        self.calc.datastore.close()  # avoid https://ci.openquake.org/job/macos/job/master_macos_engine/label=catalina,python=python3.7/5388/consoleFull
        self.run_calc(ucerf.__file__, 'job.ini',
                      calculation_mode='event_based',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))

        # check they produce the same GMFs
        gmv_eb = view('global_gmfs', self.calc.datastore)
        self.assertEqual(gmv_uc, gmv_eb)

        # check the mean hazard map
        [fname] = [f for f in export(('hmaps', 'csv'), self.calc.datastore)
                   if 'mean' in f]
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname,
                              delta=1E-5)

    def test_event_based_sampling(self):
        self.run_calc(ucerf.__file__, 'job_ebh.ini')

        # check the distribution of the events
        self.assertEventsByRlz([15, 18])

    def test_classical(self):
        self.run_calc(ucerf.__file__, 'job_classical_redux.ini',
                      ruptures_per_block='50', exports='csv')
        fnames = export(('hcurves/', 'csv'), self.calc.datastore)
        expected = ['hazard_curve-0-PGA.csv', 'hazard_curve-0-SA(0.1).csv',
                    'hazard_curve-1-PGA.csv', 'hazard_curve-1-SA(0.1).csv']
        for fname, exp in zip(fnames, expected):
            self.assertEqualFiles('expected/' + exp, fname)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    def test_classical_time_dep(self):
        ucerf_base.RUPTURES_PER_BLOCK = 10  # check splitting
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            exports='csv')
        ucerf_base.RUPTURES_PER_BLOCK = 1000  # resume default
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-td-mean.csv', fname,
                              delta=1E-6)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    def test_classical_time_dep_sampling(self):
        ucerf_base.RUPTURES_PER_BLOCK = 10  # check splitting
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            number_of_logic_tree_samples='2',
                            exports='csv')
        ucerf_base.RUPTURES_PER_BLOCK = 1000  # resume default
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-sampling.csv', fname,
                              delta=1E-6)
