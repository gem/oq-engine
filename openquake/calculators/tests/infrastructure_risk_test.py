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
from openquake.calculators.tests import CalculatorTestCase

aac = numpy.testing.assert_allclose


class ScenarioDamageTestCase(CalculatorTestCase):

    def test_case_15(self):
        self.run_calc(case_15.__file__, 'job.ini')
        ds = self.calc.datastore
        self.assertEqual(
            list(ds.read_df('infra-node_el')['id']),
            ['D1', 'D10', 'D11', 'D12', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7',
             'D8', 'D9', 'E18a', 'E18b', 'E18c', 'E20a', 'E20b', 'E20c', 'P1',
             'P2', 'P3', 'W1', 'W2'])
        aac(list(ds.read_df('infra-node_el')['Eff_loss']),
            [0.45544827586206926, 0.5793014268727713, 0.5733459357277877,
             0.5768746061751727, 0.48184873949579826, 0.42961538461538445,
             0.3932336448598129, 0.5183054003724399, 0.4915661592505851,
             0.575451843043996, 0.5289210577108661, 0.522733063115228, 0.0,
             0.7005583955957531, 0.0, 0.0, 0.6988079777365492, 0.0,
             0.7545867098865477, 0.7081277533039649, 0.7987959183673469,
             0.7617334360554696, 0.835219136835062])

        aac([
             ds['infra-avg_ccl'][()],
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.7708333333333335,
             0.5792736375574525,
             0.8479166666666668,
             0.8927160714285713,
            ])

        # FIXME: the following check is very long. We should export to csv and
        # compare with it
        aac([
             list(ds.read_df('infra-event_ccl')['CCL'].values),
             list(ds.read_df('infra-event_efl')['EFFLoss'].values),
             list(ds.read_df('infra-event_pcl')['PCL'].values),
             list(ds.read_df('infra-event_wcl')['WCL'].values),
            ],
            [
             [1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 0.5, 0.0, 0.0, 0.5, 1.0,
              0.6666666666666667, 0.0, 1.0, 0.5833333333333333, 1.0, 1.0,
              0.5, 1.0, 0.0, 1.0, 0.6666666666666667, 1.0, 1.0, 1.0, 1.0,
              0.5, 0.5, 0.5, 1.0, 1.0, 0.5, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0,
              0.5, 0.5, 0.6666666666666667, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5,
              0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.5, 1.0, 0.0,
              1.0, 0.5, 1.0, 1.0, 0.0, 0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 0.5, 1.0, 0.0, 1.0, 1.0, 1.0, 0.5, 1.0,
              1.0, 1.0, 1.0, 1.0, 1.0],
             [0.7632961260669732, 0.8483256730137886, 0.3896257386736706, 0.0,
              0.4555810899540382, 0.6035784635587658, 0.5578463558765595,
              0.10305318450426784, 0.10305318450426784, 0.5387721602101118,
              0.4300722258699936, 0.7226198292843072, 0.3369993434011818,
              0.2942547603414314, 0.607715036112935, 0.8690085357846357,
              0.7564018384766908, 0.4555810899540382, 0.7564018384766908,
              0.0, 0.6093237032173343, 0.697800393959291,
              0.6483913328956009, 0.25695994747209444, 0.7564018384766908,
              0.3896257386736706, 0.4555810899540382, 0.4555810899540382,
              0.4555810899540382, 0.8207485226526593, 0.25695994747209444,
              0.4555810899540382, 0.7564018384766908, 0.8345370978332239,
              0.6125410374261326, 0.7724885095206828, 0.3896257386736706,
              0.7632961260669732, 0.6125410374261326, 0.4555810899540382,
              0.7072225869993436, 0.4555810899540382, 0.7426132632961261,
              0.7288246881155616, 0.8046618516086672, 0.3896257386736706,
              0.4754432042022326, 0.21520026263952707, 0.7770847012475378,
              0.3896257386736706, 0.7564018384766908, 0.10305318450426784,
              0.3243598161523309, 0.7770847012475378, 0.3896257386736706,
              0.7564018384766908, 0.6061063690085359, 0.7564018384766908,
              0.34251477347340764, 0.7564018384766908, 0.5578463558765595,
              0.8483256730137886, 0.4270847012475379, 0.10305318450426784,
              0.6061063690085359, 0.4555810899540382, 0.8253447143795142,
              0.7564018384766908, 0.3896257386736706, 0.3896257386736706,
              0.3896257386736706, 0.7564018384766908, 0.7564018384766908,
              0.7632961260669732, 0.7655942219304006, 0.1995732107682205,
              0.7770847012475378, 0.7793827971109654, 0.7564018384766908,
              0.7564018384766908, 0.7564018384766908, 0.7564018384766908,
              0.8276428102429416, 0.6483913328956009, 0.7724885095206829,
              0.6621799080761656, 0.7564018384766908, 0.6125410374261326,
              0.7564018384766908, 0.18742613263296115, 0.7564018384766908,
              0.7426132632961261, 0.7564018384766908, 0.5136736703873934,
              0.7724885095206828, 0.6621799080761656, 0.723768877216021,
              0.7564018384766908, 0.7564018384766908, 0.3896257386736706],
             [1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 0.75, 0.5, 0.5, 0.75, 1.0,
              0.8333333333333334, 0.5, 1.0, 0.7916666666666666, 1.0, 1.0,
              0.5, 1.0, 0.0, 1.0, 0.8333333333333334, 1.0, 1.0, 1.0, 1.0,
              0.5, 0.5, 0.5, 1.0, 1.0, 0.5, 1.0, 1.0, 0.75, 1.0, 1.0, 1.0,
              0.75, 0.5, 0.8333333333333334, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5,
              0.5, 1.0, 1.0, 1.0, 0.5, 0.5, 1.0, 1.0, 1.0, 0.75, 1.0, 0.5,
              1.0, 0.75, 1.0, 1.0, 0.5, 0.75, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 0.75, 1.0, 0.5, 1.0, 1.0, 1.0, 0.5, 1.0,
              1.0, 1.0, 1.0, 1.0, 1.0],
             [1.0, 1.0, 1.0, 0.0, 0.5213541666666667, 1.0, 0.8933035714285714,
              0.8127480158730158, 0.8127480158730158, 0.8673735119047619,
              1.0, 0.9260416666666665, 0.7216964285714287, 1.0,
              0.9089285714285714, 1.0, 1.0, 0.5213541666666667, 1.0, 0.0,
              1.0, 0.9119047619047619, 1.0, 1.0, 1.0, 1.0,
              0.5213541666666667, 0.5213541666666667, 0.5213541666666667,
              1.0, 1.0, 0.5213541666666667, 1.0, 1.0, 0.8673735119047619,
              1.0, 1.0, 1.0, 0.8673735119047619, 0.5213541666666667,
              0.9392857142857144, 0.5213541666666667, 1.0, 1.0, 1.0, 1.0,
              0.5343749999999999, 0.8196924603174603, 1.0, 1.0, 1.0,
              0.8127480158730158, 0.7216964285714287, 1.0, 1.0, 1.0,
              0.8933035714285714, 1.0, 0.7272519841269842, 1.0,
              0.8933035714285714, 1.0, 1.0, 0.8127480158730158,
              0.8933035714285714, 0.5213541666666667, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 1.0, 0.8127480158730158, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.8673735119047619,
              1.0, 0.7216964285714287, 1.0, 1.0, 1.0, 0.5404017857142857,
              1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            ])

        self.assertEqual(
            list(ds.read_df('infra-dem_cl')['id']),
            ['D1', 'D10', 'D11', 'D12', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7',
             'D8', 'D9'])
        aac(list(ds.read_df('infra-dem_cl')['CN']),
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        aac(list(ds.read_df('infra-dem_cl')['CCL_node']),
            [0.88, 0.68, 0.88, 0.88, 0.88, 0.65, 0.68, 0.65, 0.88, 0.65, 0.66,
             0.88])
        aac(list(ds.read_df('infra-dem_cl')['PCL_node']),
            [0.775, 0.93, 0.93, 0.93, 0.775, 0.76, 0.76, 0.765, 0.76, 0.93,
             0.93, 0.93])
        aac(list(ds.read_df('infra-dem_cl')['WCL_node']),
            [0.8363333333333334, 0.9570000000000001, 0.9566666666666666,
             0.9566666666666666, 0.84625, 0.8157142857142857, 0.82,
             0.82547619047619, 0.827485714285714, 0.9570000000000001,
             0.9573333333333334, 0.9566666666666666])

    def test_demand_supply(self):
        self.run_calc(demand_supply.__file__, 'job.ini')
        ds = self.calc.datastore

        aac([
             ds['infra-avg_ccl'][()],
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.0,
             0.2964959568733154,
             0.3333333333333333,
             0.5202279202279202,
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
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.19123965855782582,
             0.25,
             0.2777777777777778,
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

        aac(ds['infra-avg_efl'][()], 0.2603130360205833)

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
             ds['infra-avg_ccl'][()],
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.25,
             0.13959390862944165,
             0.25,
             0.25,
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
             ds['infra-avg_ccl'][()],
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.5,
             0.127906976744186,
             0.5,
             0.5
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
             ds['infra-avg_ccl'][()],
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.0,
             0.032774739543551985,
             0.0,
             0.07777777777777778,
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
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.032774739543551985,
             0.0,
             0.03437796771130103,
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
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.06562726613488049,
             0.0,
             0.0753968253968254,
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
             ds['infra-avg_efl'][()],
             ds['infra-avg_pcl'][()],
             ds['infra-avg_wcl'][()],
            ],
            [
             0.0870745160085263,
             0.0,
             0.0977366255144033,
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
