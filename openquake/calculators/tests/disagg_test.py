# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
import numpy
from nose.plugins.attrib import attr
from openquake.baselib.general import writetmp
from openquake.hazardlib.probability_map import combine
from openquake.commonlib import calc
from openquake.calculators.views import view
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.disagg import case_1, case_2, case_3, case_master


class DisaggregationTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, fmt='xml', delta=None):
        if sys.platform == 'win32':  # disable concurrency on windows
            out = self.run_calc(test_dir, 'job.ini', exports=fmt,
                                concurrent_tasks='0')
        else:
            out = self.run_calc(test_dir, 'job.ini', exports=fmt)
        got = out['disagg', fmt]
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected_output/%s' % fname, actual)

    @attr('qa', 'hazard', 'disagg')
    def test_case_1(self):
        self.assert_curves_ok(
            ['poe-0.02-rlz-0-PGA-10.1-40.1_Mag.csv',
             'poe-0.02-rlz-0-PGA-10.1-40.1_Mag_Dist.csv',
             'poe-0.02-rlz-0-PGA-10.1-40.1_Lon_Lat.csv',
             'poe-0.02-rlz-0-SA(0.025)-10.1-40.1_Mag.csv',
             'poe-0.02-rlz-0-SA(0.025)-10.1-40.1_Mag_Dist.csv',
             'poe-0.02-rlz-0-SA(0.025)-10.1-40.1_Lon_Lat.csv',
             'poe-0.1-rlz-0-PGA-10.1-40.1_Mag.csv',
             'poe-0.1-rlz-0-PGA-10.1-40.1_Mag_Dist.csv',
             'poe-0.1-rlz-0-PGA-10.1-40.1_Lon_Lat.csv',
             'poe-0.1-rlz-0-SA(0.025)-10.1-40.1_Mag.csv',
             'poe-0.1-rlz-0-SA(0.025)-10.1-40.1_Mag_Dist.csv',
             'poe-0.1-rlz-0-SA(0.025)-10.1-40.1_Lon_Lat.csv'],
            case_1.__file__,
            fmt='csv')

        # disaggregation by source group
        pgetter = calc.PmapGetter(self.calc.datastore)
        pmaps = []
        for grp in sorted(pgetter.dstore['poes']):
            pmaps.append(pgetter.get_mean(grp))
        # make sure that the combination of the contributions is okay
        pmap = pgetter.get_mean()  # total mean map
        cmap = combine(pmaps)  # combination of the mean maps per source group
        for sid in pmap:
            numpy.testing.assert_almost_equal(pmap[sid].array, cmap[sid].array)

    @attr('qa', 'hazard', 'disagg')
    def test_case_2(self):
        if sys.platform == 'darwin':
            raise unittest.SkipTest('MacOSX')
        self.assert_curves_ok([
            'rlz-0-PGA--3.0--3.0.xml', 'rlz-0-PGA-0.0-0.0.xml',
            'rlz-1-PGA--3.0--3.0.xml', 'rlz-1-PGA-0.0-0.0.xml',
            'rlz-2-PGA-0.0-0.0.xml', 'rlz-3-PGA-0.0-0.0.xml'],
            case_2.__file__)

    @attr('qa', 'hazard', 'disagg')
    def test_case_3(self):
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(case_3.__file__, 'job.ini')
        self.assertEqual(str(ctx.exception), '''\
You are trying to disaggregate for poe=0.1.
However the source model #0, 'source_model_test_complex.xml',
produces at most probabilities of 0.0362320992703 for rlz=#0, IMT=PGA.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.''')

    @attr('qa', 'hazard', 'disagg')
    def test_case_master(self):
        # this tests exercise the case of a complex logic tree; it also
        # prints the warning on poe_agg very different from the expected poe
        self.run_calc(case_master.__file__, 'job.ini')
        fname = writetmp(view('mean_disagg', self.calc.datastore))
        self.assertEqualFiles('expected/mean_disagg.rst', fname)
        os.remove(fname)
