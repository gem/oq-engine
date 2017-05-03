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

from nose.plugins.attrib import attr
from openquake.calculators.tests import CalculatorTestCase
from openquake.calculators.export import export
from openquake.qa_tests_data.classical_tiling import case_1, case_2


class ClassicalTilingTestCase(CalculatorTestCase):
    @attr('qa', 'hazard', 'classical_tiling')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv')
        expected = [
            'hazard_curve-mean.csv',
            'quantile_curve-0.1.csv',
            'hazard_map-mean.csv',
            'quantile_map-0.1.csv',
        ]
        got = (out['hcurves', 'csv'] +
               out.get(('hmaps', 'csv'), []))
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual, delta=1E-6)

    @attr('qa', 'hazard', 'classical_tiling')
    def test_case_2(self):
        self.run_calc(case_2.__file__, 'job.ini', exports='csv,geojson')
        [fname] = export(('hmaps', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_map-mean.csv', fname, delta=1E-6)
