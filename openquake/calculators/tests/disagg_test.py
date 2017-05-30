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
import sys
import unittest
from nose.plugins.attrib import attr
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.disagg import case_1, case_2


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

    @attr('qa', 'hazard', 'disagg')
    def test_case_2(self):
        if sys.platform == 'darwin':
            raise unittest.SkipTest('MacOSX')
        self.assert_curves_ok(
            ['poe-0.0872-rlz-3-PGA-0.0-0.0.xml',
             'poe-0.0879-rlz-1-PGA--3.0--3.0.xml',
             'poe-0.0913-rlz-2-PGA-0.0-0.0.xml',
             'poe-0.0915-rlz-0-PGA--3.0--3.0.xml',
             'poe-0.0965-rlz-1-PGA-0.0-0.0.xml',
             'poe-0.1001-rlz-0-PGA-0.0-0.0.xml'],
            case_2.__file__)
