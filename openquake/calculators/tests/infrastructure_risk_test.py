# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import numpy
from openquake.baselib import InvalidFile
from openquake.qa_tests_data.infrastructure_risk import (
    case_15, five_nodes_demsup_directed, five_nodes_demsup_directedunweighted,
    five_nodes_demsup_multidirected, demand_supply, directed, eff_loss_random,
    multidirected, multigraph, undirected)
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase

aac = numpy.testing.assert_allclose


class InfrastructureRiskTestCase(CalculatorTestCase):

    # TODO: we need tests also for event-based

    def _check_csv_outputs(self, outputs_list, datastore, testcase,
                           replace_expected=False):
        for output in outputs_list:
            expected_fname = 'expected/infra-' + output + '.csv'
            expected_path = os.path.join(
                os.path.dirname(testcase.__file__), expected_fname)
            [got_path] = export(('infra-' + output, 'csv'), datastore)
            if replace_expected:
                shutil.copy2(got_path, expected_path)
            else:
                self.assertEqualFiles(
                    got_path, expected_path, check_text=True)
        if replace_expected:
            raise ValueError('Remember to set replace_expected to False!')

    def test_case_15(self):
        self.run_calc(case_15.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'node_el avg_loss event_ccl event_efl event_pcl event_wcl'
            ' dem_cl').split()

        self._check_csv_outputs(outputs_list, ds, case_15)

    def test_demand_supply(self):
        self.run_calc(demand_supply.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_ccl event_efl event_pcl event_wcl node_el'
            ' dem_cl').split()

        self._check_csv_outputs(outputs_list, ds, demand_supply)

    def test_directed(self):
        self.run_calc(directed.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_efl event_pcl event_wcl node_el taz_cl').split()

        self._check_csv_outputs(outputs_list, ds, directed)

    def test_eff_loss_random(self):
        self.run_calc(eff_loss_random.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_efl node_el').split()

        self._check_csv_outputs(outputs_list, ds, eff_loss_random)

    def test_five_nodes_demsup_directed(self):
        self.run_calc(five_nodes_demsup_directed.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_ccl event_efl event_pcl event_wcl node_el'
            ' dem_cl').split()

        self._check_csv_outputs(outputs_list, ds, five_nodes_demsup_directed)

    def test_five_nodes_demsup_directedunweighted(self):
        self.run_calc(five_nodes_demsup_directedunweighted.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_ccl event_efl event_pcl event_wcl node_el'
            ' dem_cl').split()

        self._check_csv_outputs(
            outputs_list, ds, five_nodes_demsup_directedunweighted)

    def test_five_nodes_demsup_multidirected(self):
        self.run_calc(five_nodes_demsup_multidirected.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_ccl event_efl event_pcl event_wcl node_el'
            ' dem_cl').split()

        self._check_csv_outputs(
            outputs_list, ds, five_nodes_demsup_multidirected)

    def test_multidirected(self):
        self.run_calc(multidirected.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_efl event_pcl event_wcl node_el taz_cl').split()

        self._check_csv_outputs(outputs_list, ds, multidirected)

    def test_multigraph(self):
        self.run_calc(multigraph.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_efl event_pcl event_wcl node_el taz_cl').split()

        self._check_csv_outputs(outputs_list, ds, multigraph)

    def test_undirected(self):
        self.run_calc(undirected.__file__, 'job.ini')
        ds = self.calc.datastore

        outputs_list = (
            'avg_loss event_efl event_pcl event_wcl node_el taz_cl').split()

        self._check_csv_outputs(outputs_list, ds, undirected)

    def test_missing_mandatory_column(self):
        with self.assertRaises(InvalidFile) as exc:
            self.run_calc(undirected.__file__,
                          'job_missing_mandatory_column.ini')
        exc_msg = exc.exception.args[0]
        got_msg_head = (
            'The following mandatory columns are missing in the exposure')
        got_msg_tail = (
            'exposure_demo_nodes_missing_mandatory_column.csv": [\'purpose\']')
        self.assertIn(got_msg_head, exc_msg)
        self.assertIn(got_msg_tail, exc_msg)

    def test_incompatible_purposes(self):
        with self.assertRaises(InvalidFile) as exc:
            self.run_calc(demand_supply.__file__,
                          'job_incompatible_purposes.ini')
        exc_msg = exc.exception.args[0]
        got_msg_head = 'Column "purpose" of'
        got_msg_tail = (
            'exposure_demo_nodes_incompatible_purposes.csv can not contain'
            ' at the same time the value "TAZ" and either "source"'
            ' or "demand".')
        self.assertIn(got_msg_head, exc_msg)
        self.assertIn(got_msg_tail, exc_msg)

    def test_multiple_graphtypes(self):
        with self.assertRaises(InvalidFile) as exc:
            self.run_calc(multigraph.__file__, 'job_multiple_graphtypes.ini')
        exc_msg = exc.exception.args[0]
        got_msg_head = 'The column "graphtype" of'
        got_msg_tail = (
            'exposure_demo_nodes_multiple_graphtypes.csv" must contain'
            ' all equal values.')
        self.assertIn(got_msg_head, exc_msg)
        self.assertIn(got_msg_tail, exc_msg)

    def test_weighted_nodes(self):
        with self.assertLogs(level='WARNING') as log:
            expected_log_head = 'Node weights different from 1 present in'
            expected_log_tail = (
                'exposure_demo_weighted_nodes.csv will be ignored.'
                ' Handling node weights is not implemented yet.')
            self.run_calc(eff_loss_random.__file__, 'job_weighted_nodes.ini')
            warning_was_found = False
            for record in log.records:
                if record.msg.startswith(expected_log_head):
                    self.assertIn(expected_log_tail, record.msg)
                    warning_was_found = True
            self.assertTrue(
                warning_was_found,
                'If there are node weights != 1, a warning should be raised')
