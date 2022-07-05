# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2022 GEM Foundation
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
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.qa_tests_data.reinsurance import (
    case_1, case_2, case_3, case_4, case_5)


class ReinsuranceTestCase(CalculatorTestCase):

    def test_case_1(self):
        self.run_calc(case_1.__file__, 'job.ini')

    def test_case_2(self):
        self.run_calc(case_2.__file__, 'job.ini')

    def test_case_3(self):
        self.run_calc(case_3.__file__, 'job.ini')

    def test_case_4(self):
        self.run_calc(case_4.__file__, 'job.ini')

    def test_case_5(self):
        self.run_calc(case_5.__file__, 'job.ini')
