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

import numpy
from openquake.qa_tests_data.scenario_damage import case_15
from openquake.qa_tests_data.infrastructure_risk import (
    five_nodes_demsup_directed, five_nodes_demsup_directedunweighted,
    five_nodes_demsup_multidirected, demand_supply, directed, eff_loss_random,
    multidirected, multigraph, undirected)
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase

aac = numpy.testing.assert_allclose


class ScenarioDamageTestCase(CalculatorTestCase):

    def test_case_15(self):
        self.run_calc(case_15.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_ccl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_ccl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-dem_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-dem_cl.csv', fname, check_all_columns=True)

    def test_demand_supply(self):
        self.run_calc(demand_supply.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['ccl'].values),
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.0],
             [0.2964959568733154],
             [0.3333333333333333],
             [0.5202279202279202],
            ])

        aac([
             list(ds.read_df('infra-event_ccl')['CCL'].values),
             list(ds.read_df('infra-event_efl')['EFFLoss'].values),
             list(ds.read_df('infra-event_pcl')['PCL'].values),
             list(ds.read_df('infra-event_wcl')['WCL'].values),
            ],
            [
             [0.],
             [0.29649596],
             [0.33333333],
             [0.52022792],
            ])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E', 'F', 'G'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.1273885350318472, 0.13953488372093012, 0.23076923076923073, 1.0,
             0.23076923076923073, 0.13953488372093012, 0.1273885350318472])

        self.assertEqual(list(ds.read_df('infra-dem_cl')['id']),
                         ['A', 'E', 'G'])
        aac(list(ds.read_df('infra-dem_cl')['CN']),
            [0.0, 0.0, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['CCL_node']),
            [0.0, 0.0, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['PCL_node']),
            [0.33333333333333337, 0.33333333333333337, 0.33333333333333337])
        aac(list(ds.read_df('infra-dem_cl')['WCL_node']),
            [0.5384615384615384, 0.5555555555555556, 0.4666666666666667])

    def test_directed(self):
        self.run_calc(directed.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.19123965855782582],
             [0.25],
             [0.2777777777777778],
            ])

        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.0, 0.38247931711565164])
        aac(list(ds.read_df('infra-event_pcl')['PCL'].values),
            [0.0, 0.5])
        aac(list(ds.read_df('infra-event_wcl')['WCL'].values),
            [0.0, 0.5555555555555556])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.5, 0.04774535809018569, 0.3164724576271186, 0.11955593509820671,
             0.0])

        self.assertEqual(list(ds.read_df('infra-taz_cl')['id']),
                         ['A', 'B', 'C'])
        aac(list(ds.read_df('infra-taz_cl')['PCL_node']),
            [0.0, 0.5, 0.25])
        aac(list(ds.read_df('infra-taz_cl')['WCL_node']),
            [0.0, 0.5, 0.33333333333333337])

    def test_eff_loss_random(self):
        self.run_calc(eff_loss_random.__file__, 'job.ini')
        ds = self.calc.datastore

        aac(list(ds.read_df('infra-avg_loss')['efl'].values),
            [0.2603130360205833])

        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.2603130360205833])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E', 'F', 'G'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.09602352640327334, 0.10010409437890358, 0.15322580645161288,
             0.09355742296918781, 0.35130718954248374, 0.41342779580215844,
             1.0])

    def test_five_nodes_demsup_directed(self):
        self.run_calc(five_nodes_demsup_directed.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['ccl'].values),
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.25],
             [0.13959390862944165],
             [0.25],
             [0.25],
            ])

        aac(list(ds.read_df('infra-event_ccl')['CCL'].values),
            [0.0, 0.5])
        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.0, 0.2791878172588833])
        aac(list(ds.read_df('infra-event_pcl')['PCL'].values),
            [0.0, 0.5])
        aac(list(ds.read_df('infra-event_wcl')['WCL'].values),
            [0.0, 0.5])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.41044776119402987, 0.0, 0.0, 0.0, 0.0])

        self.assertEqual(list(ds.read_df('infra-dem_cl')['id']), ['B', 'C'])
        aac(list(ds.read_df('infra-dem_cl')['CN']),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['CCL_node']),
            [0.5, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['PCL_node']),
            [0.5, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['WCL_node']),
            [0.5, 0.0])

    def test_five_nodes_demsup_directedunweighted(self):
        self.run_calc(five_nodes_demsup_directedunweighted.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['ccl'].values),
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.5],
             [0.127906976744186],
             [0.5],
             [0.5],
            ])

        aac(list(ds.read_df('infra-event_ccl')['CCL'].values),
            [0.0, 1.0])
        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.0, 0.255813953488372])
        aac(list(ds.read_df('infra-event_pcl')['PCL'].values),
            [0.0, 1.0])
        aac(list(ds.read_df('infra-event_wcl')['WCL'].values),
            [0.0, 1.0])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.3235294117647059, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(list(ds.read_df('infra-dem_cl')['id']), ['B'])

        aac(list(ds.read_df('infra-dem_cl')['CN']), [0.0])
        aac(list(ds.read_df('infra-dem_cl')['CCL_node']), [0.5])
        aac(list(ds.read_df('infra-dem_cl')['PCL_node']), [0.5])
        aac(list(ds.read_df('infra-dem_cl')['WCL_node']), [0.5])

    def test_five_nodes_demsup_multidirected(self):
        self.run_calc(five_nodes_demsup_multidirected.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['ccl'].values),
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.0],
             [0.032774739543551985],
             [0.0],
             [0.07777777777777778],
            ])

        aac(list(ds.read_df('infra-event_ccl')['CCL'].values),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.0, 0.06554947908710397])
        aac(list(ds.read_df('infra-event_pcl')['PCL'].values),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-event_wcl')['WCL'].values),
            [0.0, 0.15555555555555556])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.12209523809523799, 0.0, 0.03353416313559312,
             0.011058923996584154, 0.0])

        self.assertEqual(list(ds.read_df('infra-dem_cl')['id']), ['B', 'C'])
        aac(list(ds.read_df('infra-dem_cl')['CN']),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['CCL_node']),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['PCL_node']),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['WCL_node']),
            [0.09999999999999998, 0.05555555555555558])

    def test_multidirected(self):
        self.run_calc(multidirected.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.032774739543551985],
             [0.0],
             [0.03437796771130103],
            ])

        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.0, 0.06554947908710397])
        aac(list(ds.read_df('infra-event_pcl')['PCL'].values),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-event_wcl')['WCL'].values),
            [0.0, 0.06875593542260205])
        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E'])

        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.12209523809523799, 0.0, 0.03353416313559312,
             0.011058923996584154, 0.0])

        self.assertEqual(list(ds.read_df('infra-taz_cl')['id']),
                         ['A', 'B', 'C'])
        aac(list(ds.read_df('infra-taz_cl')['PCL_node']),
            [0.0, 0.0, 0.0])
        aac(list(ds.read_df('infra-taz_cl')['WCL_node']),
            [0.0, 0.08461538461538454, 0.018518518518518545])

    def test_multigraph(self):
        self.run_calc(multigraph.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.06562726613488049],
             [0.0],
             [0.0753968253968254],
            ])

        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.0, 0.13125453226976097])
        aac(list(ds.read_df('infra-event_pcl')['PCL'].values),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-event_wcl')['WCL'].values),
            [0.0, 0.1507936507936508])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.1929637526652452, 0.03571428571428573, 0.0,
             0.008403361344537863, 0.10588235294117648])

        self.assertEqual(list(ds.read_df('infra-taz_cl')['id']),
                         ['A', 'B', 'C'])
        aac(list(ds.read_df('infra-taz_cl')['PCL_node']),
            [0.0, 0.0, 0.0])
        aac(list(ds.read_df('infra-taz_cl')['WCL_node']),
            [0.11904761904761907, 0.10714285714285715, 0.0])

    def test_undirected(self):
        self.run_calc(undirected.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             list(ds.read_df('infra-avg_loss')['efl'].values),
             list(ds.read_df('infra-avg_loss')['pcl'].values),
             list(ds.read_df('infra-avg_loss')['wcl'].values),
            ],
            [
             [0.0870745160085263],
             [0.0],
             [0.0977366255144033],
            ])

        aac(list(ds.read_df('infra-event_efl')['EFFLoss'].values),
            [0.0, 0.1741490320170526])
        aac(list(ds.read_df('infra-event_pcl')['PCL'].values),
            [0.0, 0.0])
        aac(list(ds.read_df('infra-event_wcl')['WCL'].values),
            [0.0, 0.1954732510288066])

        self.assertEqual(list(ds.read_df('infra-node_el')['id']),
                         ['A', 'B', 'C', 'D', 'E'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.2560250694579053, 0.04629629629629628, 0.0,
             0.008403361344537863, 0.14438502673796794])

        self.assertEqual(list(ds.read_df('infra-taz_cl')['id']),
                         ['A', 'B', 'C'])
        aac(list(ds.read_df('infra-taz_cl')['PCL_node']),
            [0.0, 0.0, 0.0])
        aac(list(ds.read_df('infra-taz_cl')['WCL_node']),
            [0.154320987654321, 0.1388888888888889, 0.0])
