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

from openquake.db.models import OqJob, Output
from openquake.export.risk import export_agg_loss_curve
from openquake.nrml import nrml_schema_file
from openquake.xml import NRML_NS, GML_NS
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
        self._verify_loss_ratio_curves()
        self._verify_aggregate_curve()

    def _verify_loss_ratio_curves(self):

        def xpath_poes(asset_ref):
            return ("{%(ns)s}riskResult/{%(ns)s}lossRatioCurveList/"
                "{%(ns)s}asset[@gml:id='" + asset_ref +
                "']/{%(ns)s}lossRatioCurves/{%(ns)s}"
                "lossRatioCurve/{%(ns)s}poE")

        def xpath_ratios(asset_ref):
            return ("{%(ns)s}riskResult/{%(ns)s}lossRatioCurveList/"
                "{%(ns)s}asset[@gml:id='" + asset_ref +
                "']/{%(ns)s}lossRatioCurves/"
                "{%(ns)s}lossRatioCurve/{%(ns)s}lossRatio")

        job = OqJob.objects.latest("id")

        filename = "%s/loss_curves-block-#%s-block#0.xml" % (
                OUTPUT_DIR, job.id)

        poes = [float(x) for x in self._get(
            filename, xpath_poes("a2")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            0.9999999586, 0.9996645695, 0.9975213681,
            0.9816858268, 0.8646666370, 0.8646704246,
            0.6321542453]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=0.05))

        loss_ratios = [float(x) for x in self._get(
            filename, xpath_ratios("a2")).split()]

        expected_loss_ratios = [0.0018204915, 0.0054614744,
            0.0091024573, 0.0127434402, 0.0163844231,
            0.0200254060, 0.0236663889, 0.0273073718,
            0.0309483547]

        self.assertTrue(numpy.allclose(
                loss_ratios, expected_loss_ratios, atol=0.0, rtol=0.05))

        poes = [float(x) for x in self._get(
                filename, xpath_poes("a3")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            1.0000000000, 1.0000000000, 1.0000000000,
            0.9999998875, 0.9999977397, 0.9998765914,
            0.9816858693]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=0.05))

        loss_ratios = [float(x) for x in self._get(
            filename, xpath_ratios("a3")).split()]

        expected_loss_ratios = [0.0014593438, 0.0043780315,
            0.0072967191, 0.0102154068, 0.0131340944,
            0.0160527820, 0.0189714697, 0.0218901573,
            0.0248088450]

        self.assertTrue(numpy.allclose(
                loss_ratios, expected_loss_ratios, atol=0.0, rtol=0.05))

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

    def _verify_aggregate_curve(self):
        job = OqJob.objects.latest("id")
        
        [output] = Output.objects.filter(
            oq_job=job.id,
            output_type="agg_loss_curve")

        export_agg_loss_curve(output, OUTPUT_DIR)
        filename = "%s/aggregate_loss_curve.xml" % OUTPUT_DIR

        xpath = "{%(ns)s}riskResult/{%(ns)s}aggregateLossCurve/{%(ns)s}poE"

        poes = [float(x) for x in self._get(filename, xpath).split()]

        expected_poes = [1.0000000000, 1.0000000000, 0.9999991685,
            0.9932621249, 0.9502177204, 0.8646647795,
            0.8646752036, 0.6321506245, 0.6321525149]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=0.05))

        xpath = "{%(ns)s}riskResult/{%(ns)s}aggregateLossCurve/{%(ns)s}loss"

        losses = [float(x) for x in self._get(filename, xpath).split()]

        expected_losses = [18.5629274028, 55.6887822085, 92.8146370142,
            129.9404918199, 167.0663466256, 204.1922014313,
            241.3180562370, 278.4439110427, 315.5697658484]

        self.assertTrue(numpy.allclose(
                losses, expected_losses, atol=0.0, rtol=0.05))

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ["--output-type=xml"])
        self.assertEquals(0, ret_code)

    def _get(self, filename, xpath):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)

        tree = etree.parse(filename, parser=parser)

        return tree.getroot().find(xpath % {"ns": NRML_NS},
                namespaces={"gml": GML_NS}).text
