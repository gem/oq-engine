# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import json
import numpy
from openquake.qa_tests_data.multi_risk import case_1
from openquake.calculators.tests import CalculatorTestCase
from openquake.calculators.export import export
from openquake.calculators.extract import extract

ae = numpy.testing.assert_equal
aae = numpy.testing.assert_almost_equal


class MultiRiskTestCase(CalculatorTestCase):

    def test_case_1(self):
        # case with volcanic multiperil ASH, LAVA, LAHAR, PYRO
        self.run_calc(case_1.__file__, 'job.ini')

        # check extract gmf_data, called by QGIS
        aw = extract(self.calc.datastore, 'gmf_data?event_id=0')
        ae(len(aw['rlz-000']), 173)
        ae(aw['rlz-000'].dtype.names,
           ('custom_site_id', 'lon', 'lat', 'Volcanic_ASH', 'Volcanic_LAVA',
            'Volcanic_LAHAR', 'Volcanic_PYRO'))

        # check extract exposure_metadata
        md = json.loads(extract(self.calc.datastore, 'exposure_metadata').json)
        ae(md['names'], ['value-number', 'value-structural', 'occupants_night'])
        ae(md['multi_risk'], ['collapse-structural-ASH_DRY',
                              'collapse-structural-ASH_WET',
                              'loss-structural-ASH_DRY',
                              'loss-structural-ASH_WET',
                              'loss-structural-LAHAR',
                              'loss-structural-LAVA',
                              'loss-structural-PYRO',
                              'no_damage-structural-ASH_DRY',
                              'no_damage-structural-ASH_WET',
                              'number-LAHAR',
                              'number-LAVA',
                              'number-PYRO',
                              'occupants_night-LAHAR',
                              'occupants_night-LAVA',
                              'occupants_night-PYRO'])

        # check export
        [fname] = export(('asset_risk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/asset_risk.csv', fname)
        [fname] = export(('agg_risk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/agg_risk.csv', fname)

    def test_case_2(self):
        # case with two damage states
        self.run_calc(case_1.__file__, 'job_2.ini')

        # check extract
        md = json.loads(extract(self.calc.datastore, 'exposure_metadata').json)
        ae(md['multi_risk'], ['collapse-structural-ASH_DRY',
                              'collapse-structural-ASH_WET',
                              'loss-structural-ASH_DRY',
                              'loss-structural-ASH_WET',
                              'loss-structural-LAHAR',
                              'loss-structural-LAVA',
                              'loss-structural-PYRO',
                              'no_damage-structural-ASH_DRY',
                              'no_damage-structural-ASH_WET',
                              'number-LAHAR',
                              'number-LAVA',
                              'number-PYRO',
                              'occupants_night-LAHAR',
                              'occupants_night-LAVA',
                              'occupants_night-PYRO'])

        # check export
        [fname] = export(('asset_risk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/asset_risk_2.csv', fname)

        # check invalid key structural_fragility_file
        with self.assertRaises(ValueError):
            self.run_calc(case_1.__file__, 'job.ini',
                          structura_fragility_file='fragility_model.xml')
