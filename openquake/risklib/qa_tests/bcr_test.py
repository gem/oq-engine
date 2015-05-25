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

import unittest

from openquake.risklib import scientific


class BCRTestCase(unittest.TestCase):

    def test_bcr_classical(self):
        vulnerability_function_rm = (
            scientific.VulnerabilityFunction(
                'RM', 'PGA',
                [0.1, 0.2, 0.3, 0.45, 0.6],
                [0.05, 0.1, 0.2, 0.4, 0.8],
                [0.5, 0.4, 0.3, 0.2, 0.1], "LN"))

        vulnerability_function_rf = (
            scientific.VulnerabilityFunction(
                'RF', 'PGA',
                [0.1, 0.2, 0.3, 0.45, 0.6],
                [0.035, 0.07, 0.14, 0.28, 0.56],
                [0.5, 0.4, 0.3, 0.2, 0.1], "LN"))

        asset_value = 2.
        retrofitting_cost = .1
        interest_rate = 0.05
        asset_life_expectancy = 40

        hazard_imls = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4,
                       0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9, 1.0]
        poes = [0.039861266979, 0.039861266979, 0.0397287574803,
                0.0296134266256, 0.0198273287565, 0.0130622701615,
                0.00865538795, 0.00589852059369, 0.00406169858951,
                0.00281172717953, 0.00199511741778, 0.00135870597285,
                0.000989667841574, 0.000757544444296, 0.000272824002046,
                0.0, 0.0, 0.]

        original_loss_ratio_curve = scientific.classical(
            vulnerability_function_rm, hazard_imls, poes, steps=5)
        retrofitted_loss_ratio_curve = scientific.classical(
            vulnerability_function_rf, hazard_imls, poes, steps=5)

        eal_original = scientific.average_loss(original_loss_ratio_curve)
        eal_retrofitted = scientific.average_loss(retrofitted_loss_ratio_curve)

        bcr = scientific.bcr(
            eal_original, eal_retrofitted,
            interest_rate,
            asset_life_expectancy,
            asset_value,
            retrofitting_cost)

        self.assertAlmostEqual(0.009379,
                               eal_original * asset_value,
                               delta=0.0009)

        self.assertAlmostEqual(0.006586,
                               eal_retrofitted * asset_value,
                               delta=0.0009)

        self.assertAlmostEqual(0.483091, bcr, delta=0.009)
