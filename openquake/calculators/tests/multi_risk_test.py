# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
from openquake.qa_tests_data.multi_risk import case_1
from openquake.calculators.tests import CalculatorTestCase
from openquake.calculators.export import export
from openquake.calculators.extract import extract

aae = numpy.testing.assert_almost_equal


class MultiRiskTestCase(CalculatorTestCase):

    def test_case_1(self):
        # case with volcanic multiperil ASH, LAVA, LAHAR, PYRO
        self.run_calc(case_1.__file__, 'job.ini')

        [fname] = export(('asset_risk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/asset_risk.csv', fname)

        # check extract
        md = extract(self.calc.datastore, 'exposure_metadata')
        self.assertEqual(md.array, [b'number', b'occupants_None',
                                    b'occupants_night', b'value-structural'])
        self.assertEqual(md.multi_risk, ['LAHAR', 'LAVA', 'PYRO',
                                         'collapse-structural-ASH_DRY',
                                         'collapse-structural-ASH_WET',
                                         'loss-structural-ASH_DRY',
                                         'loss-structural-ASH_WET',
                                         'no_damage-structural-ASH_DRY',
                                         'no_damage-structural-ASH_WET'])

    def test_case_2(self):
        # case with two damage states
        self.run_calc(case_1.__file__, 'job_2.ini')

        [fname] = export(('asset_risk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/asset_risk_2.csv', fname)

        # check extract
        md = extract(self.calc.datastore, 'exposure_metadata')
        self.assertEqual(md.array, [b'number', b'occupants_None',
                                    b'occupants_night', b'value-structural'])
        self.assertEqual(md.multi_risk, ['LAHAR', 'LAVA', 'PYRO',
                                         'collapse-structural-ASH_DRY',
                                         'collapse-structural-ASH_WET',
                                         'loss-structural-ASH_DRY',
                                         'loss-structural-ASH_WET',
                                         'moderate-structural-ASH_DRY',
                                         'moderate-structural-ASH_WET',
                                         'no_damage-structural-ASH_DRY',
                                         'no_damage-structural-ASH_WET'])

    def test_case_3(self):
        # case with volcanic lava
        self.run_calc(case_1.__file__, 'job.ini',
                      multi_peril_csv="{'LAVA': 'lava_flow.csv'}")

        # check extract
        md = extract(self.calc.datastore, 'exposure_metadata')
        self.assertEqual(md.array, [b'number', b'occupants_None',
                                    b'occupants_night', b'value-structural'])
        self.assertEqual(md.multi_risk, ['LAVA'])

        # check invalid key structural_fragility_file
        with self.assertRaises(ValueError):
            self.run_calc(case_1.__file__, 'job.ini',
                          structura_fragility_file='fragility_model.xml')

        # check invalid key structural_consequence_file
        with self.assertRaises(ValueError):
            self.run_calc(case_1.__file__, 'job.ini',
                          structura_consequence_file='consequence_model.xml')
