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

    def test(self):
        for case in [case_1, case_2, case_3, case_4, case_5]:
            with self.subTest(case.__name__):
                out = self.run_calc(case.__file__, 'job.ini',
                                    exports='csv')
                [fname] = out['reinsurance_losses', 'csv']
                self.assertEqualFiles(
                    'expected/%s' % strip_calc_id(fname), fname)
