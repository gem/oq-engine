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
import unittest

from lxml import etree
from nose.plugins.attrib import attr

from openquake.db.models import OqJob
from openquake import xml

from tests.utils import helpers


class ScenarioRiskQATest(unittest.TestCase):
    """QA test for the Scenario Risk calculator."""

    #: decimal places
    TOTAL_LOSS_PRECISION = 2
    #: decimal places
    LOSSMAP_PRECISION = 4

    #: expected mean loss for the region
    EXP_MEAN_LOSS = 1272.7
    #: expected stddev loss for the region
    EXP_STDDEV_LOSS = 455.83

    def _verify_loss_map(self, path, expected_data):
        namespaces = dict(nrml=xml.NRML_NS, gml=xml.GML_NS)
        root = etree.parse(path)

        actual_lm_data = []
        lm_nodes = root.xpath('.//nrml:LMNode', namespaces=namespaces)

        # sanity check: there should be only 3 loss map nodes:
        self.assertEqual(3, len(lm_nodes))

        for node in lm_nodes:
            node_data = dict()

            [pos] = node.xpath('.//gml:pos', namespaces=namespaces)
            node_data['pos'] = pos.text

            [loss] = node.xpath('./nrml:loss', namespaces=namespaces)
            node_data['asset'] = loss.get('assetRef')

            [mean] = loss.xpath('./nrml:mean', namespaces=namespaces)
            [stddev] = loss.xpath('./nrml:stdDev', namespaces=namespaces)
            node_data['mean'] = float(mean.text)
            node_data['stddev'] = float(stddev.text)

            actual_lm_data.append(node_data)

        helpers.assertDeepAlmostEqual(
            self, expected_data, actual_lm_data, places=self.LOSSMAP_PRECISION)

    @attr('qa')
    def test_scenario_risk(self):
        # The rudimentary beginnings of a QA test for the scenario calc.
        # For now, just run it end-to-end to make sure it doesn't blow up.
        scen_cfg = helpers.demo_file('scenario_risk/config.gem')

        expected_loss_map = [
            dict(asset='a3', pos='15.48 38.25', mean=217.510673644,
                 stddev=86.3215466446),
            dict(asset='a2', pos='15.56 38.17', mean=469.375607933,
                 stddev=271.423557166),
            dict(asset='a1', pos='15.48 38.09', mean=585.814597,
                 stddev=270.632803227),
        ]

        result = helpers.run_job(scen_cfg, ['--output-type=xml'],
                                 check_output=True)

        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        expected_loss_map_file = helpers.demo_file(
            'scenario_risk/computed_output/loss-map-%s.xml' % job.id)

        self.assertTrue(os.path.exists(expected_loss_map_file))

        self._verify_loss_map(expected_loss_map_file, expected_loss_map)

        # We expected the shell output to look something like the following
        # two lines:
        # Mean region loss value: 1272.70087858
        # Standard deviation region loss value: 455.834734995

        # split on newline and filter out empty lines
        result = [line for line in result.split('\n') if len(line) > 0]

        # we expect 2 lines; 1 for mean, 1 for stddev
        self.assertEqual(2, len(result))

        actual_mean = float(result[0].split()[-1])
        actual_stddev = float(result[1].split()[-1])

        self.assertAlmostEqual(
            self.EXP_MEAN_LOSS, actual_mean, places=self.TOTAL_LOSS_PRECISION)
        self.assertAlmostEqual(
            self.EXP_STDDEV_LOSS, actual_stddev,
            places=self.TOTAL_LOSS_PRECISION)

    @attr(speed='slow')
    def test_scenario_risk_sample_based(self):
        # This QA is a longer-running test of the Scenario Risk calculator.
        # The vulnerabiilty model has non-zero Coefficients of Variation and
        # therefore exercises the 'sample-based' path through the calculator.
        # This test is configured to produce 1000 ground motion fields at each
        # location of interest (in the test above, only 10 are produced).

        # We expect the `mean` results to be roughly the same as the above
        # test, however the standard values are unpredicatable. The only
        # validation we can do on the stddev results is to make sure they are
        # > the values in the expected values (see above).
        pass
