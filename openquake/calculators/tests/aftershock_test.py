# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

import numpy
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.aftershock import case_1


ae = numpy.testing.assert_equal
aac = numpy.testing.assert_allclose


class AftershockTestCase(CalculatorTestCase):

    def test_case_1(self):
        # run aftershock
        self.run_calc(case_1.__file__, 'pre_job.ini')

        # run classical
        hc_id = str(self.calc.datastore.calc_id)
        self.run_calc(case_1.__file__, 'job.ini', hazard_calculation_id=hc_id)

        # checking hazard curves
        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurves.csv', fname)
