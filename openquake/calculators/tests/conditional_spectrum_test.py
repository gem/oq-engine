# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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

from openquake.calculators.tests import CalculatorTestCase
from openquake.calculators.export import export
from openquake.qa_tests_data.conditional_spectrum import case_1, case_2


class ConditionalSpectrumTestCase(CalculatorTestCase):

    def test_case_1(self):
        # test with 2x3=6 realizations and two poes
        self.run_calc(case_1.__file__, 'job.ini', concurrent_tasks='4')
        [f0, f1] = export(('cs-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/conditional-spectrum-0.csv', f0)
        self.assertEqualFiles('expected/conditional-spectrum-1.csv', f1)
        hc_id = str(self.calc.datastore.calc_id)

        # check independence from concurrent_tasks
        self.run_calc(case_1.__file__, 'job.ini', concurrent_tasks='8',
                      hazard_calculation_id=hc_id)
        [f0, f1] = export(('cs-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/conditional-spectrum-0.csv', f0)
        self.assertEqualFiles('expected/conditional-spectrum-1.csv', f1)

    def test_case_2(self):
        # test with two source models and two sites
        self.run_calc(case_2.__file__, 'job.ini')
        [f0, f1] = export(('cs-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/cs-0.csv', f0)
        self.assertEqualFiles('expected/cs-1.csv', f1)
