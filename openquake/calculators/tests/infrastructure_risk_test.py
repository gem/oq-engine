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
        nodes = self.calc.datastore.read_df('functional_demand_nodes')
        ids = list(nodes.id)
        expected_ids = [
            'D1', 'D10', 'D11', 'D12', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7',
            'D8', 'D9', 'E18a', 'E18b', 'E18c', 'E20a', 'E20b', 'E20c', 'P1',
            'P2', 'P3', 'W1', 'W2']
        self.assertEqual(ids, expected_ids)
        eff_loss = list(nodes.Eff_loss)
        expected_eff_loss = [
            0.45544827586206926, 0.5793014268727713, 0.5733459357277877,
            0.5768746061751727, 0.48184873949579826, 0.42961538461538445,
            0.3932336448598129, 0.5183054003724399, 0.4915661592505851,
            0.575451843043996, 0.5289210577108661, 0.522733063115228, 0.0,
            0.7005583955957531, 0.0, 0.0, 0.6988079777365492, 0.0,
            0.7545867098865477, 0.7081277533039649, 0.7987959183673469,
            0.7617334360554696, 0.835219136835062]
        aac(eff_loss, expected_eff_loss)

    def test_demand_supply(self):
        self.run_calc(demand_supply.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_ccl'][()],
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.0,
             0.2964959568733154,
             0.3333333333333333,
             0.5202279202279202,
            ])
        # TODO: also check:
        #       'dem_cl', 'event_connectivity_loss_ccl',
        #       'event _connectivity_loss_eff', 'event_connectivity_loss_pcl',
        #       'event_connectivity_loss_wcl', 'node_el'

    def test_directed(self):
        self.run_calc(directed.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.19123965855782582,
             0.25,
             0.2777777777777778,
            ])
        # TODO: also check:
        #       'avg_connectivity_loss_eff', 'avg_connectivity_loss_pcl',
        #       'avg_connectivity_loss_wcl', 'event_connectivity_loss_eff',
        #       'event_connectivity_loss_pcl', 'event_connectivity_loss_wcl',
        #       'node_el', 'taz_cl'

    def test_eff_loss_random(self):
        self.run_calc(eff_loss_random.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_eff'][()],
            ],
            [
             0.2603130360205833,
            ])
        # TODO: also check:
        #       'event_connectivity_loss_eff','functional_demand_nodes',
        #       'node_el'

    def test_five_nodes_demsup_directed(self):
        self.run_calc(five_nodes_demsup_directed.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_ccl'][()],
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.25,
             0.13959390862944165,
             0.25,
             0.25,
            ])
        # TODO: also check:
        #       'dem_cl', 'event_connectivity_loss_ccl',
        #       'event_connectivity_loss_eff', 'event_connectivity_loss_pcl',
        #       'event_connectivity_loss_wcl', 'functional_demand_nodes',
        #       'node_el'

    def test_five_nodes_demsup_directedunweighted(self):
        self.run_calc(five_nodes_demsup_directedunweighted.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_ccl'][()],
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.5,
             0.127906976744186,
             0.5,
             0.5
            ])
        # TODO: also check:
        #       'dem_cl', 'event_connectivity_loss_ccl',
        #       'event_connectivity_loss_eff', 'event_connectivity_loss_pcl',
        #       'event_connectivity_loss_wcl', 'functional_demand_nodes',
        #       'node_el'

    def test_five_nodes_demsup_multidirected(self):
        self.run_calc(five_nodes_demsup_multidirected.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_ccl'][()],
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.0,
             0.032774739543551985,
             0.0,
             0.07777777777777778,
            ])
        # TODO: also check:
        #       'dem_cl', 'event_connectivity_loss_ccl',
        #       'event_connectivity_loss_eff', 'event_connectivity_loss_pcl',
        #       'event_connectivity_loss_wcl', 'functional_demand_nodes',
        #       'node_el',

    def test_multidirected(self):
        self.run_calc(multidirected.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.032774739543551985,
             0.0,
             0.03437796771130103,
            ])
        # TODO: also check:
        #       'event_connectivity_loss_eff', 'event_connectivity_loss_pcl',
        #       'event_connectivity_loss_wcl', 'functional_demand_nodes',
        #       'node_el', 'taz_cl'

    def test_multigraph(self):
        self.run_calc(multigraph.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.06562726613488049,
             0.0,
             0.0753968253968254,
            ])
        # TODO: check also:
        #       'event_connectivity_loss_eff', 'event_connectivity_loss_pcl',
        #       'event_connectivity_loss_wcl', 'functional_demand_nodes',
        #       'node_el', 'taz_cl'

    def test_undirected(self):
        self.run_calc(undirected.__file__, 'job.ini')
        ds = self.calc.datastore
        aac([
             ds['avg_connectivity_loss_eff'][()],
             ds['avg_connectivity_loss_pcl'][()],
             ds['avg_connectivity_loss_wcl'][()],
            ],
            [
             0.0870745160085263,
             0.0,
             0.0977366255144033,
            ])
        # TODO: check also:
        #       'event_connectivity_loss_eff', 'event_connectivity_loss_pcl',
        #       'event_connectivity_loss_wcl', 'functional_demand_nodes',
        #       'node_el', 'taz_cl',
