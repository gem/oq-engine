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
import numpy

from openquake.risklib import scientific


class ClassicalTestCase(unittest.TestCase):

    hazard_imls = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4,
                   0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9, 1.0]
    hazard_curve = [
        0.039861266979, 0.039861266979, 0.0397287574803,
        0.0296134266256, 0.0198273287565, 0.0130622701615,
        0.00865538795, 0.00589852059369, 0.00406169858951,
        0.00281172717953, 0.00199511741778, 0.00135870597285,
        0.000989667841574, 0.000757544444296, 0.000272824002046,
        0.0, 0.0, 0.]

    loss_ratios = [
        0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06,
        0.07, 0.08, 0.09, 0.10, 0.12, 0.14, 0.16,
        0.18, 0.20, 0.24, 0.28, 0.32, 0.36, 0.40,
        0.48, 0.56, 0.64, 0.72, 0.80, 0.84, 0.88,
        0.92, 0.96, 1.00]

    def test_lognormal_distribution(self):
        loss_ratio_curve = scientific.classical(
            scientific.VulnerabilityFunction(
                'VF', 'PGA',
                [0.1, 0.2, 0.3, 0.45, 0.6],
                [0.05, 0.1, 0.2, 0.4, 0.8],
                [0.5, 0.4, 0.3, 0.2, 0.1]),
            self.hazard_imls, self.hazard_curve, steps=5)

        poes = [
            0.039334753367700, 0.039319630829000,
            0.038454063967300, 0.035355568337500,
            0.031080935951500, 0.026921966116900,
            0.023309185424900, 0.020254928647300,
            0.017692604455300, 0.015561622176500,
            0.013804482989300, 0.011159985044500,
            0.009272778209290, 0.007803862103290,
            0.006601047489540, 0.005621048101030,
            0.004262944952210, 0.003478101875460,
            0.002916428961850, 0.002375461660340,
            0.001854772287220, 0.001133190711620,
            0.000862358303705, 0.000784269030443,
            0.000660062215754, 0.000374938542785,
            0.000230249004393, 0.000122823654476,
            5.72790058705e-05, 2.35807221322e-05,
            8.66392324535e-06]

        numpy.testing.assert_allclose(self.loss_ratios, loss_ratio_curve[0])
        numpy.testing.assert_allclose(poes, loss_ratio_curve[1])

        asset_value = 2.

        conditional_losses = dict([
            (poe, scientific.conditional_loss_ratio(
                self.loss_ratios, poes, poe) * asset_value)
            for poe in [0.01, 0.02, 0.05]])

        self.assertAlmostEqual(0.264586283238, conditional_losses[0.01])
        self.assertAlmostEqual(0.141989823521, conditional_losses[0.02])
        self.assertAlmostEqual(0.0, conditional_losses[0.05])

    def test_beta_distribution(self):
        loss_ratio_curve = scientific.classical(
            scientific.VulnerabilityFunction(
                'VF', 'PGA',
                [0.1, 0.2, 0.3, 0.45, 0.6],
                [0.05, 0.1, 0.2, 0.4, 0.8],
                [0.5, 0.4, 0.3, 0.2, 0.1],
                "BT"),
            self.hazard_imls, self.hazard_curve, steps=5)

        poes = [
            0.039334753367700, 0.039125428171600,
            0.037674168943300, 0.034759710983600,
            0.031030531006800, 0.027179528786300,
            0.023629919279000, 0.020549508446100,
            0.017953286405900, 0.015789769371500,
            0.013989999469800, 0.011228361585000,
            0.009252778235140, 0.007776981119440,
            0.006618721902640, 0.005678492205870,
            0.004293209819490, 0.003423791350520,
            0.002851589502850, 0.002371116350380,
            0.001901538687150, 0.001145930527350,
            0.000834074579570, 0.000755265952955,
            0.000655382394929, 0.000422046545856,
            0.000266286103069, 0.000124036890130,
            3.28497166702e-05, 2.178664466e-06, 0.0]

        numpy.testing.assert_allclose(self.loss_ratios, loss_ratio_curve[0])
        numpy.testing.assert_allclose(poes, loss_ratio_curve[1])

        asset_value = 2.
        self.assertAlmostEqual(
            0.264870863283,
            scientific.conditional_loss_ratio(
                self.loss_ratios, poes, 0.01) * asset_value)
