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

import unittest
import mock

from openquake.engine.export import risk

from tests.utils import helpers


class ExportTestCase(unittest.TestCase):

    def setUp(self):
        self.output_mock = mock.Mock()
        self.output_patch = helpers.patch(
            'openquake.engine.db.models.Output.objects.get')
        m = self.output_patch.start()
        m.return_value = self.output_mock

        self.output_mock.hazard_metadata.investigation_time = 30
        self.output_mock.hazard_metadata.statistics = "mean"
        self.output_mock.hazard_metadata.quantile = None
        self.output_mock.hazard_metadata.sm_path = None
        self.output_mock.hazard_metadata.gsim_path = None
        rc = self.output_mock.oq_job.risk_calculation
        rc.exposure_model.stco_unit = "bucks"
        rc.exposure_model.category = "air"
        rc.interest_rate = 0.3
        rc.asset_life_expectancy = 10

    def tearDown(self):
        self.output_patch.stop()

    def test_export_agg_loss_curve(self):
        writer = 'openquake.nrmllib.risk.writers.AggregateLossCurveXMLWriter'

        self.output_mock.loss_curve.id = 0
        with mock.patch(writer) as m:
            ret = risk.export_agg_loss_curve(self.output_mock, "/tmp/")

            self.assertEqual([((),
                              {'gsim_tree_path': None,
                               'investigation_time': 30,
                               'path': '/tmp/loss-curves-0.xml',
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks'})], m.call_args_list)
            self.assertEqual('/tmp/loss-curves-0.xml', ret)

    def test_export_loss_curve(self):
        writer = 'openquake.nrmllib.risk.writers.LossCurveXMLWriter'

        self.output_mock.loss_curve.id = 0
        self.output_mock.loss_curve.insured = False

        with mock.patch(writer) as m:
            ret = risk.export_loss_curve(self.output_mock, "/tmp/")

            self.assertEqual([((),
                              {'gsim_tree_path': None,
                               'investigation_time': 30,
                               'insured': False,
                               'path': '/tmp/loss-curves-0.xml',
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks'})], m.call_args_list)
            self.assertEqual('/tmp/loss-curves-0.xml', ret)

    def test_export_loss_map(self):
        writer = 'openquake.nrmllib.risk.writers.LossMapXMLWriter'

        self.output_mock.loss_map.id = 0
        self.output_mock.loss_map.poe = 0.1

        with mock.patch(writer) as m:
            ret = risk.export_loss_map(self.output_mock, "/tmp/")

            self.assertEqual([((),
                              {'gsim_tree_path': None,
                               'investigation_time': 30,
                               'loss_category': 'air',
                               'path': '/tmp/loss-maps-0-poe-0.1.xml',
                               'poe': 0.1,
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks'})], m.call_args_list)
            self.assertEqual('/tmp/loss-maps-0-poe-0.1.xml', ret)

    def test_export_bcr_distribution(self):
        writer = 'openquake.nrmllib.risk.writers.BCRMapXMLWriter'

        self.output_mock.bcr_distribution.id = 0

        with mock.patch(writer) as m:
            ret = risk.export_bcr_distribution(self.output_mock, "/tmp/")

            self.assertEqual([((),
                              {'asset_life_expectancy': 10,
                               'gsim_tree_path': None,
                               'interest_rate': 0.3,
                               'path': '/tmp/bcr-distribution-0.xml',
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks'})], m.call_args_list)
            self.assertEqual('/tmp/bcr-distribution-0.xml', ret)

    def test_export_aggregate_loss(self):
        writer = 'csv.writer'

        self.output_mock.aggregateloss.id = 0
        self.output_mock.aggregateloss.mean = 1
        self.output_mock.aggregateloss.std_dev = 2

        with mock.patch(writer) as m:
            ret = risk.export_aggregate_loss(self.output_mock, "/tmp/")

            self.assertEqual([], m.writerow.call_args_list)
            self.assertEqual("/tmp/aggregate-loss-0.csv", ret)
