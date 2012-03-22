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
import json

from openquake import kvs

from openquake.shapes import Site, RegionConstraint, GridPoint
from openquake.engine import JobContext
from openquake.kvs.tokens import ground_motion_values_key
from openquake.calculators.risk.general import Block
from openquake.calculators.risk.scenario_damage.core import ScenarioDamageRiskCalculator

JOB_ID = 1
BLOCK_ID = 1

class ScenarioDamageRiskCalculatorTestCase(unittest.TestCase):
    
    def setUp(self):
        kvs.mark_job_as_current(JOB_ID)
        kvs.cache_gc(JOB_ID)
    
    def test_pre_execute(self):
        pass

    def test_compute_risk(self):
        site = Site(1.0, 1.0)

        block = Block(JOB_ID, BLOCK_ID, [site])
        block.to_kvs()

        # this region contains a single site, that is exactly
        # a site with longitude == 1.0 and latitude == 1.0
        params = {"REGION_VERTEX": "1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0",
                "REGION_GRID_SPACING": "0.5"}

        job_ctxt = JobContext(params, JOB_ID)

        # now storing in kvs the ground motion values
        self._store_gmvs([0.40, 0.30, 0.45, 0.35, 0.40])

        calculator = ScenarioDamageRiskCalculator(job_ctxt)
        calculator.compute_risk(BLOCK_ID)

    def _store_gmvs(self, gmvs):
        client = kvs.get_client()
        encoder = json.JSONEncoder()

        key = ground_motion_values_key(JOB_ID, GridPoint(None, 0, 0))

        for gmv in gmvs:
            client.rpush(key, encoder.encode({"mag": gmv}))
