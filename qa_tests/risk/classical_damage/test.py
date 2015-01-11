# Copyright (c) 2015, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.qa_tests_data.classical_damage import case_3

from openquake.engine.db import models


class ClassicalDamageCase3TestCase(risk.FixtureBasedQATestCase):
    module = case_3
    output_type = 'dmg_per_asset'
    hazard_calculation_fixture = 'Classical Damage QA Test 3'

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        data = models.DamageData.objects.filter(
            dmg_state__risk_calculation=job).order_by(
            'exposure_data', 'dmg_state')
        # this is a test with a single asset and 5 damage states
        # no_damage, slight, moderate, extreme, complete
        return [row.fraction for row in data]

    def expected_data(self):
        return [0.977497, 0.0028587, 0.0046976, 0.00419187, 0.0107548]
