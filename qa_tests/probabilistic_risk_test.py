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

from qa_tests.data.probabilistic_event_based_risk.ins_loss_data import (
    TOTAL_LOSS_PRECISION, LOSSMAP_PRECISION, LOSS_MAP_MB, MEAN_INS_LOSS_MB,
    STDDEV_INS_LOSS_MB, LOSS_MAP_SB, MEAN_INS_LOSS_SB, STDDEV_INS_LOSS_SB)

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
            self._verify_job_succeeded(QA_OUTPUT_DIR)
            self._verify_loss_maps(QA_OUTPUT_DIR, 0.05)
            self._verify_loss_ratio_curves(QA_OUTPUT_DIR, 0.05)
            self._verify_loss_curves(QA_OUTPUT_DIR, 0.05)
            self._verify_aggregate_curve(QA_OUTPUT_DIR, 0.05)
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

    @unittest.skip
    def test_insured_loss_mean_based(self):
        cfg = helpers.qa_file(
            "probabilistic_event_based_risk/config_insloss_mb.gem")

        result = helpers.run_job(cfg, ['--output-type=xml'],
            check_output=True)

        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        expected_loss_map_file = helpers.qa_file(
            'probabilistic_event_based_risk/computed_output/insured-loss-map%s'
            '.xml' % job.id)

        self.assertTrue(os.path.exists(expected_loss_map_file))

        helpers.verify_loss_map(self, expected_loss_map_file, LOSS_MAP_MB,
            LOSSMAP_PRECISION)

        actual_mean, actual_stddev = helpers.mean_stddev_from_result_line(result)

        self.assertAlmostEqual(MEAN_INS_LOSS_MB, actual_mean,
            places=TOTAL_LOSS_PRECISION)
        self.assertAlmostEqual(STDDEV_INS_LOSS_MB, actual_stddev,
            places=TOTAL_LOSS_PRECISION)

        # Cleaning generated results file.
        rmtree(QA_OUTPUT_DIR)


    @unittest.skip
    def test_insured_loss_sample_based(self):
        cfg = helpers.qa_file(
            "probabilistic_event_based_risk/config_insloss_sb.gem")

        result = helpers.run_job(scen_cfg, ['--output-type=xml'],
            check_output=True)

        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        expected_loss_map_file = helpers.qa_file(
            'scenario_risk_insured_losses/computed_output/insured-loss-map%s'
            '.xml' % job.id)

        self.assertTrue(os.path.exists(expected_loss_map_file))

        helpers.verify_loss_map(self, expected_loss_map_file, LOSS_MAP_SB,
            LOSSMAP_PRECISION)

        actual_mean, actual_stddev = helpers.mean_stddev_from_result_line(result)

        self.assertAlmostEqual(MEAN_INS_LOSS_SB, actual_mean,
            places=TOTAL_LOSS_PRECISION)
        self.assertAlmostEqual(STDDEV_INS_LOSS_SB, actual_stddev,
            places=TOTAL_LOSS_PRECISION)

        # Cleaning generated results file.
        rmtree(QA_OUTPUT_DIR)


    def test_hazard_computed_on_exposure_sites(self):
        # here we compute the hazard on locations
        # defined in the exposure file. For now, we just
        # check the job completes correctly.

        cfg = helpers.demo_file(
            "probabilistic_event_based_risk/config_hzr_exposure.gem")

        self._run_job(cfg)
        self._verify_job_succeeded(OUTPUT_DIR)

    def _verify_loss_curves(self, output_dir, tol):

        def xpath_poes(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:poE")

        def xpath_losses(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:loss")

        job = OqJob.objects.latest("id")

        filename = "%s/loss_curves-loss-block-#%s-block#0.xml" % (
                output_dir, job.id)

        root = self._root(filename)
        poes = [float(x) for x in self._get(root, xpath_poes("a1")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            0.9975213575, 0.9502134626, 0.8646777340,
            0.8646647795, 0.6321490651, 0.6321506245,
            0.6321525149]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=tol))

        losses = [float(x) for x in self._get(
                root, xpath_losses("a1")).split()]

        expected_losses = [14.6792147571, 44.0376442714,
            73.3960737856, 102.7545032998, 132.1129328141,
            161.4713623283, 190.8297918425, 220.1882213568,
            249.5466508710]

        self.assertTrue(numpy.allclose(
                losses, expected_losses, atol=0.0, rtol=tol))

        poes = [float(x) for x in self._get(root, xpath_poes("a2")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            0.9999999586, 0.9996645695, 0.9975213681,
            0.9816858268, 0.8646666370, 0.8646704246,
            0.6321542453]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=tol))

        losses = [float(x) for x in self._get(
                root, xpath_losses("a2")).split()]

        expected_losses = [3.6409829079, 10.9229487236,
            18.2049145394, 25.4868803551, 32.7688461709,
            40.0508119866, 47.3327778023, 54.6147436181,
            61.8967094338]

        self.assertTrue(numpy.allclose(
                losses, expected_losses, atol=0.0, rtol=tol))

        poes = [float(x) for x in self._get(root, xpath_poes("a3")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            1.0000000000, 1.0000000000, 1.0000000000,
            0.9999998875, 0.9999977397, 0.9998765914,
            0.9816858693]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=tol))

        losses = [float(x) for x in self._get(
                root, xpath_losses("a3")).split()]

        expected_losses = [1.4593438219, 4.3780314657,
            7.2967191094, 10.2154067532, 13.1340943970,
            16.0527820408, 18.9714696845, 21.8901573283,
            24.8088449721]

        self.assertTrue(numpy.allclose(
                losses, expected_losses, atol=0.0, rtol=tol))

    def _verify_loss_ratio_curves(self, output_dir, tol):

        def xpath_poes(asset_ref):
            return ("//nrml:asset[@gml:id='" + asset_ref + "']//nrml:poE")

        def xpath_ratios(asset_ref):
            return ("//nrml:asset[@gml:id='"
                    + asset_ref + "']//nrml:lossRatio")

        job = OqJob.objects.latest("id")

        filename = "%s/loss_curves-block-#%s-block#0.xml" % (
                output_dir, job.id)

        root = self._root(filename)
        poes = [float(x) for x in self._get(root, xpath_poes("a1")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            0.9975213575, 0.9502134626, 0.8646777340,
            0.8646647795, 0.6321490651, 0.6321506245,
            0.6321525149]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=tol))

        loss_ratios = [float(x) for x in self._get(
                root, xpath_ratios("a1")).split()]

        expected_loss_ratios = [0.004893071586, 0.014679214757,
            0.024465357929, 0.034251501100, 0.044037644271,
            0.053823787443, 0.063609930614, 0.073396073786,
            0.083182216957]

        self.assertTrue(numpy.allclose(
                loss_ratios, expected_loss_ratios, atol=0.0, rtol=tol))

        poes = [float(x) for x in self._get(root, xpath_poes("a2")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            0.9999999586, 0.9996645695, 0.9975213681,
            0.9816858268, 0.8646666370, 0.8646704246,
            0.6321542453]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=tol))

        loss_ratios = [float(x) for x in self._get(
                root, xpath_ratios("a2")).split()]

        expected_loss_ratios = [0.0018204915, 0.0054614744,
            0.0091024573, 0.0127434402, 0.0163844231,
            0.0200254060, 0.0236663889, 0.0273073718,
            0.0309483547]

        self.assertTrue(numpy.allclose(
                loss_ratios, expected_loss_ratios, atol=0.0, rtol=tol))

        poes = [float(x) for x in self._get(
                root, xpath_poes("a3")).split()]

        expected_poes = [1.0000000000, 1.0000000000,
            1.0000000000, 1.0000000000, 1.0000000000,
            0.9999998875, 0.9999977397, 0.9998765914,
            0.9816858693]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=tol))

        loss_ratios = [float(x) for x in self._get(
                root, xpath_ratios("a3")).split()]

        expected_loss_ratios = [0.0014593438, 0.0043780315,
            0.0072967191, 0.0102154068, 0.0131340944,
            0.0160527820, 0.0189714697, 0.0218901573,
            0.0248088450]

        self.assertTrue(numpy.allclose(
                loss_ratios, expected_loss_ratios, atol=0.0, rtol=tol))

    def _verify_job_succeeded(self, output_dir):
        job = OqJob.objects.latest("id")
        self.assertEqual("succeeded", job.status)

        expected_files = [
            "loss_curves-block-#%s-block#0.xml" % job.id,
            "loss_curves-loss-block-#%s-block#0.xml" % job.id,
            "losses_at-0.99.xml"
        ]

        for f in expected_files:
            self.assertTrue(os.path.exists(os.path.join(output_dir, f)))

    def _verify_loss_maps(self, output_dir, tol):

        def xpath(asset_ref):
            return ("//nrml:loss[@assetRef='" + asset_ref + "']//nrml:value")

        filename = "%s/losses_at-0.99.xml" % output_dir
        root = self._root(filename)

        expected_closs = 78.1154725900
        closs = float(self._get(root, xpath("a1")))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=tol))

        expected_closs = 36.2507008221
        closs = float(self._get(root, xpath("a2")))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=tol))

        expected_closs = 23.4782545574
        closs = float(self._get(root, xpath("a3")))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=tol))

    def _verify_aggregate_curve(self, output_dir, tol):
        job = OqJob.objects.latest("id")

        [output] = Output.objects.filter(
            oq_job=job.id,
            output_type="agg_loss_curve")

        export_agg_loss_curve(output, output_dir)
        filename = "%s/aggregate_loss_curve.xml" % output_dir

        root = self._root(filename)
        xpath = "//nrml:aggregateLossCurve//nrml:poE"
        poes = [float(x) for x in self._get(root, xpath).split()]

        expected_poes = [1.0000000000, 1.0000000000, 0.9999991685,
            0.9932621249, 0.9502177204, 0.8646647795,
            0.8646752036, 0.6321506245, 0.6321525149]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=tol))

        xpath = "//nrml:aggregateLossCurve//nrml:loss"
        losses = [float(x) for x in self._get(root, xpath).split()]

        expected_losses = [18.5629274028, 55.6887822085, 92.8146370142,
            129.9404918199, 167.0663466256, 204.1922014313,
            241.3180562370, 278.4439110427, 315.5697658484]

        self.assertTrue(numpy.allclose(
                losses, expected_losses, atol=0.0, rtol=tol))

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
