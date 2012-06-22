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

from openquake.nrml.utils import nrml_schema_file
from openquake.xml import NRML_NS
from openquake.db.models import OqJob

from tests.utils import helpers

OUTPUT_DIR = helpers.demo_file("scenario_damage_risk/computed_output")


class ScenarioDamageRiskQATest(unittest.TestCase):
    """
    QA test for the Scenario Damage Risk calculator.
    """

    def test_hazard_input_on_exposure_sites(self):
        cfg = helpers.demo_file(
            "scenario_damage_risk/config_hzr_exposure.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()

    def test_scenario_damage_con(self):
        cfg = helpers.demo_file("scenario_damage_risk/config.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        self._verify_dist_per_asset_con()
        self._verify_dist_per_taxonomy_con()
        self._verify_total_dist_con()
        self._verify_collapse_map_con()

    def _verify_collapse_map_con(self):
        mean, stddev = self._map_asset_values("a1")

        self._close_to(329.3743174305, mean)
        self._close_to(347.3929450270, stddev)

        mean, stddev = self._map_asset_values("a2")

        self._close_to(1270.1751143182, mean)
        self._close_to(575.8724057319, stddev)

        mean, stddev = self._map_asset_values("a3")

        self._close_to(195.4618668074, mean)
        self._close_to(253.9130901018, stddev)

    def _verify_total_dist_con(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-total-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        ds = self._ds_td("no_damage", root)

        self._close_to(2036.6565789692, float(ds.get("mean")))
        self._close_to(1075.3192939160, float(ds.get("stddev")))

        ds = self._ds_td("LS1", root)

        self._close_to(2168.3321224748, float(ds.get("mean")))
        self._close_to(1076.4342601834, float(ds.get("stddev")))

        ds = self._ds_td("LS2", root)

        self._close_to(1795.0112985561, float(ds.get("mean")))
        self._close_to(687.0910669304, float(ds.get("stddev")))

    def _verify_dist_per_asset_con(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-asset-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        ds = self._ds_dda("a1", "no_damage", root)

        self._close_to(1562.6067550208, float(ds.get("mean")))
        self._close_to(968.9350257674, float(ds.get("stddev")))

        ds = self._ds_dda("a1", "LS1", root)

        self._close_to(1108.0189275488, float(ds.get("mean")))
        self._close_to(652.7358505746, float(ds.get("stddev")))

        ds = self._ds_dda("a1", "LS2", root)

        self._close_to(329.3743174305, float(ds.get("mean")))
        self._close_to(347.3929450270, float(ds.get("stddev")))

        ds = self._ds_dda("a2", "no_damage", root)

        self._close_to(56.7201291212, float(ds.get("mean")))
        self._close_to(117.7802813522, float(ds.get("stddev")))

        ds = self._ds_dda("a2", "LS1", root)

        self._close_to(673.1047565606, float(ds.get("mean")))
        self._close_to(485.2023172324, float(ds.get("stddev")))

        ds = self._ds_dda("a2", "LS2", root)

        self._close_to(1270.1751143182, float(ds.get("mean")))
        self._close_to(575.8724057319, float(ds.get("stddev")))

        ds = self._ds_dda("a3", "no_damage", root)

        self._close_to(417.3296948271, float(ds.get("mean")))
        self._close_to(304.4769498434, float(ds.get("stddev")))

        ds = self._ds_dda("a3", "LS1", root)

        self._close_to(387.2084383654, float(ds.get("mean")))
        self._close_to(181.1415598664, float(ds.get("stddev")))

        ds = self._ds_dda("a3", "LS2", root)

        self._close_to(195.4618668074, float(ds.get("mean")))
        self._close_to(253.91309010185, float(ds.get("stddev")))

    def _verify_dist_per_taxonomy_con(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-taxonomy-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        ds = self._ds_ddt("RC", "no_damage", root)

        self._close_to(56.7201291212, float(ds.get("mean")))
        self._close_to(117.7802813522, float(ds.get("stddev")))

        ds = self._ds_ddt("RC", "LS1", root)

        self._close_to(673.1047565606, float(ds.get("mean")))
        self._close_to(485.2023172324, float(ds.get("stddev")))

        ds = self._ds_ddt("RC", "LS2", root)

        self._close_to(1270.1751143182, float(ds.get("mean")))
        self._close_to(575.8724057319, float(ds.get("stddev")))

        ds = self._ds_ddt("RM", "no_damage", root)

        self._close_to(1979.9364498479, float(ds.get("mean")))
        self._close_to(1103.6005152909, float(ds.get("stddev")))

        ds = self._ds_ddt("RM", "LS1", root)

        self._close_to(1495.2273659142, float(ds.get("mean")))
        self._close_to(745.3252495731, float(ds.get("stddev")))

        ds = self._ds_ddt("RM", "LS2", root)

        self._close_to(524.8361842379, float(ds.get("mean")))
        self._close_to(401.9195159565, float(ds.get("stddev")))

    def test_scenario_damage_dsc(self):
        cfg = helpers.demo_file("scenario_damage_risk/config_discrete.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_damage_states()

        self._verify_dist_per_asset_dsc()
        self._verify_dist_per_taxonomy_dsc()
        self._verify_total_dist_dsc()
        self._verify_collapse_map_dsc()

    def _verify_collapse_map_dsc(self):
        mean, stddev = self._map_asset_values("a1")

        self._close_to(675.8929310273, mean)
        self._close_to(556.7659393118, stddev)

        mean, stddev = self._map_asset_values("a2")

        self._close_to(907.46737796, mean)
        self._close_to(417.30737837, stddev)

        mean, stddev = self._map_asset_values("a3")

        self._close_to(309.93823125, mean)
        self._close_to(246.84424913, stddev)

    def _verify_total_dist_dsc(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-total-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        ds = self._ds_td("no_damage", root)

        self._close_to(1445.1370815035, float(ds.get("mean")))
        self._close_to(824.7812010370, float(ds.get("stddev")))

        ds = self._ds_td("LS1", root)

        self._close_to(2661.5643782540, float(ds.get("mean")))
        self._close_to(374.0010314384, float(ds.get("stddev")))

        ds = self._ds_td("LS2", root)

        self._close_to(1893.2985402425, float(ds.get("mean")))
        self._close_to(661.8114364615, float(ds.get("stddev")))

    def _verify_dist_per_taxonomy_dsc(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-taxonomy-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        ds = self._ds_ddt("RM", "no_damage", root)

        self._close_to(1100.2285892246, float(ds.get("mean")))
        self._close_to(880.2774984768, float(ds.get("stddev")))

        ds = self._ds_ddt("RM", "LS1", root)

        self._close_to(1913.9402484967, float(ds.get("mean")))
        self._close_to(296.2197411105, float(ds.get("stddev")))

        ds = self._ds_ddt("RM", "LS2", root)

        self._close_to(985.8311622787, float(ds.get("mean")))
        self._close_to(616.5632580754, float(ds.get("stddev")))

        ds = self._ds_ddt("RC", "no_damage", root)

        self._close_to(344.9084922789, float(ds.get("mean")))
        self._close_to(300.6112307894, float(ds.get("stddev")))

        ds = self._ds_ddt("RC", "LS1", root)

        self._close_to(747.6241297573, float(ds.get("mean")))
        self._close_to(144.6485296163, float(ds.get("stddev")))

        ds = self._ds_ddt("RC", "LS2", root)

        self._close_to(907.4673779638, float(ds.get("mean")))
        self._close_to(417.3073783656, float(ds.get("stddev")))

    def _verify_dist_per_asset_dsc(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-asset-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        ds = self._ds_dda("a1", "no_damage", root)

        self._close_to(875.8107820287, float(ds.get("mean")))
        self._close_to(757.5401928931, float(ds.get("stddev")))

        ds = self._ds_dda("a1", "LS1", root)

        self._close_to(1448.2962869440, float(ds.get("mean")))
        self._close_to(256.1531925368, float(ds.get("stddev")))

        ds = self._ds_dda("a1", "LS2", root)

        self._close_to(675.8929310273, float(ds.get("mean")))
        self._close_to(556.7659393118, float(ds.get("stddev")))

        ds = self._ds_dda("a2", "no_damage", root)

        self._close_to(344.9084922789, float(ds.get("mean")))
        self._close_to(300.6112307894, float(ds.get("stddev")))

        ds = self._ds_dda("a2", "LS1", root)

        self._close_to(747.6241297573, float(ds.get("mean")))
        self._close_to(144.6485296163, float(ds.get("stddev")))

        ds = self._ds_dda("a2", "LS2", root)

        self._close_to(907.4673779638, float(ds.get("mean")))
        self._close_to(417.3073783656, float(ds.get("stddev")))

        ds = self._ds_dda("a3", "no_damage", root)

        self._close_to(224.4178071959, float(ds.get("mean")))
        self._close_to(220.6516140873, float(ds.get("stddev")))

        ds = self._ds_dda("a3", "LS1", root)

        self._close_to(465.6439615527, float(ds.get("mean")))
        self._close_to(136.9281761924, float(ds.get("stddev")))

        ds = self._ds_dda("a3", "LS2", root)

        self._close_to(309.9382312514, float(ds.get("mean")))
        self._close_to(246.8442491255, float(ds.get("stddev")))

    def _map_asset_values(self, asset_ref):
        job = OqJob.objects.latest("id")
        filename = "%s/collapse-map-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        xpath_mean = ("//nrml:cf[@assetRef='" + asset_ref + "']/nrml:mean")
        xpath_stddev = ("//nrml:cf[@assetRef='" + asset_ref + "']/nrml:stdDev")

        return float(self._get(root, xpath_mean).text), float(
                self._get(root, xpath_stddev).text)

    def _ds_td(self, damage_state, root):
        xpath = ("nrml:totalDmgDist/"
            "nrml:damage[@ds='" + damage_state + "']")

        return self._get(root, xpath)

    def _ds_dda(self, asset_ref, damage_state, root):
        xpath = ("nrml:dmgDistPerAsset/nrml:DDNode/"
            "nrml:asset[@assetRef='" + asset_ref + "']/"
            "nrml:damage[@ds='" + damage_state + "']")

        return self._get(root, xpath)

    def _ds_ddt(self, taxonomy, damage_state, root):
        xpath = ("nrml:dmgDistPerTaxonomy/nrml:DDNode[nrml:taxonomy='"
            + taxonomy + "']/nrml:damage[@ds='" + damage_state + "']")

        return self._get(root, xpath)

    def _close_to(self, expected, actual):
        self.assertTrue(numpy.allclose(actual, expected, atol=0.0, rtol=0.001))

    def _verify_damage_states(self):
        job = OqJob.objects.latest("id")
        filename = "%s/dmg-dist-asset-%s.xml" % (OUTPUT_DIR, job.id)
        root = self._root(filename)

        xpath = ("//nrml:dmgDistPerAsset//nrml:damageStates")
        dmg_states = self._get(root, xpath).text.split()

        self.assertEquals(["no_damage", "LS1", "LS2"], dmg_states)

    def _verify_job_succeeded(self):
        job = OqJob.objects.latest("id")
        self.assertEqual("succeeded", job.status)

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ["--output-type=xml"])
        self.assertEquals(0, ret_code)

    def _root(self, filename):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)
        return etree.parse(filename, parser=parser)

    def _get(self, root, xpath):
        return root.find(xpath, namespaces={"nrml": NRML_NS})
