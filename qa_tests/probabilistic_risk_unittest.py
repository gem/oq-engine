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
import numpy
import unittest

from lxml import etree

from openquake.db.models import OqJob
from openquake.nrml import nrml_schema_file
from openquake.xml import NRML_NS
from tests.utils import helpers

OUTPUT_DIR = helpers.demo_file(
    "probabilistic_event_based_risk/computed_output")


class ProbabilisticEventBasedRiskQATest(unittest.TestCase):
    """QA tests for the Probabilistic Event Based Risk calculator."""

    def test_probabilistic_risk(self):
        cfg = helpers.demo_file(
            "probabilistic_event_based_risk/config_qa.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()
        self._verify_loss_maps()

    def _verify_job_succeeded(self):
        job = OqJob.objects.latest("id")
        self.assertEqual("succeeded", job.status)

        expected_files = [
            "loss_curves-block-#%s-block#0.xml" % job.id,
            "loss_curves-loss-block-#%s-block#0.xml" % job.id,
            "losses_at-0.99.xml"
        ]

        for f in expected_files:
            self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, f)))

    def _verify_loss_maps(self):

        def xpath(asset_ref):
            return ("{%(ns)s}riskResult/{%(ns)s}lossMap/"
                "{%(ns)s}LMNode/{%(ns)s}loss[@assetRef='"
                + asset_ref + "']/{%(ns)s}value")

        filename = "%s/losses_at-0.99.xml" % OUTPUT_DIR
        expected_closs = 78.1154725900

        closs = float(self._get(filename, xpath("a1")))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=0.05))

        expected_closs = 36.2507008221

        closs = float(self._get(filename, xpath("a2")))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=0.05))

        expected_closs = 23.4782545574

        closs = float(self._get(filename, xpath("a3")))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=0.05))

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ["--output-type=xml"])
        self.assertEquals(0, ret_code)

    def _get(self, filename, xpath):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)

        tree = etree.parse(filename, parser=parser)

        return tree.getroot().find(xpath % {'ns': NRML_NS}).text
