#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (C) 2016 GEM Foundation

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

import h5py
import unittest
from openquake.qa_tests_data import ucerf
from openquake.calculators.tests import CalculatorTestCase
from nose.plugins.attrib import attr


class UcerfTestCase(CalculatorTestCase):
    @attr('qa', 'hazard', 'ucerf')
    def test_event_based(self):
        if h5py.__version__ < '2.3.0':
            raise unittest.SkipTest  # UCERF requires vlen arrays
        out = self.run_calc(ucerf.__file__, 'job.ini', exports='txt')
        num_exported = len(out['gmf_data', 'txt'])
        # just check that some realizations are exported
        self.assertGreaterEqual(num_exported, 1)

    @attr('qa', 'hazard', 'ucerf')
    def test_classical(self):
        raise unittest.SkipTest  # temporarily until the numbers become stable
        if h5py.__version__ < '2.3.0':
            raise unittest.SkipTest  # UCERF requires vlen arrays
        out = self.run_calc(ucerf.__file__, 'job_classical_redux.ini',
                            exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles('expected/hazard_curve.csv', fname)
