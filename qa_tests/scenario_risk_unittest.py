# Copyright (c) 2010-2012, GEM Foundation.
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


import unittest

from nose.plugins.attrib import attr

from openquake.db.models import OqCalculation

from tests.utils import helpers


class ScenarioRiskQATest(unittest.TestCase):
    """QA test for the Scenario Risk calculator."""

    @attr('qa')
    def test_scenario_risk(self):
        # The rudimentary beginnings of a QA test for the scenario calc.
        # For now, just run it end-to-end to make sure it doesn't blow up.
        scen_cfg = helpers.demo_file('scenario_risk/config.gem')

        ret_code = helpers.run_job(scen_cfg, ['--output-type=xml'])
        self.assertEqual(0, ret_code)

        calculation = OqCalculation.objects.latest('id')
        self.assertEqual('succeeded', calculation.status)
