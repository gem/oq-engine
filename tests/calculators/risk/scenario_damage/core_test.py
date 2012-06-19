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
import os

from django.contrib.gis import geos

from openquake import kvs
from openquake.db import models
from openquake.shapes import Site, GridPoint
from openquake.engine import JobContext
from openquake.db.models import DmgDistPerAsset, DmgDistPerAssetData
from openquake.kvs.tokens import ground_motion_values_key
from openquake.calculators.risk.general import Block
from openquake.calculators.risk.scenario_damage.core import (
    ScenarioDamageRiskCalculator, compute_gmv_fractions)

from tests.utils import helpers

BLOCK_ID = 1


class ScenarioDamageRiskCalculatorTestCase(
    unittest.TestCase, helpers.DbTestCase):

    def setUp(self):
        inputs = [("fragility", ""), ("exposure", "")]
        self.job = self.setup_classic_job(inputs=inputs)

        kvs.mark_job_as_current(self.job.id)
        kvs.cache_gc(self.job.id)

        self.site = Site(1.0, 1.0)
        block = Block(self.job.id, BLOCK_ID, [self.site])
        block.to_kvs()

        # this region contains a single site, that is exactly
        # a site with longitude == 1.0 and latitude == 1.0
        params = {"REGION_VERTEX": "1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0",
                "REGION_GRID_SPACING": "0.5", "BASE_PATH": ".",
                "OUTPUT_DIR": "."}

        self.job_ctxt = JobContext(params, self.job.id, oq_job=self.job)

        self.em = self._store_em()
        self._store_gmvs([0.40, 0.30, 0.45, 0.35, 0.40])

        self.calculator = ScenarioDamageRiskCalculator(self.job_ctxt)

        # just stubbing out some preprocessing stuff...
        ScenarioDamageRiskCalculator.store_exposure_assets = lambda self: None
        ScenarioDamageRiskCalculator.store_fragility_model = lambda self: None
        ScenarioDamageRiskCalculator.partition = lambda self: None

    def test_compute_risk_dda_con(self):
        # test the damage distribution per asset with a continuous
        # fragility model
        fm = self._store_con_fmodel()

        self.calculator.pre_execute()
        self.calculator.compute_risk(BLOCK_ID, fmodel=fm)

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

    def test_compute_risk_dda_dsc(self):
        # test the damage distribution per asset with a discrete
        # fragility model
        fm = self._store_dsc_fmodel()

        self.calculator.pre_execute()
        self.calculator.compute_risk(BLOCK_ID, fmodel=fm)

        [dda] = DmgDistPerAsset.objects.filter(output__oq_job=self.job.id,
                output__output_type="dmg_dist_per_asset")

        self.assertEquals(["no_damage", "LS1", "LS2"], dda.dmg_states)

        [exposure] = self.em.exposuredata_set.filter(asset_ref="A")
        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="no_damage")

        self._close_to(68.0, data.mean)
        self._close_to(8.5513157, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS1")

        self._close_to(21.0, data.mean)
        self._close_to(4.2756578, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS2")

        self._close_to(11.0, data.mean)
        self._close_to(4.2756578, data.stddev)

        [exposure] = self.em.exposuredata_set.filter(asset_ref="B")
        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="no_damage")

        self._close_to(30.4, data.mean)
        self._close_to(3.4, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS1")

        self._close_to(3.9, data.mean)
        self._close_to(1.4, data.stddev)

        [data] = DmgDistPerAssetData.objects.filter(dmg_dist_per_asset=dda,
                exposure_data=exposure, dmg_state="LS2")

        self._close_to(5.7, data.mean)
        self._close_to(2.1, data.stddev)

    def test_dda_iml_above_range(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is higher than the highest
        # intensity measure level defined in the model (in this
        # particular case 0.7). Given this condition, to compute
        # the fractions of buildings we use the highest intensity
        # measure level defined in the model (0.7 in this case)

        [ism] = models.inputs4job(self.job.id, input_type="fragility")

        fmodel = models.FragilityModel(
            owner=ism.owner, input=ism, imls=[0.1, 0.3, 0.5, 0.7],
            imt="mmi", lss=["LS1"], format="discrete")

        fmodel.save()

        func = models.Ffd(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS1", poes=[0.05, 0.20, 0.50, 1.00], lsi=1)

        func.save()

        self._close_to(compute_gmv_fractions([func], 0.7),
                compute_gmv_fractions([func], 0.8))

    def test_dda_iml_below_range_damage_limit_undefined(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1). Given this condition, and without
        # having the no_damage_limit attribute defined, the
        # fractions of buildings is 100% no_damage and 0% for the
        # remaining limit states defined in the model
        [ism] = models.inputs4job(self.job.id, input_type="fragility")

        fmodel = models.FragilityModel(
            owner=ism.owner, input=ism, imls=[0.1, 0.3, 0.5, 0.7],
            imt="mmi", lss=["LS1"], format="discrete")

        fmodel.save()

        func = models.Ffd(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS1", poes=[0.05, 0.20, 0.50, 1.00], lsi=1)

        func.save()

        self._close_to([1.0, 0.0],
            compute_gmv_fractions([func], 0.05))

    def test_dda_iml_below_range_damage_limit_defined(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1) and lower than the no_damage_limit
        # attribute defined in the model. Given this condition, the
        # fractions of buildings is 100% no_damage and 0% for the
        # remaining limit states defined in the model.

        [ism] = models.inputs4job(self.job.id, input_type="fragility")

        fmodel = models.FragilityModel(
            owner=ism.owner, input=ism, imls=[0.1, 0.3, 0.5, 0.7],
            imt="mmi", lss=["LS1"], format="discrete", no_damage_limit=0.05)

        fmodel.save()

        func = models.Ffd(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS1", poes=[0.05, 0.20, 0.50, 1.00], lsi=1)

        func.save()

        self._close_to([1.0, 0.0],
            compute_gmv_fractions([func], 0.02))

    def test_gmv_between_no_damage_limit_and_first_iml(self):
        # corner case where we have a ground motion value
        # (that corresponds to the intensity measure level in the
        # fragility function) that is lower than the lowest
        # intensity measure level defined in the model (in this
        # particular case 0.1) but bigger than the no_damage_limit
        # attribute defined in the model. Given this condition, the
        # fractions of buildings is 97.5% no_damage and 2.5% for the
        # remaining limit states defined in the model.

        fm = self._store_dsc_fmodel()
        funcs = fm.ffd_set.filter(
            taxonomy="RC").order_by("lsi")

        self._close_to([0.975, 0.025, 0.],
            compute_gmv_fractions(funcs, 0.075))

    def test_post_execute_serialization(self):
        # when --output-type=xml is specified, we serialize results
        fm = self._store_con_fmodel()

        self.calculator.pre_execute()
        self.calculator.compute_risk(BLOCK_ID, fmodel=fm)

        # since the taxonomy data is computed and aggregated
        # per block in the execute() method and we are not
        # testing it here, just stubbing out some values to
        # produce the taxonomy distribution
        self.calculator.ddt_fractions = {"RC": numpy.array(
                [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])}

        # stubbing out also the total distribution
        self.calculator.total_fractions = numpy.array([[1.0, 0.0, 0.0]])

        self.job_ctxt.serialize_results_to = ["xml"]
        self.calculator.post_execute()

        paths = self._results_files()

        for path in paths:
            self.assertTrue(os.path.exists(path))
            os.unlink(path)

    def test_post_execute_no_serialization(self):
        # otherwise, just on database (default)
        fm = self._store_con_fmodel()

        # stubbing out the total distribution
        self.calculator.total_fractions = numpy.array([[1.0, 0.0, 0.0]])

        self.calculator.pre_execute()
        self.calculator.compute_risk(BLOCK_ID, fmodel=fm)
        self.calculator.post_execute()

        paths = self._results_files()

        for path in paths:
            self.assertFalse(os.path.exists(path))

    def _results_files(self):
        target_dir = os.path.join(self.job_ctxt.params.get("BASE_PATH"),
                self.job_ctxt.params.get("OUTPUT_DIR"))

        return [os.path.join(
            target_dir, "dmg-dist-asset-%s.xml" % self.job.id), os.path.join(
            target_dir, "dmg-dist-taxonomy-%s.xml" % self.job.id),
            os.path.join(target_dir, "dmg-dist-total-%s.xml" % self.job.id),
            os.path.join(target_dir, "collapse-map-%s.xml" % self.job.id)]

    def _close_to(self, expected, actual):
        self.assertTrue(numpy.allclose(actual, expected, atol=0.0, rtol=0.05))

    def _store_gmvs(self, gmvs):
        client = kvs.get_client()
        encoder = json.JSONEncoder()

        key = ground_motion_values_key(self.job.id, GridPoint(None, 0, 0))

        for gmv in gmvs:
            client.rpush(key, encoder.encode({"mag": gmv}))

    def _store_con_fmodel(self):
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

    def _store_dsc_fmodel(self):
        [ism] = models.inputs4job(self.job.id, input_type="fragility")

        fmodel = models.FragilityModel(
            owner=ism.owner, input=ism, imls=[0.1, 0.3, 0.5, 0.7],
            imt="mmi", lss=["LS1", "LS2"], format="discrete",
            no_damage_limit=0.05)

        fmodel.save()

        models.Ffd(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS2", poes=[0.00, 0.05, 0.20, 0.50], lsi=2).save()

        models.Ffd(
            fragility_model=fmodel, taxonomy="RC",
            ls="LS1", poes=[0.05, 0.20, 0.50, 1.00], lsi=1).save()

        models.Ffd(
            fragility_model=fmodel, taxonomy="RM",
            ls="LS2", poes=[0.02, 0.07, 0.25, 0.60], lsi=2).save()

        models.Ffd(
            fragility_model=fmodel, taxonomy="RM",
            ls="LS1", poes=[0.03, 0.12, 0.42, 0.90], lsi=1).save()

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
