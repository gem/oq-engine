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


import os
import tempfile
import unittest

from django.contrib.gis import geos
from openquake import shapes
from openquake.db import models
from openquake.output.scenario_damage import DmgDistPerAssetXMLWriter

from tests.utils import helpers


class DmgDistPerAssetXMLWriterTestCase(unittest.TestCase, helpers.DbTestCase):

    job = None

    @classmethod
    def setUpClass(cls):
        inputs = [("exposure", "")]
        cls.job = cls.setup_classic_job(inputs=inputs)

    def setUp(self):
        self.data = []
        self.dda = None

    def test_serialize(self):
# TODO: 1. map nrml/schema/examples/dmg-dist-per-asset.xml DONE
#       2. check results
#       3. refactoring
#       4. validation
#       5. serialization with no data
        damage_states = [
            "no_damage",
            "slight",
            "moderate",
            "extensive",
            "complete"]

        writer = DmgDistPerAssetXMLWriter("p.txt",
                "ebl1", damage_states)

        output = models.Output(
            owner=self.job.owner,
            oq_job=self.job,
            display_name="",
            db_backed=True,
            output_type="dmg_dist_per_asset")

        output.save()

        self.dda = models.DmgDistPerAsset(
            output=output,
            dmg_states=damage_states)

        self.dda.save()

        asset_1, asset_2, asset_3 = self.make_assets()

        self.make_data(asset_1, "no_damage", 1.0, 1.6)
        self.make_data(asset_1, "slight", 34.8, 18.3)
        self.make_data(asset_1, "moderate", 64.2, 19.8)
        self.make_data(asset_1, "extensive", 64.3, 19.7)
        self.make_data(asset_1, "complete", 64.3, 19.7)

        self.make_data(asset_2, "no_damage", 1.0, 1.6)
        self.make_data(asset_2, "slight", 34.8, 18.3)
        self.make_data(asset_2, "moderate", 64.2, 19.8)
        self.make_data(asset_2, "extensive", 64.3, 19.7)
        self.make_data(asset_2, "complete", 64.3, 19.7)

        self.make_data(asset_3, "no_damage", 1.1, 1.7)
        self.make_data(asset_3, "slight", 34.9, 18.4)
        self.make_data(asset_3, "moderate", 64.3, 19.7)
        self.make_data(asset_3, "extensive", 64.3, 19.7)
        self.make_data(asset_3, "complete", 64.3, 19.7)

        writer.serialize(self.data)

    def make_assets(self):
        [ism] = models.inputs4job(self.job.id, input_type="exposure")

        em = models.ExposureModel(
            owner=ism.owner, input=ism,
            name="AAA", category="single_asset",
            reco_type="aggregated", reco_unit="USD",
            stco_type="aggregated", stco_unit="USD")

        em.save()

        site_1 = shapes.Site(-116.0, 41.0)
        site_2 = shapes.Site(-117.0, 42.0)

        asset_1 = models.ExposureData(
            exposure_model=em, taxonomy="RC",
            asset_ref="asset_1", number_of_units=100, stco=1,
            site=geos.GEOSGeometry(site_1.point.to_wkt()), reco=1)

        asset_2 = models.ExposureData(
            exposure_model=em, taxonomy="RM",
            asset_ref="asset_2", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(site_2.point.to_wkt()), reco=1)

        asset_3 = models.ExposureData(
            exposure_model=em, taxonomy="RM",
            asset_ref="asset_3", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(site_2.point.to_wkt()), reco=1)

        asset_1.save()
        asset_2.save()
        asset_3.save()

        return asset_1, asset_2, asset_3

    def make_data(self, asset, dmg_state, mean, stddev):
        data = models.DmgDistPerAssetData(
            dmg_dist_per_asset = self.dda,
            exposure_data = asset,
            dmg_state = dmg_state,
            mean = mean,
            stddev = stddev,
            location = asset.site)

        data.save()
        self.data.append(data)
