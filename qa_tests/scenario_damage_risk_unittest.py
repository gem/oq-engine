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

    def test_dda_con(self):
        cfg = helpers.demo_file("scenario_damage_risk/config.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        ds = self._ds("a1", "no_damage")

        self._close_to(1562.6067550208, float(ds.get("mean")))
        self._close_to(968.9350257674, float(ds.get("stddev")))

        ds = self._ds("a1", "LS1")

        self._close_to(1108.0189275488, float(ds.get("mean")))
        self._close_to(652.7358505746, float(ds.get("stddev")))

        ds = self._ds("a1", "LS2")

        self._close_to(329.3743174305, float(ds.get("mean")))
        self._close_to(347.3929450270, float(ds.get("stddev")))

        ds = self._ds("a2", "no_damage")

        self._close_to(56.7201291212, float(ds.get("mean")))
        self._close_to(117.7802813522, float(ds.get("stddev")))

        ds = self._ds("a2", "LS1")

        self._close_to(673.1047565606, float(ds.get("mean")))
        self._close_to(485.2023172324, float(ds.get("stddev")))

        ds = self._ds("a2", "LS2")

        self._close_to(1270.1751143182, float(ds.get("mean")))
        self._close_to(575.8724057319, float(ds.get("stddev")))

        ds = self._ds("a3", "no_damage")

        self._close_to(417.3296948271, float(ds.get("mean")))
        self._close_to(304.4769498434, float(ds.get("stddev")))

        ds = self._ds("a3", "LS1")

        self._close_to(387.2084383654, float(ds.get("mean")))
        self._close_to(181.1415598664, float(ds.get("stddev")))

        ds = self._ds("a3", "LS2")

        self._close_to(195.4618668074, float(ds.get("mean")))
        self._close_to(253.91309010185, float(ds.get("stddev")))

    def test_dda_dsc(self):
        cfg = helpers.demo_file("scenario_damage_risk/config_discrete.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        ds = self._ds("a1", "no_damage")

        self._close_to(875.8107820287, float(ds.get("mean")))
        self._close_to(757.5401928931, float(ds.get("stddev")))

        ds = self._ds("a1", "LS1")

        self._close_to(1448.2962869440, float(ds.get("mean")))
        self._close_to(256.1531925368, float(ds.get("stddev")))

        ds = self._ds("a1", "LS2")

        self._close_to(675.8929310273, float(ds.get("mean")))
        self._close_to(556.7659393118, float(ds.get("stddev")))

        ds = self._ds("a2", "no_damage")

        self._close_to(344.9084922789, float(ds.get("mean")))
        self._close_to(300.6112307894, float(ds.get("stddev")))

        ds = self._ds("a2", "LS1")

        self._close_to(747.6241297573, float(ds.get("mean")))
        self._close_to(144.6485296163, float(ds.get("stddev")))

        ds = self._ds("a2", "LS2")

        self._close_to(907.4673779638, float(ds.get("mean")))
        self._close_to(417.3073783656, float(ds.get("stddev")))

        ds = self._ds("a3", "no_damage")

        self._close_to(224.4178071959, float(ds.get("mean")))
        self._close_to(220.6516140873, float(ds.get("stddev")))

        ds = self._ds("a3", "LS1")

        self._close_to(465.6439615527, float(ds.get("mean")))
        self._close_to(136.9281761924, float(ds.get("stddev")))

        ds = self._ds("a3", "LS2")

        self._close_to(309.9382312514, float(ds.get("mean")))
        self._close_to(246.8442491255, float(ds.get("stddev")))

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
