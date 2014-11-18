# Copyright (c) 2010-2014, GEM Foundation.
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

import shutil
import tempfile
import unittest
import mock

from nose.plugins.attrib import attr

from openquake.engine.db import models
from openquake.engine.export import core

from openquake.engine.tests.export.core_test import BaseExportTestCase
from openquake.engine.tests.utils import helpers


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
        rc.exposure_model.category = "air"
        rc.exposure_model.unit = mock.Mock(return_value="bucks")
        rc.interest_rate = 0.3
        rc.asset_life_expectancy = 10

    def tearDown(self):
        self.output_patch.stop()

    def test_export_agg_loss_curve(self):
        writer = 'openquake.commonlib.risk_writers.AggregateLossCurveXMLWriter'

        self.output_mock.loss_curve.id = 0
        self.output_mock.loss_curve.loss_type = "structural"
        self.output_mock.output_type = 'agg_loss_curve'
        with mock.patch(writer) as m:
            ret = core.export_output(('agg_loss_curve', 'xml'),
                                     self.output_mock, "/tmp/")

            self.assertEqual([(('/tmp/loss-curves-0.xml', ),
                              {'gsim_tree_path': None,
                               'investigation_time': 30,
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks',
                               'loss_type': 'structural'})], m.call_args_list)
            self.assertEqual('/tmp/loss-curves-0.xml', ret)

    def test_export_loss_curve(self):
        writer = 'openquake.commonlib.risk_writers.LossCurveXMLWriter'

        self.output_mock.loss_curve.id = 0
        self.output_mock.loss_curve.insured = False
        self.output_mock.loss_curve.loss_type = "structural"
        self.output_mock.output_type = 'loss_curve'

        with mock.patch(writer) as m:
            ret = core.export_output(('loss_curve', 'xml'),
                                     self.output_mock, "/tmp/")

            self.assertEqual([(('/tmp/loss-curves-0.xml', ),
                              {'gsim_tree_path': None,
                               'investigation_time': 30,
                               'insured': False,
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks',
                               'loss_type': 'structural'})], m.call_args_list)
            self.assertEqual('/tmp/loss-curves-0.xml', ret)

    def test_export_loss_map(self):
        writer = 'openquake.commonlib.risk_writers.LossMapXMLWriter'

        self.output_mock.loss_map.id = 0
        self.output_mock.loss_map.poe = 0.1
        self.output_mock.loss_map.loss_type = "structural"
        self.output_mock.output_type = 'loss_map'

        with mock.patch(writer) as m:
            ret = core.export_output(('loss_map', 'xml'),
                                     self.output_mock, "/tmp/")

            self.assertEqual([(('/tmp/loss-maps-0.xml', ),
                              {'gsim_tree_path': None,
                               'investigation_time': 30,
                               'loss_category': 'air',
                               'poe': 0.1,
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks',
                               'loss_type': 'structural'})], m.call_args_list)
            self.assertEqual('/tmp/loss-maps-0.xml', ret)

    def test_export_bcr_distribution(self):
        writer = 'openquake.commonlib.risk_writers.BCRMapXMLWriter'

        self.output_mock.bcr_distribution.id = 0
        self.output_mock.bcr_distribution.loss_type = "structural"
        self.output_mock.output_type = 'bcr_distribution'

        with mock.patch(writer) as m:
            ret = core.export_output(('bcr_distribution', 'xml'),
                                     self.output_mock, "/tmp/")

            self.assertEqual([(('/tmp/bcr-distribution-0.xml', ),
                              {'asset_life_expectancy': 10,
                               'gsim_tree_path': None,
                               'interest_rate': 0.3,
                               'quantile_value': None,
                               'source_model_tree_path': None,
                               'statistics': 'mean',
                               'unit': 'bucks',
                               'loss_type': 'structural'})], m.call_args_list)
            self.assertEqual('/tmp/bcr-distribution-0.xml', ret)

    def test_export_aggregate_loss(self):
        writer = 'csv.writer'

        self.output_mock.aggregate_loss.id = 0
        self.output_mock.aggregate_loss.mean = 1
        self.output_mock.aggregate_loss.std_dev = 2
        self.output_mock.aggregate_loss.loss_type = "structural"
        self.output_mock.output_type = 'aggregate_loss'

        with mock.patch(writer) as m:
            ret = core.export_output(('aggregate_loss', 'csv'),
                                     self.output_mock, "/tmp/")

            self.assertEqual([], m.writerow.call_args_list)
            self.assertEqual("/tmp/aggregate-loss-0.csv", ret)


class ClassicalExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_classical_risk_export(self):
        target_dir = tempfile.mkdtemp()
        try:
            haz_cfg = helpers.get_data_path(
                'end-to-end-hazard-risk/job_haz_classical.ini'
            )
            risk_cfg = helpers.get_data_path(
                'end-to-end-hazard-risk/job_risk_classical.ini'
            )

            haz_job = helpers.run_job(haz_cfg).job
            # Run the risk on all outputs produced by the haz calc:
            risk_job = helpers.run_job(
                risk_cfg, hazard_calculation_id=haz_job.id).job

            risk_outputs = models.Output.objects.filter(oq_job=risk_job)

            loss_curve_outputs = risk_outputs.filter(output_type='loss_curve')
            loss_map_outputs = risk_outputs.filter(output_type='loss_map')

            # 16 logic tree realizations + 1 mean + 2 quantiles = 19
            # + 19 insured loss curves
            self.assertEqual(38, loss_curve_outputs.count())
            # make sure the mean and quantile curve sets got created correctly
            loss_curves = models.LossCurve.objects.filter(
                output__oq_job=risk_job,
                insured=False
            )
            # sanity check
            self.assertEqual(19, loss_curves.count())

            insured_curves = models.LossCurve.objects.filter(
                output__oq_job=risk_job,
                insured=True
            )
            # sanity check
            self.assertEqual(19, insured_curves.count())

            # mean
            self.assertEqual(1, loss_curves.filter(statistics='mean').count())
            # quantiles
            self.assertEqual(
                2, loss_curves.filter(statistics='quantile').count()
            )

            # mean
            self.assertEqual(
                1, insured_curves.filter(statistics='mean').count())
            # quantiles
            self.assertEqual(
                2, insured_curves.filter(statistics='quantile').count()
            )

            # 16 logic tree realizations = 16 loss map + 1 mean loss
            # map + 2 quantile loss map
            self.assertEqual(19, loss_map_outputs.count())

            # 19 loss fractions
            loss_fraction_outputs = risk_outputs.filter(
                output_type="loss_fraction")
            self.assertEqual(19, loss_fraction_outputs.count())

            # Now try to export everything, just to do a "smoketest" of the
            # exporter code:
            loss_curve_files = []
            for o in loss_curve_outputs:
                loss_curve_files.append(core.export(o.id, target_dir, 'xml'))

            loss_map_files = []
            for o in loss_map_outputs:
                loss_map_files.append(core.export(o.id, target_dir, 'xml'))

            self.assertEqual(38, len(loss_curve_files))
            self.assertEqual(19, len(loss_map_files))

            for f in loss_curve_files:
                self._test_exported_file(f)
            for f in loss_map_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)


class EventBasedExportTestCase(BaseExportTestCase):

    @attr('slow')
    def test_event_based_risk_export(self):
        target_dir = tempfile.mkdtemp()
        try:
            haz_cfg = helpers.get_data_path(
                'end-to-end-hazard-risk/job_haz_event_based.ini'
            )
            risk_cfg = helpers.get_data_path(
                'end-to-end-hazard-risk/job_risk_event_based.ini'
            )

            haz_job = helpers.run_job(haz_cfg).job
            # Run the risk on all outputs produced by the haz calc:
            risk_job = helpers.run_job(
                risk_cfg, hazard_calculation_id=haz_job.id).job

            risk_outputs = models.Output.objects.filter(oq_job=risk_job)

            agg_loss_curve_outputs = risk_outputs.filter(
                output_type='agg_loss_curve')
            loss_curve_outputs = risk_outputs.filter(output_type='loss_curve')
            loss_map_outputs = risk_outputs.filter(output_type='loss_map')

            # (1 mean + 2 quantiles) * 2 (as there also insured curves)
            self.assertEqual(6, loss_curve_outputs.count())

            # 16 rlzs + 16 (due to insured curves)
            event_loss_curve_outputs = risk_outputs.filter(
                output_type='event_loss_curve')
            self.assertEqual(32, event_loss_curve_outputs.count())
            self.assertEqual(16, agg_loss_curve_outputs.count())

            # make sure the mean and quantile curve sets got created correctly
            loss_curves = models.LossCurve.objects.filter(
                output__oq_job=risk_job
            )
            # sanity check (16 aggregate loss curve + 38 loss curves)
            self.assertEqual(54, loss_curves.count())
            # mean
            self.assertEqual(2, loss_curves.filter(statistics='mean').count())
            # quantiles
            self.assertEqual(
                4, loss_curves.filter(statistics='quantile').count()
            )

            # 16 logic tree realizations = 16 loss map + 1 mean loss
            # map + 2 quantile loss map
            self.assertEqual(19, loss_map_outputs.count())

            # 16 event loss table (1 per rlz)
            event_loss_tables = risk_outputs.filter(output_type="event_loss")
            self.assertEqual(16, event_loss_tables.count())

            # 32 loss fractions
            loss_fraction_outputs = risk_outputs.filter(
                output_type="loss_fraction")
            self.assertEqual(32, loss_fraction_outputs.count())

            # Now try to export everything, just to do a "smoketest" of the
            # exporter code:
            loss_curve_files = []
            for o in loss_curve_outputs:
                loss_curve_files.append(core.export(o.id, target_dir, 'xml'))
            for o in loss_fraction_outputs:
                loss_curve_files.append(core.export(o.id, target_dir, 'xml'))
            for o in event_loss_curve_outputs:
                loss_curve_files.append(core.export(o.id, target_dir, 'xml'))

            agg_loss_curve_files = []
            for o in agg_loss_curve_outputs:
                agg_loss_curve_files.append(
                    core.export(o.id, target_dir, 'xml')
                )

            event_loss_table_files = []
            for o in event_loss_tables:
                event_loss_table_files.append(
                    core.export(o.id, target_dir, 'csv')
                )

            loss_map_files = []
            for o in loss_map_outputs:
                loss_map_files.append(core.export(o.id, target_dir, 'xml'))

            self.assertEqual(70, len(loss_curve_files))
            self.assertEqual(16, len(agg_loss_curve_files))
            self.assertEqual(16, len(event_loss_table_files))
            self.assertEqual(19, len(loss_map_files))

            for f in loss_curve_files:
                self._test_exported_file(f)
            for f in loss_map_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)
