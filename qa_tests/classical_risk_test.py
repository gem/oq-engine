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

from lxml import etree

from openquake.db.models import OqJob
from openquake.nrml.utils import nrml_schema_file
from openquake.xml import NRML_NS

from tests.utils import helpers

OUTPUT_DIR = helpers.demo_file('classical_psha_based_risk/computed_output')


class ClassicalRiskQATestCase(unittest.TestCase):
    """QA tests for the Classical Risk calculator."""

    def test_classical_psha_based_risk(self):
        cfg = helpers.demo_file(
            'classical_psha_based_risk/config.gem')

        self._run_job(cfg)
        self._verify_job_succeeded()

        self._verify_loss_curve()
        self._verify_loss_ratio_curve()
        self._verify_loss_maps()

    def test_hazard_computed_on_exposure_sites(self):
        # slightly different configuration where we
        # run the engine triggering the hazard computation
        # on sites defined in the exposure file
        cfg = helpers.demo_file(
            "classical_psha_based_risk/config_hzr_exposure.gem")

        self._run_job(cfg)
        self._verify_job_succeeded()

    def _verify_loss_maps(self):
        filename = "%s/losses_at-0.01.xml" % OUTPUT_DIR
        expected_closs = 0.264530582

        closs = float(self._get(filename, "//nrml:value"))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=0.05))

        filename = "%s/losses_at-0.02.xml" % OUTPUT_DIR
        expected_closs = 0.143009004

        closs = float(self._get(filename, "//nrml:value"))

        self.assertTrue(numpy.allclose(
                closs, expected_closs, atol=0.0, rtol=0.05))

    def _verify_loss_ratio_curve(self):
        job = OqJob.objects.latest('id')

        filename = "%s/losscurves-block-#%s-block#0.xml" % (
                OUTPUT_DIR, job.id)

        poes = [float(x) for x in self._get(filename, "//nrml:poE").split()]

        expected_poes = [0.03944225, 0.03942720, 0.03856604, 0.03548283,
                0.03122610, 0.02707623, 0.02345915, 0.02038896, 0.01780364,
                0.01564709, 0.01386492, 0.01117745, 0.00925748, 0.00776335,
                0.00654064, 0.00554503, 0.00416704, 0.00337727, 0.00282694,
                0.00231098, 0.00182046, 0.00114431, 0.00089103, 0.00081684,
                0.00068862, 0.00039127, 0.00024029, 0.00012818, 0.00005978,
                0.00002461, 0.00000904]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=0.05))

        loss_ratios = [float(x) for x in self._get(
            filename, "//nrml:lossRatio").split()]

        expected_loss_ratios = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07,
                0.08, 0.09, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.24, 0.28,
                0.32, 0.36, 0.40, 0.48, 0.56, 0.64, 0.72, 0.80, 0.84, 0.88,
                0.92, 0.96, 1.00]

        self.assertTrue(numpy.allclose(expected_loss_ratios, loss_ratios))

    def _verify_loss_curve(self):
        job = OqJob.objects.latest('id')

        filename = "%s/losscurves-loss-block-#%s-block#0.xml" % (
                OUTPUT_DIR, job.id)

        poes = [float(x) for x in self._get(filename, "//nrml:poE").split()]

        expected_poes = [0.03944225, 0.03942720, 0.03856604, 0.03548283,
                0.03122610, 0.02707623, 0.02345915, 0.02038896, 0.01780364,
                0.01564709, 0.01386492, 0.01117745, 0.00925748, 0.00776335,
                0.00654064, 0.00554503, 0.00416704, 0.00337727, 0.00282694,
                0.00231098, 0.00182046, 0.00114431, 0.00089103, 0.00081684,
                0.00068862, 0.00039127, 0.00024029, 0.00012818, 0.00005978,
                0.00002461, 0.00000904]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.0, rtol=0.05))

        losses = [float(x) for x in self._get(filename, "//nrml:loss").split()]

        expected_losses = [0.00, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16,
                0.18, 0.20, 0.24, 0.28, 0.32, 0.36, 0.40, 0.48, 0.56,
                0.64, 0.72, 0.80, 0.96, 1.12, 1.28, 1.44, 1.60, 1.68,
                1.76, 1.84, 1.92, 2.00]

        self.assertTrue(numpy.allclose(expected_losses, losses))

    def _verify_job_succeeded(self):
        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        expected_files = [
            'hazardcurve-0.xml',
            'hazardcurve-mean.xml',
            'losscurves-block-#%s-block#0.xml' % job.id,
            'losscurves-loss-block-#%s-block#0.xml' % job.id,
            'losses_at-0.01.xml',
            'losses_at-0.02.xml',
            'losses_at-0.05.xml'
        ]

        for f in expected_files:
            self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, f)))

    def _run_job(self, config):
        ret_code = helpers.run_job(config, ['--output-type=xml'])
        self.assertEquals(0, ret_code)

    def _get(self, filename, xpath):
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)
        tree = etree.parse(filename, parser=parser)

        return tree.find(xpath,
                namespaces={"nrml": NRML_NS}).text
