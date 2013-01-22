# coding=utf-8
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

import mock
import unittest

from risklib.models import input
from risklib import scientific
from risklib.curve import Curve
from risklib import api


class ComputeOnSitesTestCase(unittest.TestCase):

    def test_multiple_sites(self):
        asset = scientific.Asset("a1", None, None, None)
        sites = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)
        assets_getter = mock.Mock(return_value=[asset])

        list(api.compute_on_sites(
             sites, assets_getter, hazard_getter, calculator))

        expected_calls = [(((1.0, 1.0),), {}), (((2.0, 2.0),), {}),
                          (((3.0, 3.0),), {})]

        self.assertEquals(expected_calls, assets_getter.call_args_list)
        self.assertEquals(expected_calls, hazard_getter.call_args_list)

        self.assertEquals([((asset, 1.0), {})] * 3,
                          calculator.call_args_list)

    def test_multiple_assets_per_site(self):
        sites = [(1.0, 1.0)]

        assets = [
            scientific.Asset("a1", None, None, None),
            scientific.Asset("a2", None, None, None),
            scientific.Asset("a3", None, None, None),
        ]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)
        assets_getter = mock.Mock(return_value=assets)

        list(api.compute_on_sites(
             sites, assets_getter, hazard_getter, calculator))

        expected_calls = [((assets[0], 1.0), {}), ((assets[1], 1.0), {}),
                          ((assets[2], 1.0), {})]

        self.assertEquals(expected_calls, calculator.call_args_list)


class ComputeOnAssetsTestCase(unittest.TestCase):

    def test_compute_on_assets(self):
        assets = [
            scientific.Asset("a1", None, None, (1.0, 1.0)),
            scientific.Asset("a2", None, None, (2.0, 2.0)),
            scientific.Asset("a3", None, None, (3.0, 3.0)),
        ]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)

        list(api.compute_on_assets(assets, hazard_getter, calculator))

        expected_calls = [(((1.0, 1.0),), {}), (((2.0, 2.0),), {}),
                          (((3.0, 3.0),), {})]

        self.assertEquals(expected_calls, hazard_getter.call_args_list)

        expected_calls = [((assets[0], 1.0), {}), ((assets[1], 1.0), {}),
                          ((assets[2], 1.0), {})]

        self.assertEquals(expected_calls, calculator.call_args_list)


class ConditionalLossesTestCase(unittest.TestCase):

    def test_conditional_losses_calculator(self):
        asset = scientific.Asset("a1", None, .5, None)
        loss_ratio_curve = Curve([(2.0, 2.0)])
        loss_curve = Curve([(1.0, 2.0)])  # abscissae rescaled by 0.5

        asset_output = scientific.ClassicalOutput(
            asset, loss_ratio_curve, None)

        loss_curve_calculator = mock.Mock(return_value=asset_output)

        asset_output = api.ConditionalLosses(
            [0.1, 0.2], loss_curve_calculator)(asset, 1.0)

        loss_curve_calculator.assert_called_with(asset, 1.0)

        expected_output = scientific.ClassicalOutput(
            asset, loss_ratio_curve, {0.2: 1.0, 0.1: 1.0})

        # as output we have the output from the given loss curve
        # calculator, plus the conditional losses
        self.assertEquals(expected_output, asset_output)
        self.assertEquals(asset_output.loss_curve, loss_curve)


class ClassicalCalculatorTestCase(unittest.TestCase):

    def test_classical_calculator(self):
        hazard_curve = [(0.1, 0.5), (0.2, 0.6)]
        asset = scientific.Asset("a1", "RC", 1.0, None)

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN", "RC")

        vulnerability_model = {"RC": function}
        asset_output = api.Classical(vulnerability_model)(asset, hazard_curve)

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.loss_curve)
        self.assertIsNotNone(asset_output.loss_ratio_curve)


class ScenarioDamageCalculatorTestCase(unittest.TestCase):

    def test_scenario_damage_calculator(self):
        fragility_model = input.FragilityModel(
            "discrete", [0.1, 0.2], ["LS1", "LS2"])

        fragility_function = input.FragilityFunctionSeq(
            fragility_model, input.FragilityFunctionDiscrete,
            [[0.8, 0.7], [0.8, 0.7]])

        asset = scientific.Asset("a1", "RC", None, None, number_of_units=1.0)

        calculator = api.ScenarioDamage(
            fragility_model, {"RC": fragility_function})

        asset_output = calculator(asset, [0.11, 0.12, 0.13])

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.collapse_map)
        self.assertIsNotNone(asset_output.damage_distribution_asset)


class BCRCalculatorTestCase(unittest.TestCase):

    def test_bcr_calculator(self):
        hazard_curve = [(0.1, 0.5), (0.2, 0.6)]
        asset = scientific.Asset("a1", "RC", 1.0, None, retrofitting_cost=1.0)

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN", "RC")

        vulnerability_model = {"RC": function}
        vulnerability_model_retrofitted = {"RC": function}

        asset_output = (
            api.BCR(api.Classical(vulnerability_model),
                    api.Classical(vulnerability_model_retrofitted), 1.0, 1.0)
            (asset, hazard_curve))

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.bcr)
        self.assertIsNotNone(asset_output.eal_original)
        self.assertIsNotNone(asset_output.eal_retrofitted)


class ProbabilisticEventBasedCalculatorTestCase(unittest.TestCase):

    def test_event_based_calculator(self):
        asset = scientific.Asset("a1", "RC", 1.0, None)
        hazard = [0.11, 0.12, 0.13]

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN", "RC")

        vulnerability_model = {"RC": function}

        asset_output = api.ProbabilisticEventBased(
            vulnerability_model,
            seed=37, correlation_type="perfect", tses=1, time_span=50)(
                asset, hazard)

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.losses)
        self.assertIsNotNone(asset_output.loss_curve)
        self.assertIsNotNone(asset_output.loss_ratio_curve)


class ScenarioRiskCalculatorTestCase(unittest.TestCase):

    def test_scenario_risk_calculator(self):
        hazard = [0.11, 0.12, 0.13]
        asset = scientific.Asset("a1", "RC", 1.0, None,
                            ins_limit=1.0, deductible=1.0)

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN", "RC")

        vulnerability_model = {"RC": function}

        asset_output = api.ScenarioRisk(
            vulnerability_model, 37, "perfect")(asset, hazard)

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.mean)
        self.assertIsNotNone(asset_output.standard_deviation)
