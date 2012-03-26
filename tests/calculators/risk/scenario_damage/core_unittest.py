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

from django.contrib.gis import geos

from openquake import kvs
from openquake.db import models
from openquake.shapes import Site, GridPoint
from openquake.db.models import Output
from openquake.engine import JobContext
from openquake.kvs.tokens import ground_motion_values_key
from openquake.calculators.risk.general import Block
from openquake.calculators.risk.scenario_damage.core import (
    ScenarioDamageRiskCalculator)

from tests.utils import helpers

BLOCK_ID = 1

class ScenarioDamageRiskCalculatorTestCase(
    unittest.TestCase, helpers.DbTestCase):
    
    job = None
    
    def setUp(self):
        kvs.mark_job_as_current(self.job.id)
        kvs.cache_gc(self.job.id)

        self.site = Site(1.0, 1.0)
        block = Block(self.job.id, BLOCK_ID, [self.site])
        block.to_kvs()

        # this region contains a single site, that is exactly
        # a site with longitude == 1.0 and latitude == 1.0
        params = {"REGION_VERTEX": "1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0",
                "REGION_GRID_SPACING": "0.5"}

        job_ctxt = JobContext(params, self.job.id, oq_job=self.job)

        # now storing in kvs the ground motion values
        self._store_gmvs([0.40, 0.30, 0.45, 0.35, 0.40])
        self._store_em()

        self.fm = self._store_fmodel()

        self.calculator = ScenarioDamageRiskCalculator(job_ctxt)

    @classmethod
    def setUpClass(cls):
        inputs = [("fragility", ""), ("exposure", "")]
        cls.job = cls.setup_classic_job(inputs=inputs)

    def test_compute_risk(self):
        self.calculator.pre_execute()
        self.calculator.compute_risk(BLOCK_ID, fmodel=self.fm)

    def TODO_pre_execute(self):
        # store the main output artifact to db
        self.calculator.pre_execute()

        sdac_output = Output.objects.filter(
            oq_job=self.job.id,
            output_type="dmg_dist_per_asset")

        self.assertEquals(1, len(sdac_output))

    def _store_gmvs(self, gmvs):
        client = kvs.get_client()
        encoder = json.JSONEncoder()

        key = ground_motion_values_key(self.job.id, GridPoint(None, 0, 0))

        for gmv in gmvs:
            client.rpush(key, encoder.encode({"mag": gmv}))

    def _store_fmodel(self):
        [ism] = models.inputs4job(self.job.id, input_type="fragility")

        fmodel = models.FragilityModel(
            owner=ism.owner, input=ism,
            lss=["LS1", "LS2"], format="continuous")

        fmodel.save()

        models.Ffc(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS1", mean="0.20", stddev="0.05").save()

        models.Ffc(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS2", mean="0.35", stddev="0.10").save()

        models.Ffc(
            fragility_model=fmodel, taxonomy="RM",
            ls="LS1", mean="0.25", stddev="0.08").save()

        models.Ffc(
            fragility_model=fmodel, taxonomy="RM",
            ls="LS2", mean="0.40", stddev="0.12").save()

        return fmodel

    def _store_em(self):
        [ism] = models.inputs4job(self.job.id, input_type="exposure")

        em = models.ExposureModel(
            owner=ism.owner, input=ism,
            name="AAA", category="single_asset",
            reco_type="aggregated", reco_unit="USD",
            stco_type="aggregated", stco_unit="USD")

        em.save()

        models.ExposureData(
            exposure_model=em, taxonomy="RC",
            asset_ref="A", stco=100,
            site=geos.GEOSGeometry(self.site.point.to_wkt()), reco=1).save()

        models.ExposureData(
            exposure_model=em, taxonomy="RM",
            asset_ref="B", stco=40,
            site=geos.GEOSGeometry(self.site.point.to_wkt()), reco=1).save()
