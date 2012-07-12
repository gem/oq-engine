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
from shutil import rmtree
from nose.plugins.attrib import attr

from openquake.db.models import OqJob
from openquake import xml

from tests.utils import helpers

QA_OUTPUT_DIR = helpers.qa_file(
    "scenario_risk_insured_losses/computed_output")


class ScenarioRiskQATest(unittest.TestCase):
    """QA test for the Scenario Risk calculator."""

    #: decimal places
    TOTAL_LOSS_PRECISION = 2
    #: decimal places
    LOSSMAP_PRECISION = 4

    def test_hazard_input_on_exposure_sites(self):
        cfg = helpers.demo_file(
            "scenario_risk/config_hzr_exposure.gem")

        ret_code = helpers.run_job(cfg, ["--output-type=xml"])
        self.assertEquals(0, ret_code)

        self.assertEqual("succeeded", OqJob.objects.latest("id").status)

    def _loss_map_result_from_file(self, path):
        namespaces = dict(nrml=xml.NRML_NS, gml=xml.GML_NS)
        root = etree.parse(path)

        lm_data = []
        lm_nodes = root.xpath('.//nrml:LMNode', namespaces=namespaces)

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

            lm_data.append(node_data)

        return lm_data

    def _mean_stddev_from_result_line(self, result):
        result = [line for line in result.split('\n') if len(line) > 0]
        # We expected the shell output to look something like the following
        # two lines:
        # Mean region loss value: XXX.XXX
        # Standard deviation region loss value: XXX.XXX
        self.assertEqual(2, len(result))

        actual_mean = float(result[0].split()[-1])
        actual_stddev = float(result[1].split()[-1])
        return actual_mean, actual_stddev

    def _verify_loss_map(self, path, lm_data):
        expected_data = self._loss_map_result_from_file(path)

        helpers.assertDeepAlmostEqual(
            self, sorted(expected_data), sorted(lm_data),
            places=self.LOSSMAP_PRECISION)

    def _verify_loss_map_within_range(self, mb_loss_map,
                                      expected_loss_map, range):
        for i, lm_node in enumerate(mb_loss_map):
            exp_lm_node = expected_loss_map[i]

            delta = lm_node['mean'] * range
            self.assertAlmostEqual(
                lm_node['mean'], exp_lm_node['mean'], delta=delta)

            self.assertTrue(exp_lm_node['stddev'] > lm_node['stddev'])

    def test_scenario_risk(self):
        # This test exercises the 'mean-based' path through the Scenario Risk
        # calculator. There is no random sampling done here so the results are
        # 100% predictable.
        scen_cfg = helpers.demo_file('scenario_risk/config.gem')

        exp_mean_loss = 1053.09
        exp_stddev_loss = 246.62
        expected_loss_map = [
            dict(asset='a3', pos='15.48 38.25', mean=180.717534009275,
                 stddev=92.2122644809969),
            dict(asset='a2', pos='15.56 38.17', mean=432.225448142534,
                 stddev=186.864456949986),
            dict(asset='a1', pos='15.48 38.09', mean=440.147078317589,
                 stddev=182.615976701858),
        ]

        result = helpers.run_job(scen_cfg, ['--output-type=xml'],
                                 check_output=True)

        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        expected_loss_map_file = helpers.demo_file(
            'scenario_risk/computed_output/loss-map-%s.xml' % job.id)

        self.assertTrue(os.path.exists(expected_loss_map_file))

        self._verify_loss_map(expected_loss_map_file, expected_loss_map)

        actual_mean, actual_stddev = self._mean_stddev_from_result_line(result)

        self.assertAlmostEqual(
            exp_mean_loss, actual_mean, places=self.TOTAL_LOSS_PRECISION)
        self.assertAlmostEqual(
            exp_stddev_loss, actual_stddev, places=self.TOTAL_LOSS_PRECISION)

    @attr('slow')
    def test_scenario_risk_sample_based(self):
        # This QA test is a longer-running test of the Scenario Risk
        # calculator.

        # The vulnerabiilty model has non-zero Coefficients of Variation and
        # therefore exercises the 'sample-based' path through the calculator.
        # This test is configured to produce 1000 ground motion fields at each
        # location of interest (in the test above, only 10 are produced).

        # Since we're seeding the random epsilon sampling, we can consistently
        # reproduce all result values.

        # When these values are compared to the results computed by a similar
        # config which takes the 'mean-based' path (with CoVs = 0), we expect
        # the following:
        # All of the mean values in the 'sample-based' results should be with
        # 5%, + or -, of the 'mean-based' results.
        # The standard deviation values of the 'sample-based' results should
        # simply be greater than those produced with the 'mean-based' method.

        # For comparison, mean and stddev values for the region were computed
        # with 1000 GMFs using the mean-based approach. These values (rounded
        # to 2 decimal places) are:
        mb_mean_loss = 1233.26
        mb_stddev_loss = 443.63
        # Loss map for the mean-based approach:
        mb_loss_map = [
            dict(asset='a3', pos='15.48 38.25', mean=200.54874638,
                stddev=94.2302991022),
            dict(asset='a2', pos='15.56 38.17', mean=510.821363253,
                stddev=259.964152622),
            dict(asset='a1', pos='15.48 38.09', mean=521.885458891,
                stddev=244.825980356),
        ]

        # Sanity checks are done. Let's do this.
        scen_cfg = helpers.demo_file(
            'scenario_risk/config_sample-based_qa.gem')
        result = helpers.run_job(scen_cfg, ['--output-type=xml'],
            check_output=True)

        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        expected_loss_map_file = helpers.demo_file(
            'scenario_risk/computed_output/loss-map-%s.xml' % job.id)
        self.assertTrue(os.path.exists(expected_loss_map_file))

        loss_map = self._loss_map_result_from_file(expected_loss_map_file)
        self._verify_loss_map_within_range(sorted(mb_loss_map),
            sorted(loss_map), 0.05)

        exp_mean_loss, exp_stddev_loss = self._mean_stddev_from_result_line(
            result)
        self.assertAlmostEqual(mb_mean_loss, exp_mean_loss,
            delta=mb_mean_loss * 0.05)
        self.assertTrue(exp_stddev_loss > mb_stddev_loss)

    def test_scenario_risk_insured_losses(self):
        # This test exercises the 'mean-based' path through the Scenario Risk
        # calculator. There is no random sampling done here so the results are
        # 100% predictable.
        scen_cfg = helpers.qa_file('scenario_risk_insured_losses/config.gem')

        exp_mean_loss = 799.102578
        exp_stddev_loss = 382.148808
        expected_loss_map = [
            dict(asset='a3', pos='15.48 38.25', mean=156.750910806,
                stddev=100.422061776),
            dict(asset='a2', pos='15.56 38.17', mean=314.859579324,
                stddev=293.976254984),
            dict(asset='a1', pos='15.48 38.09', mean=327.492087529,
                stddev=288.47906994),
            ]

        result = helpers.run_job(scen_cfg, ['--output-type=xml'],
            check_output=True)

        job = OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

        expected_loss_map_file = helpers.qa_file(
            'scenario_risk_insured_losses/computed_output/insured-loss-map%s'
            '.xml' % job.id)

        self.assertTrue(os.path.exists(expected_loss_map_file))

        self._verify_loss_map(expected_loss_map_file, expected_loss_map)

        actual_mean, actual_stddev = self._mean_stddev_from_result_line(result)

        self.assertAlmostEqual(
            exp_mean_loss, actual_mean, places=self.TOTAL_LOSS_PRECISION)
        self.assertAlmostEqual(
            exp_stddev_loss, actual_stddev, places=self.TOTAL_LOSS_PRECISION)

        # Cleaning generated results file.
        rmtree(QA_OUTPUT_DIR)
