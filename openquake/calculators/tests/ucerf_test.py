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
import os
import sys
import h5py
import unittest
from openquake.baselib.general import writetmp
from openquake.calculators.export import export
from openquake.calculators.views import view
from openquake.qa_tests_data import ucerf
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id

from nose.plugins.attrib import attr


class UcerfTestCase(CalculatorTestCase):
    @attr('qa', 'hazard', 'ucerf')
    def test_event_based(self):
        if h5py.__version__ < '2.6.0':
            raise unittest.SkipTest  # UCERF requires vlen arrays
        self.run_calc(ucerf.__file__, 'job.ini')
        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        # check that we get the expected number of events
        with open(fname) as f:
            self.assertEqual(len(f.readlines()), 918)
        # check the header and the first 18 events
        self.assertEqualFiles('expected/ruptures.csv', fname, lastline=19)

        # run a regular event based on top of the UCERF ruptures and
        # check the generated hazard maps
        self.run_calc(ucerf.__file__, 'job.ini',
                      calculation_mode='event_based',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))
        [fname] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname)

    @attr('qa', 'hazard', 'ucerf')
    def test_classical(self):
        if h5py.__version__ < '2.6.0':
            raise unittest.SkipTest  # UCERF requires vlen arrays
        out = self.run_calc(ucerf.__file__, 'job_classical_redux.ini',
                            exports='csv')
        [f1, f2] = out['hcurves', 'csv']
        self.assertEqualFiles('expected/hazard_curve-rlz-000.csv', f1)
        self.assertEqualFiles('expected/hazard_curve-rlz-001.csv', f2)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    @attr('qa', 'hazard', 'ucerf_td')
    def test_classical_time_dep(self):
        if h5py.__version__ < '2.6.0':
            raise unittest.SkipTest  # UCERF requires vlen arrays
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            exports='csv')
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-td-mean.csv', fname,
                              delta=1E-6)

        # make sure this runs
        view('fullreport', self.calc.datastore)

    @attr('qa', 'hazard', 'ucerf_td')
    def test_classical_time_dep_sampling(self):
        if h5py.__version__ < '2.6.0':
            raise unittest.SkipTest  # UCERF requires vlen arrays
        out = self.run_calc(ucerf.__file__, 'job_classical_time_dep_redux.ini',
                            number_of_logic_tree_samples='2',
                            exports='csv')
        fname = out['hcurves', 'csv'][0]
        self.assertEqualFiles('expected/hazard_curve-sampling.csv', fname,
                              delta=1E-6)

    @attr('qa', 'risk', 'ucerf')
    def test_event_based_risk(self):
        if h5py.__version__ < '2.6.0':
            raise unittest.SkipTest  # UCERF requires vlen arrays
        self.run_calc(ucerf.__file__, 'job_ebr.ini',
                      number_of_logic_tree_samples='2')

        fnames = export(('agg_loss_table', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', fname)

        # make sure this runs
        view('fullreport', self.calc.datastore)
