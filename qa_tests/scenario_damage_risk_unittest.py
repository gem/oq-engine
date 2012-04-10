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

    def test_scenario_damage_risk_con(self):
        cfg = helpers.demo_file("scenario_damage_risk/config.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        [asset] = self._asset("a1")
        [data] = self._data(asset, "no_damage")

        self._close_to(1083.2878086376, data.mean)
        self._close_to(926.8114705410, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(1193.2879148011, data.mean)
        self._close_to(471.4571312182, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(723.4242765613, data.mean)
        self._close_to(755.9750053225, data.stddev)

        [asset] = self._asset("a2")
        [data] = self._data(asset, "no_damage")

        self._close_to(42.3377447524, data.mean)
        self._close_to(70.0892678237, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(730.4180238456, data.mean)
        self._close_to(494.7514529615, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(1227.2442314019, data.mean)
        self._close_to(549.4191085089, data.stddev)

        [asset] = self._asset("a3")
        [data] = self._data(asset, "no_damage")

        self._close_to(264.2663623864, data.mean)
        self._close_to(228.8391071035, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(451.0114061630, data.mean)
        self._close_to(140.2229465594, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(284.7222314506, data.mean)
        self._close_to(248.9585500745, data.stddev)

    def test_scenario_damage_risk_dsc(self):
        cfg = helpers.demo_file("scenario_damage_risk/config_discrete.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        [asset] = self._asset("a1")
        [data] = self._data(asset, "no_damage")

        self._close_to(554.6860951500, data.mean)
        self._close_to(598.7552048028, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(1399.3356341082, data.mean)
        self._close_to(349.3604258216, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(1045.9782707418, data.mean)
        self._close_to(749.3971884847, data.stddev)

        [asset] = self._asset("a2")
        [data] = self._data(asset, "no_damage")

        self._close_to(354.7536330800, data.mean)
        self._close_to(257.9890985575, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(779.0404984000, data.mean)
        self._close_to(153.3343303635, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(866.2058685200, data.mean)
        self._close_to(398.0973556984, data.stddev)

        [asset] = self._asset("a3")
        [data] = self._data(asset, "no_damage")

        self._close_to(108.3440263950, data.mean)
        self._close_to(122.0563889256, data.stddev)

        [data] = self._data(asset, "LS1")

        self._close_to(477.5115825656, data.mean)
        self._close_to(138.8593089805, data.stddev)

        [data] = self._data(asset, "LS2")

        self._close_to(414.1443910394, data.mean)
        self._close_to(232.3139816472, data.stddev)

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
