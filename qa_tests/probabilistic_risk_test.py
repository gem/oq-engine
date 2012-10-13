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

from qa_tests.data.probabilistic_event_based_risk import test_data

OUTPUT_DIR = helpers.demo_file(
    "probabilistic_event_based_risk/computed_output")
QA_OUTPUT_DIR = helpers.qa_file(
    "probabilistic_event_based_risk/computed_output")


class ProbabilisticEventBasedRiskQATest(unittest.TestCase):
    """QA tests for the Probabilistic Event Based Risk calculator."""

    def test_mean_based(self):
        try:
            expected_poes = {}
            expected_losses = {}
            expected_loss_map = {}

            cfg = helpers.qa_file(
                "probabilistic_event_based_risk/m_config.gem")

            self._run_job(cfg)
            self._verify_job_succeeded()

            expected_loss_map["a1"] = 78.1154725900
            expected_loss_map["a2"] = 36.2507008221
            expected_loss_map["a3"] = 23.4782545574

            self._verify_loss_map(expected_loss_map, QA_OUTPUT_DIR, 0.05)

            expected_poes["a1"] = [
                1.0000000000, 1.0000000000, 0.9975213575,
                0.9502134626, 0.8646777340, 0.8646647795,
                0.6321490651, 0.6321506245, 0.6321525149,
            ]

            expected_poes["a2"] = [
                1.0000000000, 1.0000000000, 0.9999999586,
                0.9996645695, 0.9975213681, 0.9816858268,
                0.8646666370, 0.8646704246, 0.6321542453,
            ]

            expected_poes["a3"] = [
                1.0000000000, 1.0000000000, 1.0000000000,
                1.0000000000, 1.0000000000, 0.9999998875,
                0.9999977397, 0.9998765914, 0.9816858693,
            ]

            expected_losses["a1"] = [
                0.004893071586, 0.014679214757, 0.024465357929,
                0.034251501100, 0.044037644271, 0.053823787443,
                0.063609930614, 0.073396073786, 0.083182216957,
            ]

            expected_losses["a2"] = [
                0.0018204915, 0.0054614744, 0.0091024573,
                0.0127434402, 0.0163844231, 0.0200254060,
                0.0236663889, 0.0273073718, 0.0309483547,
            ]

            expected_losses["a3"] = [
                0.0014593438, 0.0043780315, 0.0072967191,
                0.0102154068, 0.0131340944, 0.0160527820,
                0.0189714697, 0.0218901573, 0.0248088450,
            ]

            self._verify_loss_ratio_curves(expected_poes,
                expected_losses, QA_OUTPUT_DIR, 0.05)

            # y-values don't change in loss curves

            expected_losses["a1"] = [
                14.6792147571, 44.0376442714, 73.3960737856,
                102.7545032998, 132.1129328141, 161.4713623283,
                190.8297918425, 220.1882213568, 249.5466508710,
            ]

            expected_losses["a2"] = [
                3.6409829079, 10.9229487236, 18.2049145394,
                25.4868803551, 32.7688461709, 40.0508119866,
                47.3327778023, 54.6147436181, 61.8967094338,
            ]

            expected_losses["a3"] = [
                1.4593438219, 4.3780314657, 7.2967191094,
                10.2154067532, 13.1340943970, 16.0527820408,
                18.9714696845, 21.8901573283, 24.8088449721,
            ]

            self._verify_loss_curves(expected_poes,
                expected_losses, QA_OUTPUT_DIR, 0.05)

            expected_aggregate_poes = [
                1.0000000000, 1.0000000000, 0.9999991685,
                0.9932621249, 0.9502177204, 0.8646647795,
                0.8646752036, 0.6321506245, 0.6321525149,
            ]

            expected_aggregate_losses = [
                18.5629274028, 55.6887822085, 92.8146370142,
                129.9404918199, 167.0663466256, 204.1922014313,
                241.3180562370, 278.4439110427, 315.5697658484,
            ]

            self._verify_aggregate_curve(expected_aggregate_poes,
                expected_aggregate_losses, QA_OUTPUT_DIR, 0.05)

        finally:
            rmtree(QA_OUTPUT_DIR)

    def test_sampled_based_beta(self):
        try:
            expected_poes = {}
            expected_losses = {}
            expected_loss_map = {}

            cfg = helpers.qa_file(
                "probabilistic_event_based_risk/config_beta_qa.gem")

            self._run_job(cfg)
            self._verify_job_succeeded()

            expected_loss_map["a1"] = 73.8279109206
            expected_loss_map["a2"] = 25.2312514028
            expected_loss_map["a3"] = 29.7790495007

            self._verify_loss_map(expected_loss_map, QA_OUTPUT_DIR, 0.05)

            expected_poes["a1"] = [
                1.0, 0.601480958915, 0.147856211034,
                0.130641764601, 0.113079563283, 0.0768836536134,
                0.0768836536134, 0.0198013266932, 0.0198013266932,
            ]

            expected_poes["a3"] = [
                1.0, 0.999088118034, 0.472707575957,
                0.197481202038, 0.095162581964, 0.0392105608477,
                0.0198013266932, 0.0198013266932, 0.0198013266932,
            ]

            expected_poes["a2"] = [
                1.0, 0.831361852731, 0.302323673929,
                0.130641764601, 0.0768836536134, 0.0768836536134,
                0.0582354664158, 0.0582354664158, 0.0392105608477,
            ]

            expected_losses["a1"] = [
                0.0234332852886, 0.0702998558659, 0.117166426443,
                0.16403299702, 0.210899567598, 0.257766138175,
                0.304632708752, 0.351499279329, 0.398365849907,
            ]

            expected_losses["a3"] = [
                0.00981339568577, 0.0294401870573, 0.0490669784288,
                0.0686937698004, 0.0883205611719, 0.107947352543,
                0.127574143915, 0.147200935287, 0.166827726658,
            ]

            expected_losses["a2"] = [
                0.0112780780331, 0.0338342340993, 0.0563903901655,
                0.0789465462317, 0.101502702298, 0.124058858364,
                0.14661501443, 0.169171170497, 0.191727326563,
            ]

            self._verify_loss_ratio_curves(expected_poes,
                expected_losses, QA_OUTPUT_DIR, 0.05)

            # y-values don't change in loss curves

            expected_losses["a1"] = [
                70.2998558659, 210.899567598, 351.499279329,
                492.098991061, 632.698702793, 773.298414525,
                913.898126256, 1054.49783799, 1195.09754972,
            ]

            expected_losses["a2"] = [
                22.5561560662, 67.6684681986, 112.780780331,
                157.893092463, 203.005404596, 248.117716728,
                293.230028861, 338.342340993, 383.454653125,
            ]

            expected_losses["a3"] = [
                9.81339568577, 29.4401870573, 49.0669784288,
                68.6937698004, 88.3205611719, 107.947352543,
                127.574143915, 147.200935287, 166.827726658,
            ]

            self._verify_loss_curves(expected_poes,
                expected_losses, QA_OUTPUT_DIR, 0.05)

            expected_aggregate_poes = [
                1.0, 0.732864698034, 0.228948414196,
                0.147856211034, 0.0768836536134, 0.0768836536134,
                0.0198013266932, 0.0198013266932, 0.0198013266932,
            ]

            expected_aggregate_losses = [
                102.669407618, 308.008222854, 513.347038089,
                718.685853325, 924.024668561, 1129.3634838,
                1334.70229903, 1540.04111427, 1745.3799295,
            ]

            self._verify_aggregate_curve(expected_aggregate_poes,
                expected_aggregate_losses, QA_OUTPUT_DIR, 0.05)

        finally:
            rmtree(QA_OUTPUT_DIR)

    @unittest.skip
    def test_sampled_based(self):
        pass

    def test_insured_loss_mean_based(self):
        try:
            cfg = helpers.qa_file(
                "probabilistic_event_based_risk/m_il_config.gem")

            self._run_job(cfg)
            job_id = OqJob.objects.latest("id").id

            [output] = Output.objects.filter(oq_job=job_id,
                output_type="agg_loss_curve")

            export_agg_loss_curve(output, QA_OUTPUT_DIR)

            expected_files = [
                "loss_curves-block-#%s-block#0.xml" % job_id,
                "loss_curves-loss-block-#%s-block#0.xml" % job_id,
                "loss_curves-insured-block=#%s-block#0.xml" % job_id,
                "losses_at-0.99.xml",
                "aggregate_loss_curve.xml",
                "insured_loss_curves-insured-loss-block=#%s-block#0.xml" %
                    job_id]

            self._verify_job_succeeded()
            self._verify_outputs(QA_OUTPUT_DIR, expected_files)

            expected_poes = {}
            expected_losses = {}

            expected_poes["a1"] = test_data.EXPECTED_POES_LR_A1_MB_IL
            expected_poes["a2"] = test_data.EXPECTED_POES_LR_A2_MB_IL
            expected_poes["a3"] = test_data.EXPECTED_POES_LR_A3_MB_IL

            expected_losses["a1"] = test_data.EXPECTED_LOSS_RATIOS_A1_MB_IL
            expected_losses["a2"] = test_data.EXPECTED_LOSS_RATIOS_A2_MB_IL
            expected_losses["a3"] = test_data.EXPECTED_LOSS_RATIOS_A3_MB_IL

            # self._verify_loss_ratio_curves(expected_poes, expected_losses,
            #     QA_OUTPUT_DIR, 0.05,
            #     "%s/loss_curves-insured-block=#%s-block#0.xml")

            expected_poes["a1"] = test_data.EXPECTED_POES_LC_A1_MB_IL
            expected_poes["a2"] = test_data.EXPECTED_POES_LC_A2_MB_IL
            expected_poes["a3"] = test_data.EXPECTED_POES_LC_A3_MB_IL

            expected_losses["a1"] = test_data.EXPECTED_LOSSES_A1_MB_IL
            expected_losses["a2"] = test_data.EXPECTED_LOSSES_A2_MB_IL
            expected_losses["a3"] = test_data.EXPECTED_LOSSES_A3_MB_IL

            self._verify_loss_curves(expected_poes, expected_losses,
                QA_OUTPUT_DIR, 0.05,
                "%s/insured_loss_curves-insured-loss-block=#%s-block#0.xml")

        finally:
            rmtree(QA_OUTPUT_DIR)

    # TODO After PEB sample based has been fixed
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
            self._verify_job_succeeded()
            job_id = OqJob.objects.latest("id").id

            expected_files = [
                "losses_at-0.99.xml",
                "loss_curves-block-#%s-block#0.xml" % job_id,
                "loss_curves-loss-block-#%s-block#0.xml" % job_id
            ]

            self._verify_outputs(OUTPUT_DIR, expected_files)

        finally:
            rmtree(OUTPUT_DIR)

    def _verify_loss_curves(self, expected_poes,
        expected_losses, output_dir, tol,
        file_pattern="%s/loss_curves-loss-block-#%s-block#0.xml"):

        def xpath_poes(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:poE")

        def xpath_losses(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:loss")

        job = OqJob.objects.latest("id")
        filename = file_pattern % (output_dir, job.id)
        root = self._root(filename)

        for asset_ref in expected_poes.keys():
            poes = [float(x) for x in self._get(root,
                xpath_poes(asset_ref)).split()]

            numpy.testing.assert_allclose(
                poes, expected_poes[asset_ref], atol=0.0, rtol=tol)

            losses = [float(x) for x in self._get(
                root, xpath_losses(asset_ref)).split()]

            numpy.testing.asset_allclose(
                losses, expected_losses[asset_ref],
                atol=0.0, rtol=tol)

    def _verify_loss_ratio_curves(self, expected_poes, expected_loss_ratios,
        output_dir, tol, file_pattern="%s/loss_curves-block-#%s-block#0.xml"):

        def xpath_poes(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:poE")

        def xpath_ratios(asset_ref):
            return ("//nrml:asset[@gml:id='"
                + asset_ref + "']//nrml:lossRatio")

        job = OqJob.objects.latest("id")
        filename = file_pattern % (output_dir, job.id)
        root = self._root(filename)

        for asset_ref in expected_poes.keys():
            poes = [float(x) for x in self._get(root,
                xpath_poes(asset_ref)).split()]

            numpy.testing.assert_allclose(
                poes, expected_poes[asset_ref], atol=0.0, rtol=tol)

            loss_ratios = [float(x) for x in self._get(
                root, xpath_ratios(asset_ref)).split()]

            self.assertTrue(numpy.allclose(
                loss_ratios, expected_loss_ratios[asset_ref],
                atol=0.0, rtol=tol))

    def _verify_job_succeeded(self):
        job = OqJob.objects.latest("id")
        self.assertEqual("succeeded", job.status)

    def _verify_outputs(self, output_dir, expected_files):
        for f in expected_files:
            self.assertTrue(os.path.exists(os.path.join(output_dir, f)))

    def _verify_loss_map(self, expected_losses, output_dir, tol):

        def xpath(asset_ref):
            return ("//nrml:loss[@assetRef='" + asset_ref + "']//nrml:value")

        filename = "%s/losses_at-0.99.xml" % output_dir
        root = self._root(filename)

        for asset_ref in expected_losses.keys():
            loss = float(self._get(root, xpath(asset_ref)))

            self.assertTrue(numpy.allclose(
                loss, expected_losses[asset_ref], atol=0.0, rtol=tol))

    def _verify_aggregate_curve(self, expected_poes,
        expected_losses, output_dir, tol):

        job = OqJob.objects.latest("id")

        [output] = Output.objects.filter(
            oq_job=job.id, output_type="agg_loss_curve")

        export_agg_loss_curve(output, output_dir)
        filename = "%s/aggregate_loss_curve.xml" % output_dir
        root = self._root(filename)

        xpath = "//nrml:aggregateLossCurve//nrml:poE"
        poes = [float(x) for x in self._get(root, xpath).split()]

        self.assertTrue(numpy.allclose(
            poes, expected_poes, atol=0.0, rtol=tol))

        xpath = "//nrml:aggregateLossCurve//nrml:loss"
        losses = [float(x) for x in self._get(root, xpath).split()]

        self.assertTrue(numpy.allclose(
            losses, expected_losses, atol=0.0, rtol=0.05))

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
