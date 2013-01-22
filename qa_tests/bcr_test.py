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

import unittest

from risklib import api
from risklib import scientific


class BCRTestCase(unittest.TestCase):

    def test_bcr_classical(self):
        vulnerability_function_rm = (
            scientific.VulnerabilityFunction(
            [0.1, 0.2, 0.3, 0.45, 0.6], [0.05, 0.1, 0.2, 0.4, 0.8],
            [0.5, 0.4, 0.3, 0.2, 0.1], "LN"))

        vulnerability_function_rf = (
            scientific.VulnerabilityFunction(
            [0.1, 0.2, 0.3, 0.45, 0.6], [0.035, 0.07, 0.14, 0.28, 0.56],
            [0.5, 0.4, 0.3, 0.2, 0.1], "LN"))

        asset = scientific.Asset("a1", 2, None, retrofitting_cost=0.1)

        calculator_rm = api.Classical(vulnerability_function_rm, steps=5)
        calculator_rf = api.Classical(vulnerability_function_rf, steps=5)

        calculator_bcr = api.BCR(calculator_rm, calculator_rf,
            interest_rate=0.05, asset_life_expectancy=40)

        hazard = [
            (0.001, 0.0398612669790014), (0.01, 0.0398612669790014),
            (0.05, 0.0397287574802989), (0.1, 0.0296134266256125),
            (0.15, 0.0198273287564916), (0.2, 0.0130622701614519),
            (0.25, 0.00865538795000043), (0.3, 0.00589852059368967),
            (0.35, 0.00406169858951178), (0.4, 0.00281172717952682),
            (0.45, 0.00199511741777669), (0.5, 0.00135870597284571),
            (0.55, 0.000989667841573727), (0.6, 0.000757544444296432),
            (0.7, 0.000272824002045979), (0.8, 0.0),
            (0.9, 0.0), (1.0, 0.0)]

        asset_output = calculator_bcr(asset, hazard)

        self.assertAlmostEqual(0.009379,
            asset_output.eal_original, delta=0.0009)

        self.assertAlmostEqual(0.006586,
            asset_output.eal_retrofitted, delta=0.0009)

        self.assertAlmostEqual(0.483091,
            asset_output.bcr, delta=0.009)
