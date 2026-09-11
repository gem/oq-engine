# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2026 GEM Foundation
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
from openquake.qa_tests_data.aftershock import case_1, case_2


ae = numpy.testing.assert_equal
aac = numpy.testing.assert_allclose


class AftershockTestCase(CalculatorTestCase):

    def test_case_1(self):
        # Run aftershock: ruptures listed in delta_rates.csv have their
        # occurrence_rate shifted and, for GMMs that require it (e.g.
        # CY08, Bradley2013), are flagged as aftershocks so any aftershock
        # ground motion adjustment is applied to those ruptures
        self.run_calc(case_1.__file__, 'job.ini')

        # checking hazard curves
        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurves.csv', fname)

    def test_case_2(self):
        # Aftershock calc with AbrahamsonEtAl2014 (uses crjb),
        # ChiouYoungs2008 and Bradley2013. Tests use of optional
        # crjb column in a delta_rates CSV, which ASK14 requires for
        # any rupture flagged as an aftershock
        self.run_calc(case_2.__file__, 'job.ini')
        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hcurves.csv', fname)
