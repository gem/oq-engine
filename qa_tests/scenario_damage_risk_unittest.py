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

from lxml import etree

from openquake.nrml import nrml_schema_file
from openquake.xml import NRML_NS
from openquake.db.models import OqJob

from tests.utils import helpers

OUTPUT_DIR = helpers.demo_file("scenario_damage_risk/computed_output")


class ScenarioDamageRiskQATest(unittest.TestCase):
    """
    QA test for the Scenario Damage Risk calculator.
    """

    def test_scenario_damage_risk(self):
        cfg = helpers.demo_file("scenario_damage_risk/config.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        ds = self._ds("a1", "no_damage")

        self._close_to(1083.2878086376, float(ds.get("mean")))
        self._close_to(926.8114705410, float(ds.get("stddev")))

        ds = self._ds("a1", "LS1")

        self._close_to(1193.2879148011, float(ds.get("mean")))
        self._close_to(471.4571312182, float(ds.get("stddev")))

        ds = self._ds("a1", "LS2")

        self._close_to(723.4242765613, float(ds.get("mean")))
        self._close_to(755.9750053225, float(ds.get("stddev")))

        ds = self._ds("a2", "no_damage")

        self._close_to(42.3377447524, float(ds.get("mean")))
        self._close_to(70.0892678237, float(ds.get("stddev")))

        ds = self._ds("a2", "LS1")

        self._close_to(730.4180238456, float(ds.get("mean")))
        self._close_to(494.7514529615, float(ds.get("stddev")))

        ds = self._ds("a2", "LS2")

        self._close_to(1227.2442314019, float(ds.get("mean")))
        self._close_to(549.4191085089, float(ds.get("stddev")))

        ds = self._ds("a3", "no_damage")

        self._close_to(264.2663623864, float(ds.get("mean")))
        self._close_to(228.8391071035, float(ds.get("stddev")))

        ds = self._ds("a3", "LS1")

        self._close_to(451.0114061630, float(ds.get("mean")))
        self._close_to(140.2229465594, float(ds.get("stddev")))

        ds = self._ds("a3", "LS2")

        self._close_to(284.7222314506, float(ds.get("mean")))
        self._close_to(248.9585500745, float(ds.get("stddev")))

    def _ds(self, asset_ref, damage_state):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-asset-%s.xml" % (OUTPUT_DIR, job.id)

        xpath = ("{%(ns)s}dmgDistPerAsset/{%(ns)s}DDNode/"
            "{%(ns)s}asset[@assetRef='" + asset_ref + "']/"
            "{%(ns)s}damage[@ds='" + damage_state + "']")

        return self._get(filename, xpath)

    def _close_to(self, expected, actual):
        self.assertTrue(numpy.allclose(actual, expected, atol=0.0, rtol=0.001))

    def _verify_damage_states(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-asset-%s.xml" % (OUTPUT_DIR, job.id)

        xpath = ('{%(ns)s}dmgDistPerAsset/{%(ns)s}damageStates')
        dmg_states = self._get(filename, xpath).text.split()

        self.assertEquals(["no_damage", "LS1", "LS2"], dmg_states)

    def _verify_job_succeeded(self):
        job = OqJob.objects.latest("id")
        self.assertEqual("succeeded", job.status)

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ["--output-type=xml"])
        self.assertEquals(0, ret_code)

    def _get(self, filename, xpath):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)

        tree = etree.parse(filename, parser=parser)

        return tree.getroot().find(xpath % {'ns': NRML_NS})
