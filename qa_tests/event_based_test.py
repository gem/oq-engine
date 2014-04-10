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

from openquake.risklib import scientific
from openquake.risklib.tests.utils import vectors_from_csv

THISDIR = os.path.dirname(__file__)

gmf = vectors_from_csv('gmf', THISDIR)


class EventBasedTestCase(unittest.TestCase):

    def test_mean_based_with_no_correlation(self):
        # This is a regression test. Data has not been checked
        vf = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.01, 0.02, 0.02, 0.01, 0.03], "LN"))
        gmvs = numpy.array([[10., 20., 30., 40., 50.],
                            [1., 2., 3., 4., 5.]])

        loss_matrix = vf.call_many(gmvs, seed=1, asset_correlation=0)
        losses, poes = scientific.event_based(
            loss_matrix[0], 120, 30, curve_resolution=4)

        first_curve_integral = scientific.average_loss(losses, poes)

        self.assertAlmostEqual(0.500993631, first_curve_integral)

    def test_mean_based_with_partial_correlation(self):
        # This is a regression test. Data has not been checked
        vf = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.01, 0.02, 0.02, 0.01, 0.03], "LN"))
        gmvs = numpy.array([[10., 20., 30., 40., 50.],
                           [1., 2., 3., 4., 5.]])
        loss_matrix = vf.call_many(gmvs, seed=1, asset_correlation=0.5)

        losses, poes = scientific.event_based(loss_matrix[0], 120, 30, 4)
        first_curve_integral = scientific.average_loss(losses, poes)

        self.assertAlmostEqual(0.48983614471, first_curve_integral)

    def test_mean_based_with_perfect_correlation(self):
        # This is a regression test. Data has not been checked
        vf = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.01, 0.02, 0.02, 0.01, 0.03], "LN"))

        gmvs = [[10., 20., 30., 40., 50.],
                [1., 2., 3., 4., 5.]]

        loss_matrix = vf.call_many(gmvs, seed=1, asset_correlation=1)
        losses, poes = scientific.event_based(loss_matrix[0], 120, 30, 4)

        first_curve_integral = scientific.average_loss(losses, poes)

        self.assertAlmostEqual(0.483041416, first_curve_integral)

    def test_mean_based(self):
        vulnerability_function_rm = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        vulnerability_function_rc = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.0035, 0.07, 0.14, 0.28, 0.56],
                [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        curve_rm_1 = scientific.event_based(
            vulnerability_function_rm.call_many([gmf[0]])[0], 50, 50)

        curve_rm_2 = scientific.event_based(
            vulnerability_function_rm.call_many([gmf[1]])[0], 50, 50)

        curve_rc = scientific.event_based(
            vulnerability_function_rc.call_many([gmf[2]])[0], 50, 50)

        for i, curve_rm in enumerate([curve_rm_1, curve_rm_2]):

            conditional_loss = scientific.conditional_loss_ratio(
                curve_rm[0], curve_rm[1], 0.8)
            self.assertAlmostEqual([0.0490311, 0.0428061][i], conditional_loss)

            self.assertAlmostEqual(
                [0.070219108, 0.04549904][i],
                scientific.average_loss(curve_rm[0], curve_rm[1]))

        conditional_loss = scientific.conditional_loss_ratio(
            curve_rc[0], curve_rc[1], 0.8)
        self.assertAlmostEqual(0.0152273, conditional_loss)

        self.assertAlmostEqual(
            0.0152393,
            scientific.average_loss(curve_rc[0], curve_rc[1]))

    def test_insured_loss_mean_based(self):
        vf = scientific.VulnerabilityFunction(
            [0.001, 0.2, 0.3, 0.5, 0.7],
            [0.01, 0.1, 0.2, 0.4, 0.8],
            [0.0, 0.0, 0.0, 0.0, 0.0],
            "LN")

        loss_ratios = vf.call_many(gmf[0:2])

        values = [3000, 1000]
        insured_limits = [1250., 40.]
        deductibles = [40, 13]

        insured_average_losses = [
            scientific.average_loss(*scientific.event_based(
                scientific.insured_losses(
                    lrs,
                    deductibles[i] / values[i], insured_limits[i] / values[i]),
                50, 50, 20))
            for i, lrs in enumerate(loss_ratios)]

        numpy.testing.assert_allclose(
            [207.86489132 / 3000,   38.07815797 / 1000],
            insured_average_losses)
