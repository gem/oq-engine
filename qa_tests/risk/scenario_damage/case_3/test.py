# Copyright (c) 2010-2013, GEM Foundation.
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

import os
import unittest
from nose.plugins.attrib import attr
from tests.utils import helpers
from openquake.engine.calculators.risk import CALCULATORS


class ScenarioDamageRiskCase3TestCase(unittest.TestCase):
    cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

    @attr('qa', 'risk', 'scenario_damage')
    def test_orphan_taxonomies(self):
        hazard_demo = helpers.demo_file("scenario_hazard/job.ini")
        job, _files = helpers.get_scenario_risk_job(self.cfg, hazard_demo)
        calc = CALCULATORS[job.risk_calculation.calculation_mode](job)
        # not enough taxonomies in the fragility_function, RM is missing
        with self.assertRaises(RuntimeError) as cm:
            calc.pre_execute()
        self.assertEqual(
            str(cm.exception), "The following taxonomies are in the exposure "
            "model bad not in the fragility model: set([u'RM'])")
