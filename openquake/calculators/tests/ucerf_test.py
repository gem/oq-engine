#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (C) 2016-2017 GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from openquake.baselib.general import writetmp
from openquake.calculators.export import export
from openquake.calculators.views import view, rst_table
from openquake.qa_tests_data import ucerf
from openquake.calculators.tests import CalculatorTestCase, REFERENCE_OS

from nose.plugins.attrib import attr


class UcerfTestCase(CalculatorTestCase):
    @attr('qa', 'hazard', 'ucerf')
    def test_event_based(self):
        self.run_calc(ucerf.__file__, 'job.ini')
        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        # check that we get the expected number of events
        with open(fname) as f:
            self.assertEqual(len(f.readlines()), 36)
        if REFERENCE_OS:
            # check the header and the first 18 events
            self.assertEqualFiles('expected/ruptures.csv', fname, lastline=19)

        # run a regular event based on top of the UCERF ruptures and
        # check the generated hazard maps
        self.run_calc(ucerf.__file__, 'job.ini',
                      calculation_mode='event_based',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))

        # check the GMFs
        gmdata = self.calc.datastore['gmdata'].value
        got = writetmp(rst_table(gmdata, fmt='%.6f'))
        self.assertEqualFiles('expected/gmdata_eb.csv', got)

        # check the mean hazard map
        [fname] = [f for f in export(('hmaps', 'csv'), self.calc.datastore)
                   if 'mean' in f]
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname)

    @attr('qa', 'hazard', 'ucerf')
    def test_event_based_sampling(self):
        self.run_calc(ucerf.__file__, 'job_ebh.ini')

        # check the GMFs
        gmdata = self.calc.datastore['gmdata'].value
        got = writetmp(rst_table(gmdata, fmt='%s'))
        self.assertEqualFiles('expected/gmdata.csv', got)

        # check the mean hazard map
        got = writetmp(view('hmap', self.calc.datastore))
        self.assertEqualFiles('expected/hmap.rst', got)

    @attr('qa', 'hazard', 'ucerf')
    def test_classical(self):
        self.run_calc(ucerf.__file__, 'job_classical_redux.ini', exports='csv')
        [f1, f2] = export(('hcurves/all', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-rlz-000.csv', f1)
        self.assertEqualFiles('expected/hazard_curve-rlz-001.csv', f2)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    @attr('qa', 'hazard', 'ucerf_td')
    def test_classical_time_dep(self):
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            exports='csv')
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-td-mean.csv', fname,
                              delta=1E-6)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    @attr('qa', 'hazard', 'ucerf_td')
    def test_classical_time_dep_sampling(self):
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            number_of_logic_tree_samples='2',
                            exports='csv')
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-sampling.csv', fname,
                              delta=1E-6)

    @attr('qa', 'risk', 'ucerf')
    def test_event_based_risk(self):
        self.run_calc(ucerf.__file__, 'job_ebr.ini',
                      number_of_logic_tree_samples='2')

        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', fname)

        # make sure this runs
        view('fullreport', self.calc.datastore)
