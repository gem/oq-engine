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
from nose.plugins.attrib import attr

from openquake.db.models import OqJob
from openquake.nrml import nrml_schema_file
from openquake.xml import NRML_NS

from tests.utils import helpers

OUTPUT_DIR = helpers.demo_file('classical_psha_based_risk/computed_output')


class ClassicalRiskQATestCase(unittest.TestCase):
    """Single site QA tests for the Classical Risk calculator."""

    @attr('qa')
    def test_classical_psha_based_risk(self):
        cfg = helpers.demo_file(
            'classical_psha_based_risk/config.gem')

        self._run_job(cfg)
        self._verify_job_succeeded()

        self._verify_loss_curve()
        self._verify_loss_ratio_curve()
        self._verify_loss_maps()

    def _verify_loss_maps(self):
        xpath = '{%(ns)s}riskResult/{%(ns)s}lossMap/{%(ns)s}LMNode/{%(ns)s}loss/{%(ns)s}value'

        filename = "%s/losses_at-0.01.xml" % OUTPUT_DIR
        expected_closs = 0.264530582

        closs = float(self._get(filename, xpath))
        self.assertTrue((closs - expected_closs) / expected_closs <= 0.05)

        filename = "%s/losses_at-0.02.xml" % OUTPUT_DIR
        expected_closs = 0.143009004

        closs = float(self._get(filename, xpath))
        self.assertTrue((closs - expected_closs) / expected_closs <= 0.05)

    def _verify_loss_ratio_curve(self):
        job = OqJob.objects.latest('id')

        filename = "%s/losscurves-block-#%s-block#0.xml" % (
                OUTPUT_DIR, job.id)

        xpath = '{%(ns)s}riskResult/{%(ns)s}lossRatioCurveList/{%(ns)s}asset/{%(ns)s}lossRatioCurves/{%(ns)s}lossRatioCurve/{%(ns)s}poE'
        poes = [float(x) for x in self._get(filename, xpath).split()]

        expected_poes = [0.03944, 0.03943, 0.03857, 0.03548, 0.03123, 0.02708,
                0.02346, 0.02039, 0.01780, 0.01565, 0.01386, 0.01118, 0.00926,
                0.00776, 0.00654, 0.00555, 0.00417, 0.00338, 0.00283, 0.00231,
                0.00182, 0.00114, 0.00089, 0.00082, 0.00069, 0.00039, 0.00024,
                0.00013, 0.00006, 0.00002, 0.00001]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.000005, rtol=0.05))

        xpath = '{%(ns)s}riskResult/{%(ns)s}lossRatioCurveList/{%(ns)s}asset/{%(ns)s}lossRatioCurves/{%(ns)s}lossRatioCurve/{%(ns)s}lossRatio'
        loss_ratios = [float(x) for x in self._get(filename, xpath).split()]

        expected_loss_ratios = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07,
                0.08, 0.09, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.24, 0.28,
                0.32, 0.36, 0.40, 0.48, 0.56, 0.64, 0.72, 0.80, 0.84, 0.88,
                0.92, 0.96, 1.00]

        self.assertTrue(numpy.allclose(expected_loss_ratios, loss_ratios))

    def _verify_loss_curve(self):
        job = OqJob.objects.latest('id')

        filename = "%s/losscurves-loss-block-#%s-block#0.xml" % (
                OUTPUT_DIR, job.id)

        xpath = '{%(ns)s}riskResult/{%(ns)s}lossCurveList/{%(ns)s}asset/{%(ns)s}lossCurves/{%(ns)s}lossCurve/{%(ns)s}poE'
        poes = [float(x) for x in self._get(filename, xpath).split()]

        expected_poes = [0.03944, 0.03943, 0.03857, 0.03548, 0.03123, 0.02708,
                0.02346, 0.02039, 0.01780, 0.01565, 0.01386, 0.01118, 0.00926,
                0.00776, 0.00654, 0.00555, 0.00417, 0.00338, 0.00283, 0.00231,
                0.00182, 0.00114, 0.00089, 0.00082, 0.00069, 0.00039, 0.00024,
                0.00013, 0.00006, 0.00002, 0.00001]

        self.assertTrue(numpy.allclose(
                poes, expected_poes, atol=0.000005, rtol=0.05))

        xpath = '{%(ns)s}riskResult/{%(ns)s}lossCurveList/{%(ns)s}asset/{%(ns)s}lossCurves/{%(ns)s}lossCurve/{%(ns)s}loss'
        losses = [float(x) for x in self._get(filename, xpath).split()]

        expected_losses = [0.00, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16,
                0.18, 0.20, 0.24, 0.28, 0.32, 0.36, 0.40, 0.48, 0.56,
                0.64, 0.72, 0.80, 0.96, 1.12, 1.28, 1.44, 1.60, 1.68,
                1.76, 1.84, 1.92, 2.00]

        self.assertTrue(numpy.allclose(expected_losses, losses))

    def _verify_poes(self, expected, computed):
        for x in xrange(len(expected)):
            # absolute(a - b) / b <= 0.05
            self.assertTrue(numpy.abs((
                    computed[x] - expected[x]) / expected[x] <= 0.05))

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
        
        return tree.getroot().find(xpath % {'ns': NRML_NS}).text
