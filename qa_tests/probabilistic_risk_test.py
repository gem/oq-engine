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
from shutil import rmtree

from openquake.db.models import OqJob, Output
from openquake.export.risk import export_agg_loss_curve
from openquake.nrml.utils import nrml_schema_file
from openquake.xml import NRML_NS, GML_NS
from tests.utils import helpers


from qa_tests.data.probabilistic_event_based_risk.test_data import (
    EXPECTED_LOSS_A1_MB, EXPECTED_LOSS_A2_MB, EXPECTED_LOSS_A3_MB,
    LOSS_CURVES_MB, LOSS_RATIOS_CURVES_MB, AGGREGATE_CURVE,
    LOSS_CURVES_MB_IL, LOSS_RATIOS_CURVES_MB_IL)

OUTPUT_DIR = helpers.demo_file(
    "probabilistic_event_based_risk/computed_output")
QA_OUTPUT_DIR = helpers.qa_file(
    "probabilistic_event_based_risk/computed_output")


class ProbabilisticEventBasedRiskQATest(unittest.TestCase):
    """QA tests for the Probabilistic Event Based Risk calculator."""

    def test_mean_based(self):
        try:
            cfg = helpers.qa_file(
            "probabilistic_event_based_risk/m_config.gem")

            self._run_job(cfg)
            job_id = OqJob.objects.latest('id').id
            [output] = Output.objects.filter(
                oq_job=job_id,
                output_type="agg_loss_curve")
            export_agg_loss_curve(output, QA_OUTPUT_DIR)
            expected_files = [
                "%s/loss_curves-block-#%s-block#0.xml" % (QA_OUTPUT_DIR,
                                                          job_id),
                "%s/loss_curves-loss-block-#%s-block#0.xml" % (QA_OUTPUT_DIR,
                                                                job_id),
                "%s/losses_at-0.99.xml" % QA_OUTPUT_DIR,

                "%s/aggregate_loss_curve.xml" % QA_OUTPUT_DIR
            ]

            self._verify_job_succeeded(expected_files)
            self._verify_loss_maps(expected_files[2], EXPECTED_LOSS_A1_MB,
                EXPECTED_LOSS_A2_MB, EXPECTED_LOSS_A3_MB)
            self._verify_loss_ratio_curves(expected_files[0],
                LOSS_RATIOS_CURVES_MB)
            self._verify_loss_curves(expected_files[1], LOSS_CURVES_MB)
            self._verify_aggregate_curve(expected_files[3])
        finally:
            # Cleaning generated results file.
            rmtree(QA_OUTPUT_DIR)

    #TODO Add/Complete the skipped QA Tests
    @unittest.skip
    def test_sampled_based(self):
        cfg = helpers.qa_file(
            "probabilistic_event_based_risk/config_qa.gem")

        self._run_job(cfg)
        self._verify_job_succeeded(QA_OUTPUT_DIR)
        self._verify_loss_maps(QA_OUTPUT_DIR, 0.05)
        self._verify_loss_ratio_curves(QA_OUTPUT_DIR, 0.10)
        self._verify_loss_curves(QA_OUTPUT_DIR, 0.10)
        self._verify_aggregate_curve(QA_OUTPUT_DIR, 0.05)

        # Cleaning generated results file.
        rmtree(QA_OUTPUT_DIR)


    def test_insured_loss_mean_based(self):
        try:
            cfg = helpers.qa_file(
                "probabilistic_event_based_risk/m_il_config.gem")
            self._run_job(cfg)
            job_id = OqJob.objects.latest('id').id

            [output] = Output.objects.filter(
                oq_job=job_id,
                output_type="agg_loss_curve")
            export_agg_loss_curve(output, QA_OUTPUT_DIR)
            expected_files = [
                "%s/loss_curves-block-#%s-block#0.xml" % (QA_OUTPUT_DIR,
                                                          job_id),
                "%s/loss_curves-loss-block-#%s-block#0.xml" % (QA_OUTPUT_DIR,
                                                               job_id),
                "%s/insured_loss_curves-insured-loss-block=#%s-block#0.xml" % (
                    QA_OUTPUT_DIR, job_id),

                "%s/loss_curves-insured-block=#%s-block#0.xml" % (
                    QA_OUTPUT_DIR, job_id),

                "%s/losses_at-0.99.xml" % QA_OUTPUT_DIR,

                "%s/aggregate_loss_curve.xml" % QA_OUTPUT_DIR
            ]
            self._verify_job_succeeded(expected_files)
            self._verify_loss_ratio_curves(expected_files[3],
                LOSS_RATIOS_CURVES_MB_IL)
            self._verify_loss_curves(expected_files[2], LOSS_CURVES_MB_IL)
        finally:
            rmtree(QA_OUTPUT_DIR)


    #TODO After PEB sample based has been fixed.
    @unittest.skip
    def test_insured_loss_sample_based(self):
        pass

    def test_hazard_computed_on_exposure_sites(self):
        # here we compute the hazard on locations
        # defined in the exposure file. For now, we just
        # check the job completes correctly.

        try:
            cfg = helpers.demo_file(
                "probabilistic_event_based_risk/config_hzr_exposure.gem")

            self._run_job(cfg)
            job_id = OqJob.objects.latest('id').id

            expected_files = [
                "%s/loss_curves-block-#%s-block#0.xml" % (OUTPUT_DIR,
                                                          job_id),
                "%s/loss_curves-loss-block-#%s-block#0.xml" % (OUTPUT_DIR,
                                                               job_id),
                "%s/losses_at-0.99.xml" % OUTPUT_DIR
            ]
            self._verify_job_succeeded(expected_files)
        finally:
            rmtree(OUTPUT_DIR)

    def _verify_loss_curves(self, filename, loss_curves):

        def xpath_poes(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:poE")

        def xpath_losses(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:loss")

        root = self._root(filename)
        LOSSES_INDEX = 0
        POES_INDEX = 1

        for i, loss_curve in enumerate(loss_curves, start=1):
            losses = [float(x) for x in self._get(
                root, xpath_losses("a%s" % i)).split()]
            poes = [float(x) for x in self._get(root,
                xpath_poes("a%s" % i)).split()]

            self.assertTrue(numpy.allclose(
                losses, loss_curve[LOSSES_INDEX], atol=0.0, rtol=0.05))
            self.assertTrue(numpy.allclose(
                poes, loss_curve[POES_INDEX], atol=0.0, rtol=0.05))

    def _verify_loss_ratio_curves(self, filename, loss_ratio_curves):

        def xpath_poes(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:poE")

        def xpath_ratios(asset_ref):
            return ("//nrml:asset[@gml:id='"
                    + asset_ref + "']//nrml:lossRatio")

        root = self._root(filename)

        LOSS_RATIO_INDEX = 0
        POES_INDEX = 1

        for i, loss_ratio_curve in enumerate(loss_ratio_curves, start=1):
            loss_ratios = [float(x) for x in self._get(
                root, xpath_ratios("a%s" % i)).split()]
            poes = [float(x) for x in self._get(
                root, xpath_poes("a%s" % i)).split()]

            self.assertTrue(numpy.allclose(
                loss_ratios, loss_ratio_curve[LOSS_RATIO_INDEX],
                atol=0.0, rtol=0.05))
            self.assertTrue(numpy.allclose(
                poes, loss_ratio_curve[POES_INDEX], atol=0.0, rtol=0.05))

    def _verify_job_succeeded(self, expected_files):
        job = OqJob.objects.latest("id")
        self.assertEqual("succeeded", job.status)

        for f in expected_files:
            self.assertTrue(os.path.exists(f))

    def _verify_loss_maps(self, filename, *expected_losses):

        def xpath(asset_ref):
            return ("//nrml:loss[@assetRef='" + asset_ref + "']//nrml:value")

        root = self._root(filename)

        for i, exp_loss in enumerate(expected_losses, start=1):
            loss = float(self._get(root, xpath("a%s" % i)))

            self.assertTrue(numpy.allclose(
                loss, exp_loss, atol=0.0, rtol=0.05))

    def _verify_aggregate_curve(self, filename):
        root = self._root(filename)
        xpath = "//nrml:aggregateLossCurve//nrml:loss"
        losses = [float(x) for x in self._get(root, xpath).split()]
        xpath = "//nrml:aggregateLossCurve//nrml:poE"
        poes = [float(x) for x in self._get(root, xpath).split()]

        self.assertTrue(numpy.allclose(
            losses, AGGREGATE_CURVE[0], atol=0.0, rtol=0.05))
        self.assertTrue(numpy.allclose(
                poes, AGGREGATE_CURVE[1], atol=0.0, rtol=0.05))

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ["--output-type=xml"])
        self.assertEquals(0, ret_code)

    def _root(self, filename):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)
        return etree.parse(filename, parser=parser)

    def _get(self, root, xpath):
        return root.find(xpath,
                namespaces={"gml": GML_NS, "nrml": NRML_NS}).text
