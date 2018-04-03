# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_bcr import case_1, case_2
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id


class ClassicalBCRTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_bcr')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['bcr-rlzs', 'csv']
        self.assertEqualFiles('expected/bcr-structural.csv', fname)

    @attr('qa', 'risk', 'classical_bcr')
    def test_case_2(self):
        # test with the exposure in CSV format
        self.run_calc(case_2.__file__, 'job.ini',
                      exposure_file='exposure_model-header.xml')

        # test with the exposure in XML format
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv')
        fnames = out['bcr-stats', 'csv']
        assert fnames
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)
