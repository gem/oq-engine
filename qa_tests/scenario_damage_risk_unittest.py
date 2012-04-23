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
import numpy

from openquake.db import models
from openquake.db.models import OqJob
from openquake.db.models import (
DmgDistPerAsset, DmgDistPerAssetData, ExposureModel)

from tests.utils import helpers


class ScenarioDamageRiskQATest(unittest.TestCase):
    """
    QA test for the Scenario Damage Risk calculator.
    """

    def test_scenario_damage_risk(self):
        cfg = helpers.demo_file("scenario_damage_risk/config.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        [asset] = self._asset("a1")
        [data] = self._data(asset, "no_damage")

        self._close_to(1562.6067550208, data.mean)
        self._close_to(968.9350257674, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(1108.0189275488, data.mean)
        self._close_to(652.7358505746, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(329.3743174305, data.mean)
        self._close_to(347.3929450270, data.stddev)

        [asset] = self._asset("a2")
        [data] = self._data(asset, "no_damage")

        self._close_to(56.7201291212, data.mean)
        self._close_to(117.7802813522, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(673.1047565606, data.mean)
        self._close_to(485.2023172324, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(1270.1751143182, data.mean)
        self._close_to(575.8724057319, data.stddev)

        [asset] = self._asset("a3")
        [data] = self._data(asset, "no_damage")

        self._close_to(417.3296948271, data.mean)
        self._close_to(304.4769498434, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(387.2084383654, data.mean)
        self._close_to(181.1415598664, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(195.4618668074, data.mean)
        self._close_to(253.9130901018, data.stddev)

    def _asset(self, asset_ref):
        job = OqJob.objects.latest("id")

        [ism] = models.inputs4job(job.id, input_type="exposure")
        [em] = ExposureModel.objects.filter(owner=ism.owner, input=ism)

        return em.exposuredata_set.filter(asset_ref=asset_ref)

    def _close_to(self, expected, actual):
        self.assertTrue(numpy.allclose(actual, expected, atol=0.0, rtol=0.001))

    def _data(self, asset, damage_state):
        job = OqJob.objects.latest("id")

        [dda] = DmgDistPerAsset.objects.filter(output__oq_job=job.id,
                output__output_type="dmg_dist_per_asset")

        return DmgDistPerAssetData.objects.filter(
            dmg_dist_per_asset=dda, exposure_data=asset,
            dmg_state=damage_state)

    def _verify_damage_states(self):
        job = OqJob.objects.latest("id")

        [dda] = DmgDistPerAsset.objects.filter(output__oq_job=job.id,
                output__output_type="dmg_dist_per_asset")

        self.assertEquals(["no_damage", "LS1", "LS2"], dda.dmg_states)

    def _verify_job_succeeded(self):
        job = OqJob.objects.latest("id")
        self.assertEqual("succeeded", job.status)

    def _run_job(self, config):
        ret_code = helpers.run_job(config)
        self.assertEquals(0, ret_code)
