# coding=utf-8
# Copyright (c) 2010-2013, GEM Foundation.
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

import unittest

from openquake.risklib.models.input import FragilityModel
from openquake.risklib import scientific
from openquake.risklib import api

# FIXME(lp). IMHO, in this file we are not testing much...


class ClassicalCalculatorTestCase(unittest.TestCase):
    def test_classical_calculator(self):
        hazard_curve = [(0.1, 0.5), (0.2, 0.6)]

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertEqual(1, len(api.Classical(function)([hazard_curve])))


class ScenarioDamageCalculatorTestCase(unittest.TestCase):

    def test_scenario_damage_calculator(self):
        fragility_model = FragilityModel(
            "discrete", 'PGA', [0.1, 0.2], ["LS1", "LS2"],
            ('RC', [[0.8, 0.7], [0.8, 0.7]], None))

        calculator = api.ScenarioDamage(fragility_model['RC'])

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertEqual(1, len(calculator([[0.11, 0.12, 0.13]])))


class ProbabilisticEventBasedCalculatorTestCase(unittest.TestCase):

    def test_event_based_calculator(self):
        hazard = [0.11, 0.12, 0.13]

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        loss_ratios, loss_ratio_curves = api.ProbabilisticEventBased(
            function, seed=37, correlation=1, tses=1, time_span=50)(
                [hazard])

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertEqual(1, len(loss_ratio_curves))
        self.assertEqual(1, len(loss_ratios))

    def test_event_based_trivial_case(self):
        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        loss_ratios, loss_ratio_curves = api.ProbabilisticEventBased(
            function, tses=20, time_span=30)([])
        self.assertEqual(1, len(loss_ratios))
        self.assertEqual(0, len(loss_ratio_curves))

        self.assertEqual(0, len(loss_ratios[0]))


class ScenarioCalculatorTestCase(unittest.TestCase):

    def test_scenario_risk_calculator(self):
        hazard = [0.11, 0.12, 0.13]

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertEqual(1, len(api.Scenario(function, 37, 1)([hazard])))

    def test_scenario_risk_calculator_trivial_case(self):
        hazard = []

        function = scientific.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        ret = api.Scenario(function, 37, 1)([hazard])
        self.assertEqual(1, len(ret))
        self.assertEqual(0, len(ret[0]))
