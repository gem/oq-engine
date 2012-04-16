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
import numpy

from django.contrib.gis import geos

from openquake import kvs
from openquake.db import models
from openquake.shapes import Site, GridPoint
from openquake.engine import JobContext
from openquake.db.models import DmgDistPerAsset, DmgDistPerAssetData
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

        self.em = self._store_em()
        self.fm = self._store_fmodel()
        self._store_gmvs([0.40, 0.30, 0.45, 0.35, 0.40])

        self.calculator = ScenarioDamageRiskCalculator(job_ctxt)

        # just stubbing out some preprocessing stuff...
        ScenarioDamageRiskCalculator.store_exposure_assets = lambda self: None
        ScenarioDamageRiskCalculator.store_fragility_model = lambda self: None
        ScenarioDamageRiskCalculator.partition = lambda self: None

    @classmethod
    def setUpClass(cls):
        inputs = [("fragility", ""), ("exposure", "")]
        cls.job = cls.setup_classic_job(inputs=inputs)

    def test_compute_risk(self):
        self.calculator.pre_execute()
        self.calculator.compute_risk(BLOCK_ID, fmodel=self.fm)

        [dda] = DmgDistPerAsset.objects.filter(output__oq_job=self.job.id,
                output__output_type="dmg_dist_per_asset")

        self.assertEquals(["no_damage", "LS1", "LS2"], dda.dmg_states)

        [exposure] = self.em.exposuredata_set.filter(asset_ref="A")
        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="no_damage")

        self._close_to(1.00563, data.mean)
        self._close_to(1.61341, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS1")

        self._close_to(34.80851, data.mean)
        self._close_to(18.34906, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS2")

        self._close_to(64.18586, data.mean)
        self._close_to(19.83963, data.stddev)

        [exposure] = self.em.exposuredata_set.filter(asset_ref="B")
        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="no_damage")

        self._close_to(3.64527, data.mean)
        self._close_to(3.35330, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS1")

        self._close_to(17.10494, data.mean)
        self._close_to(4.63604, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS2")

        self._close_to(19.24979, data.mean)
        self._close_to(7.78725, data.stddev)

    def _close_to(self, expected, actual):
        self.assertTrue(numpy.allclose(actual, expected, atol=0.0, rtol=0.05))

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
            ls="LS2", mean="0.35", stddev="0.10", lsi=2).save()

        models.Ffc(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS1", mean="0.20", stddev="0.05", lsi=1).save()

        models.Ffc(
            fragility_model=fmodel, taxonomy="RM",
            ls="LS2", mean="0.40", stddev="0.12", lsi=2).save()

        models.Ffc(
            fragility_model=fmodel, taxonomy="RM",
            ls="LS1", mean="0.25", stddev="0.08", lsi=1).save()

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
            asset_ref="A", number_of_units=100, stco=1,
            site=geos.GEOSGeometry(self.site.point.to_wkt()), reco=1).save()

        models.ExposureData(
            exposure_model=em, taxonomy="RM",
            asset_ref="B", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(self.site.point.to_wkt()), reco=1).save()

        return em
