# coding=utf-8
# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import os
import unittest

import numpy

from openquake.risklib import scientific, workflows
from openquake.risklib.tests.utils import vectors_from_csv

THISDIR = os.path.dirname(__file__)

gmf = vectors_from_csv('gmf', THISDIR)

assets = [workflows.Asset(
          1, 'SOME-TAXONOMY', 1, (0, 0),
          dict(structural=10),
          insurance_limits=dict(structural=1250),
          deductibles=dict(structural=40))
          ] * 2


class EventBasedTestCase(unittest.TestCase):
    loss_type = 'structural'

    def assert_similar(self, a, b):
        assert a.keys() == b.keys(), (a.keys(), b.keys())
        for k in a:
            self.assertAlmostEqual(a[k], b[k])

    def test_mean_based_with_no_correlation(self):
        # This is a regression test. Data has not been checked
        vf = (
            scientific.VulnerabilityFunction(
                'SOME-TAXONOMY', 'PGA',
                [0.001, 0.2, 0.3, 0.5, 0.7],
                [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.01, 0.02, 0.02, 0.01, 0.03]))
        gmvs = numpy.array([[10., 20., 30., 40., 50.],
                            [1., 2., 3., 4., 5.]])

        epsilons = scientific.make_epsilons(gmvs, seed=1, correlation=0)
        loss_matrix = vf.apply_to(gmvs, epsilons)
        losses_poes = scientific.event_based(
            loss_matrix[0], 120, 30, curve_resolution=4)

        first_curve_integral = scientific.average_loss(losses_poes)

        self.assertAlmostEqual(0.500993631, first_curve_integral)

        wf = workflows.ProbabilisticEventBased(
            'PGA', 'SOME-TAXONOMY',
            vulnerability_functions={self.loss_type: vf},
            risk_investigation_time=50,
            hazard_investigation_time=50,
            ses_per_logic_tree_path=200,
            number_of_logic_tree_samples=0,
            loss_curve_resolution=4,
            conditional_loss_poes=[0.1, 0.5, 0.9],
            insured_losses=False
            )
        out = wf(self.loss_type, assets, gmvs, epsilons, [1, 2, 3, 4, 5])
        self.assert_similar(
            out.event_loss_table,
            {1: 16.246646231503398,
             2: 15.613885199116158,
             3: 15.669704465134854,
             4: 16.241922530992454,
             5: 16.010104452203464,
             })

    def test_mean_based_with_partial_correlation(self):
        # This is a regression test. Data has not been checked
        vf = (
            scientific.VulnerabilityFunction(
                'SOME-TAXONOMY', 'PGA',
                [0.001, 0.2, 0.3, 0.5, 0.7],
                [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.01, 0.02, 0.02, 0.01, 0.03]))
        gmvs = numpy.array([[10., 20., 30., 40., 50.],
                           [1., 2., 3., 4., 5.]])
        epsilons = scientific.make_epsilons(gmvs, seed=1, correlation=0.5)
        loss_matrix = vf.apply_to(gmvs, epsilons)

        losses_poes = scientific.event_based(loss_matrix[0], 120, 30, 4)
        first_curve_integral = scientific.average_loss(losses_poes)

        self.assertAlmostEqual(0.48983614471, first_curve_integral)

        wf = workflows.ProbabilisticEventBased(
            'PGA', 'SOME-TAXONOMY',
            vulnerability_functions={self.loss_type: vf},
            risk_investigation_time=50,
            hazard_investigation_time=50,
            ses_per_logic_tree_path=200,
            number_of_logic_tree_samples=0,
            loss_curve_resolution=4,
            conditional_loss_poes=[0.1, 0.5, 0.9],
            insured_losses=False
            )
        out = wf(self.loss_type, assets, gmvs, epsilons, [1, 2, 3, 4, 5])
        self.assert_similar(
            out.event_loss_table,
            {1: 15.332714802464356,
             2: 16.21582466071975,
             3: 15.646630129345354,
             4: 15.285164778325353,
             5: 15.860930792931873,
             })

    def test_mean_based_with_perfect_correlation(self):
        # This is a regression test. Data has not been checked
        vf = (
            scientific.VulnerabilityFunction(
                'SOME-TAXONOMY', 'PGA',
                [0.001, 0.2, 0.3, 0.5, 0.7],
                [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.01, 0.02, 0.02, 0.01, 0.03]))

        gmvs = [[10., 20., 30., 40., 50.],
                [1., 2., 3., 4., 5.]]

        epsilons = scientific.make_epsilons(gmvs, seed=1, correlation=1)
        loss_matrix = vf.apply_to(gmvs, epsilons)
        losses_poes = scientific.event_based(loss_matrix[0], 120, 30, 4)

        first_curve_integral = scientific.average_loss(losses_poes)

        self.assertAlmostEqual(0.483041416, first_curve_integral)

        wf = workflows.ProbabilisticEventBased(
            'PGA', 'SOME-TAXONOMY',
            vulnerability_functions={self.loss_type: vf},
            risk_investigation_time=50,
            hazard_investigation_time=50,
            ses_per_logic_tree_path=200,
            number_of_logic_tree_samples=0,
            loss_curve_resolution=4,
            conditional_loss_poes=[0.1, 0.5, 0.9],
            insured_losses=False
            )
        out = wf(self.loss_type, assets, gmvs, epsilons, [1, 2, 3, 4, 5])
        self.assert_similar(
            out.event_loss_table,
            {1: 15.232320555463319,
             2: 16.248173683693864,
             3: 15.583030510462981,
             4: 15.177382760499968,
             5: 15.840499250058254,
             })

    def test_mean_based(self):
        epsilons = scientific.make_epsilons([gmf[0]], seed=1, correlation=0)
        vulnerability_function_rm = (
            scientific.VulnerabilityFunction(
                'RM', 'PGA',
                [0.001, 0.2, 0.3, 0.5, 0.7],
                [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.0, 0.0, 0.0, 0.0, 0.0]))

        vulnerability_function_rc = (
            scientific.VulnerabilityFunction(
                'RC', 'PGA',
                [0.001, 0.2, 0.3, 0.5, 0.7],
                [0.0035, 0.07, 0.14, 0.28, 0.56],
                [0.0, 0.0, 0.0, 0.0, 0.0]))

        cr = 50  # curve resolution
        curve_rm_1 = scientific.event_based(
            vulnerability_function_rm.apply_to(
                [gmf[0]], epsilons)[0], 50, 50, cr)

        curve_rm_2 = scientific.event_based(
            vulnerability_function_rm.apply_to(
                [gmf[1]], epsilons)[0], 50, 50, cr)

        curve_rc = scientific.event_based(
            vulnerability_function_rc.apply_to(
                [gmf[2]], epsilons)[0], 50, 50, cr)

        for i, curve_rm in enumerate([curve_rm_1, curve_rm_2]):

            conditional_loss = scientific.conditional_loss_ratio(
                curve_rm[0], curve_rm[1], 0.8)
            self.assertAlmostEqual([0.0490311, 0.0428061][i], conditional_loss)

            self.assertAlmostEqual(
                [0.070219108, 0.04549904][i],
                scientific.average_loss(curve_rm))

        conditional_loss = scientific.conditional_loss_ratio(
            curve_rc[0], curve_rc[1], 0.8)
        self.assertAlmostEqual(0.0152273, conditional_loss)

        self.assertAlmostEqual(
            0.0152393, scientific.average_loss(curve_rc))

    def test_insured_loss_mean_based(self):
        vf = scientific.VulnerabilityFunction(
            'VF', 'PGA',
            [0.001, 0.2, 0.3, 0.5, 0.7],
            [0.01, 0.1, 0.2, 0.4, 0.8],
            [0.0, 0.0, 0.0, 0.0, 0.0])

        epsilons = scientific.make_epsilons(gmf[0:2], seed=1, correlation=0)
        loss_ratios = vf.apply_to(gmf[0:2], epsilons)

        values = [3000, 1000]
        insured_limits = [1250., 40.]
        deductibles = [40, 13]

        insured_average_losses = [
            scientific.average_loss(scientific.event_based(
                scientific.insured_losses(
                    lrs,
                    deductibles[i] / values[i], insured_limits[i] / values[i]),
                50, 50, 20))
            for i, lrs in enumerate(loss_ratios)]

        numpy.testing.assert_allclose(
            [207.86489132 / 3000,   38.07815797 / 1000],
            insured_average_losses)

        wf = workflows.ProbabilisticEventBased(
            'PGA', 'SOME-TAXONOMY',
            vulnerability_functions={self.loss_type: vf},
            risk_investigation_time=50,
            hazard_investigation_time=50,
            ses_per_logic_tree_path=200,
            number_of_logic_tree_samples=0,
            loss_curve_resolution=4,
            conditional_loss_poes=[0.1, 0.5, 0.9],
            insured_losses=True
            )
        out = wf(self.loss_type, assets, gmf[0:2], epsilons, [1, 2, 3, 4, 5])
        self.assert_similar(
            out.event_loss_table,
            {1: 0.20314761658291458,
             2: 0,
             3: 0,
             4: 0,
             5: 0,
             })
