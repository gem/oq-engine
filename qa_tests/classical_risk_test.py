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

import numpy
import os
import unittest
from nose.plugins.attrib import attr
from shutil import rmtree

from lxml import etree
from glob import glob
from itertools import repeat

from openquake.db.models import OqJob
from openquake.nrml.utils import nrml_schema_file
from openquake.xml import NRML_NS

from tests.utils import helpers

from qa_tests.data.classical_risk_test.test_data import (
    EXPECTED_CLOSS_01, EXPECTED_CLOSS_02, EXPECTED_POES_LRC,
    EXPECTED_LOSS_RATIOS_LRC, EXPECTED_POES_LC, EXPECTED_LOSSES_LC)

from qa_tests.data.classical_risk_test.beta_distributions.test_data import (
    B_EXPECTED_CLOSS, B_EXPECTED_POES_LC_LRC, B_EXPECTED_LOSSES_LC,
    B_EXPECTED_LOSS_RATIOS_LRC)

OUTPUT_DIR = helpers.demo_file('classical_psha_based_risk/computed_output')
QA_OUTPUT_DIR = helpers.qa_file('classical_risk_test/computed_output')
OUTPUT_BETA_DIR = helpers.qa_file(
    'classical_risk_test/beta_distributions/computed_output')


class ClassicalRiskQATestCase(unittest.TestCase):
    """QA tests for the Classical Risk calculator."""

    def test_classical_psha_based_risk(self):
        cfg = helpers.demo_file(
            'classical_psha_based_risk/config.gem')

        self._run_job(cfg)

        job_id = OqJob.objects.latest('id').id
        expected_files = [
            'hazardcurve-0.xml',
            'hazardcurve-mean.xml',
            'losscurves-block-#%s-block#0.xml' % job_id,
            'losscurves-loss-block-#%s-block#0.xml' % job_id,
            'losses_at-0.01.xml',
            'losses_at-0.02.xml',
            'losses_at-0.05.xml'
        ]

        self._verify_job_succeeded(OUTPUT_DIR, expected_files)
        self._verify_loss_curve(job_id, EXPECTED_POES_LC, EXPECTED_LOSSES_LC,
            0.0, OUTPUT_DIR)
        self._verify_loss_ratio_curve(job_id, EXPECTED_POES_LRC,
            EXPECTED_LOSS_RATIOS_LRC, 0.0, OUTPUT_DIR)
        self._verify_loss_maps(OUTPUT_DIR, EXPECTED_CLOSS_01,
            EXPECTED_CLOSS_02)

    def test_classical_beta_distrib(self):
        try:
            cfg = helpers.qa_file(
                'classical_risk_test/beta_distributions/config_risk.gem')

            self._run_job(cfg)

            job_id = OqJob.objects.latest('id').id
            expected_files = [
                'hazardcurve-0.xml',
                'hazardcurve-mean.xml',
                'losscurves-block-#%s-block#0.xml' % job_id,
                'losscurves-loss-block-#%s-block#0.xml' % job_id,
                'losses_at-0.01.xml',
            ]
            self._verify_job_succeeded(OUTPUT_BETA_DIR, expected_files)

            self._verify_loss_curve(job_id, B_EXPECTED_POES_LC_LRC,
                B_EXPECTED_LOSSES_LC, 0.05, OUTPUT_BETA_DIR)

            self._verify_loss_ratio_curve(job_id, B_EXPECTED_POES_LC_LRC,
                B_EXPECTED_LOSS_RATIOS_LRC, 0.05, OUTPUT_BETA_DIR)

            self._verify_loss_maps(OUTPUT_BETA_DIR, B_EXPECTED_CLOSS)

        finally:
            # Cleaning generated results file.
            rmtree(OUTPUT_BETA_DIR)


    @attr('slow')
    def test_verify_output_per_asset(self):
        try:
            cfg = helpers.qa_file(
                'classical_risk_test/qa_config.gem')
            self._run_job(cfg)

            exp_num_items = 3815
            job = OqJob.objects.latest('id')

            lc_block_pattern = "%s/losscurves-block-#%s-block#*.xml" % (
                QA_OUTPUT_DIR, job.id)
            lc_lblock_pattern = "%s/losscurves-loss-block-#%s-block#*.xml" % (
                QA_OUTPUT_DIR, job.id)
            losses_at = "%s/losses_at-0.1.xml" % (QA_OUTPUT_DIR)

            num_assets_lc_block_files = self._compute_sum_items(
                'asset', lc_block_pattern)
            num_assets_lc_lblock_files = self._compute_sum_items(
                'asset', lc_lblock_pattern)
            num_losses = self._compute_sum_items('loss', losses_at)

            self.assertEqual(exp_num_items, num_assets_lc_block_files)
            self.assertEqual(exp_num_items, num_assets_lc_lblock_files)
            self.assertEqual(exp_num_items, num_losses)

        finally:
            # Cleaning generated results file.
            rmtree(QA_OUTPUT_DIR)

    def _compute_sum_items(self, item, pattern):
        fun = self._count_num_items_in_filename
        filenames = glob(pattern)
        items = repeat(item, len(filenames))
        items_per_filenames = [fun(item, pattern)
                                for item, pattern in zip(items, filenames)]
        return sum(items_per_filenames)

    def _count_num_items_in_filename(self, item, filename):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)
        root = etree.parse(filename, parser=parser).getroot()
        exp = etree.XPath('count(//n:%s)' % item, namespaces={'n': NRML_NS})
        num_items = exp(root)
        return num_items

    def test_hazard_computed_on_exposure_sites(self):
        # slightly different configuration where we
        # run the engine triggering the hazard computation
        # on sites defined in the exposure file
        cfg = helpers.demo_file(
            "classical_psha_based_risk/config_hzr_exposure.gem")

        job_id = OqJob.objects.latest('id').id
        expected_files = ['hazardcurve-0.xml', 'hazardcurve-mean.xml',
                          'losscurves-block-#%s-block#0.xml' % job_id,
                          'losscurves-loss-block-#%s-block#0.xml' % job_id,
                          'losses_at-0.01.xml', 'losses_at-0.02.xml',
                          'losses_at-0.05.xml']

        self._run_job(cfg)
        self._verify_job_succeeded(OUTPUT_DIR, expected_files)

    def _verify_loss_maps(self, output_dir, *expected_closses):
        for i, exp_closs in enumerate(expected_closses, start=1):
            filename = "%s/losses_at-0.0%s.xml" % (output_dir, i)
            closs = float(self._get(filename, "//nrml:value"))

            self.assertTrue(numpy.allclose(
                    closs, exp_closs, atol=0.0, rtol=0.05))

    def _verify_loss_ratio_curve(self, job_id, expected_poes,
                                 expected_loss_ratios, tol, output_dir):

        filename = "%s/losscurves-block-#%s-block#0.xml" % (
                output_dir, job_id)

        poes = [float(x) for x in self._get(filename, "//nrml:poE").split()]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=0.05))

        loss_ratios = [float(x) for x in self._get(
            filename, "//nrml:lossRatio").split()]

        self.assertTrue(numpy.allclose(expected_loss_ratios, loss_ratios,
            atol=0.0, rtol=tol))

    def _verify_loss_curve(self, job_id, expected_poes, expected_losses, tol,
                           output_dir):

        filename = "%s/losscurves-loss-block-#%s-block#0.xml" % (
                output_dir, job_id)

        poes = [float(x) for x in self._get(filename, "//nrml:poE").split()]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=0.05))

        losses = [float(x) for x in self._get(filename, "//nrml:loss").split()]

        self.assertTrue(numpy.allclose(expected_losses, losses, atol=0.0,
            rtol=tol))

    def _verify_job_succeeded(self, dir, expected_files):
        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)
        for f in expected_files:
            self.assertTrue(os.path.exists(os.path.join(dir, f)))

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ['--output-type=xml'])
        self.assertEquals(0, ret_code)

    def _get(self, filename, xpath):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)
        tree = etree.parse(filename, parser=parser)

        return tree.find(xpath,
                namespaces={"nrml": NRML_NS}).text
