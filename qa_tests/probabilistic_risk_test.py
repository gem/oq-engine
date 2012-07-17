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
from nose.plugins.attrib import attr

from qa_tests.data.probabilistic_event_based_risk.test_data import (
    MB_LOSS_CURVES, MB_LOSS_RATIO_CURVES, MB_LOSS_MAPS, MB_AGGREGATE_CURVE,
    SB_LOSS_CURVES, SB_LOSS_RATIO_CURVES, SB_LOSS_MAPS, SB_AGGREGATE_CURVE)

OUTPUT_DIR = helpers.demo_file(
    "probabilistic_event_based_risk/computed_output")
QA_OUTPUT_DIR = helpers.qa_file(
    "probabilistic_event_based_risk/computed_output")


XPATH_POE = "//nrml:asset[@gml:id='%s']//nrml:poE"
XPATH_LOSS = "//nrml:asset[@gml:id='%s']//nrml:loss"
XPATH_LOSS_RATIO = "//nrml:asset[@gml:id='%s']//nrml:lossRatio"
XPATH_LOSS_MAP = "//nrml:loss[@assetRef='%s']//nrml:value"
XPATH_AC_POE = "//nrml:aggregateLossCurve//nrml:poE"
XPATH_AC_LOSS = "//nrml:aggregateLossCurve//nrml:loss"

ASSETS_ID = ['a1', 'a2', 'a3']


def get_root(filename):
    schema = etree.XMLSchema(file=nrml_schema_file())
    parser = etree.XMLParser(schema=schema)
    return etree.parse(filename, parser=parser)


def elem_content(root, xpath, elem_id=None):
    xpath_exp = xpath % elem_id if elem_id else xpath
    return root.find(xpath_exp,
        namespaces={"gml": GML_NS, "nrml": NRML_NS}).text


class ProbabilisticEventBasedRiskQATest(unittest.TestCase):
    """QA tests for the Probabilistic Event Based Risk calculator."""

    def _verify_assets(self, filename, container, elem, tol):
        root = get_root(filename)
        for i, asset_id in enumerate(ASSETS_ID):
            poes = [float(x) for x in elem_content(
                root, XPATH_POE, asset_id).split()]
            losses = [float(x) for x in elem_content(
                root, elem, asset_id).split()]

            self.assertTrue(numpy.allclose(
                poes, container[i][0], atol=0.0, rtol=tol))
            self.assertTrue(numpy.allclose(
                losses, container[i][1], atol=0.0, rtol=tol))

    def test_mean_based(self):
        cfg = helpers.demo_file(
            "probabilistic_event_based_risk/config_qa.gem")
        self._run_job(cfg)
        self._verify_job_succeeded(OUTPUT_DIR)
        job_id = OqJob.objects.latest("id").id

        self._verify_loss_maps(OUTPUT_DIR, MB_LOSS_MAPS, 0.05)
        self._verify_loss_ratio_curves(job_id, OUTPUT_DIR,
            MB_LOSS_RATIO_CURVES, 0.05)
        self._verify_loss_curves(job_id, OUTPUT_DIR, MB_LOSS_CURVES, 0.05)
        self._verify_aggregate_curve(job_id, OUTPUT_DIR, MB_AGGREGATE_CURVE,
            0.05)

    @attr('slow')
    def test_sampled_based(self):
        cfg = helpers.qa_file(
            "probabilistic_event_based_risk/config_qa.gem")
        self._run_job(cfg)
        self._verify_job_succeeded(QA_OUTPUT_DIR)
        job_id = OqJob.objects.latest("id").id

        self._verify_loss_maps(QA_OUTPUT_DIR, SB_LOSS_MAPS, 0.05)
        self._verify_loss_ratio_curves(job_id, QA_OUTPUT_DIR,
            SB_LOSS_RATIO_CURVES, 0.05)
        self._verify_loss_curves(job_id, QA_OUTPUT_DIR, SB_LOSS_CURVES, 0.05)
        self._verify_aggregate_curve(job_id, QA_OUTPUT_DIR,
            SB_AGGREGATE_CURVE, 0.05)

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

    def _verify_loss_curves(self, job_id, output_dir, expected_results, tol):
        filename = "%s/loss_curves-loss-block-#%s-block#0.xml" % (
                output_dir, job_id)

        self._verify_assets(filename, expected_results, XPATH_LOSS, tol)

    def _verify_loss_ratio_curves(self, job_id, output_dir,
                                  expected_results, tol):
        filename = "%s/loss_curves-block-#%s-block#0.xml" % (
                output_dir, job_id)

        self._verify_assets(filename, expected_results, XPATH_LOSS_RATIO, tol)

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

    def _verify_loss_maps(self, output_dir, expected_results, tol):
        filename = "%s/losses_at-0.99.xml" % output_dir
        root = get_root(filename)

        for i, asset_id in enumerate(ASSETS_ID):
            closs = float(elem_content(root, XPATH_LOSS_MAP, asset_id))
            self.assertTrue(numpy.allclose(
                closs, expected_results[i], atol=0.0, rtol=tol))

    def _verify_aggregate_curve(self, job_id, output_dir, expected_results,
                                tol):
        [output] = Output.objects.filter(
            oq_job=job_id,
            output_type="agg_loss_curve")
        export_agg_loss_curve(output, output_dir)
        filename = "%s/aggregate_loss_curve.xml" % output_dir
        root = get_root(filename)
        poes = [float(x) for x in elem_content(root, XPATH_AC_POE).split()]
        losses = [float(x) for x in elem_content(root, XPATH_AC_LOSS).split()]

        self.assertTrue(numpy.allclose(
                poes, expected_results[0], atol=0.0, rtol=tol))
        self.assertTrue(numpy.allclose(
                losses, expected_results[1], atol=0.0, rtol=tol))

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ["--output-type=xml"])
        self.assertEquals(0, ret_code)
