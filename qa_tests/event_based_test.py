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
import numpy

from risklib import api
from risklib.models import input
from risklib import vulnerability_function
from risklib import event_based

from qa_tests.event_based_test_data import (GROUND_MOTION_VALUES_A1,
    GROUND_MOTION_VALUES_A2, GROUND_MOTION_VALUES_A3)


class EventBasedTestCase(unittest.TestCase):

    def assert_allclose(self, expected, actual):
        return numpy.testing.assert_allclose(
            expected, actual, atol=0.0, rtol=0.05)

    def test_mean_based(self):
        vulnerability_function_rm = (
                vulnerability_function.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        vulnerability_function_rc = (
            vulnerability_function.VulnerabilityFunction(
            [0.001, 0.2, 0.3, 0.5, 0.7], [0.0035, 0.07, 0.14, 0.28, 0.56],
            [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        vulnerability_model = {"RM": vulnerability_function_rm,
                               "RC": vulnerability_function_rc}

        peb_calculator = api.probabilistic_event_based(
            vulnerability_model, 10, None, None)
        calculator = api.conditional_losses([0.99], peb_calculator)

        asset_output = calculator(input.Asset("a1", "RM", 3000, None),
            {"IMLs": GROUND_MOTION_VALUES_A1, "TSES": 50, "TimeSpan": 50})

        expected_output = 78.1154725900
        self.assertAlmostEqual(expected_output,
            asset_output.conditional_losses[0.99],
            delta=0.05 * expected_output)

        expected_poes_a1 = [1.0000000000, 1.0000000000, 0.9975213575,
                            0.9502134626, 0.8646777340, 0.8646647795,
                            0.6321490651, 0.6321506245, 0.6321525149]

        # Loss ratio curve
        expected_losses_a1_lrc = [0.004893071586, 0.014679214757,
                                    0.024465357929, 0.034251501100,
                                    0.044037644271, 0.053823787443,
                                    0.063609930614, 0.073396073786,
                                    0.083182216957]

        # Loss curve
        expected_losses_a1_lc = [14.6792147571, 44.0376442714, 73.3960737856,
                                102.7545032998, 132.1129328141, 161.4713623283,
                                190.8297918425, 220.1882213568, 249.5466508710]

        self.assert_allclose(
            expected_poes_a1, asset_output.loss_ratio_curve.y_values)

        self.assert_allclose(
            expected_losses_a1_lrc, asset_output.loss_ratio_curve.x_values)

        self.assert_allclose(
            expected_poes_a1, asset_output.loss_curve.y_values)

        self.assert_allclose(
            expected_losses_a1_lc, asset_output.loss_curve.x_values)

        asset_output = calculator(input.Asset("a2", "RC", 2000, None),
            {"IMLs": GROUND_MOTION_VALUES_A2, "TSES": 50, "TimeSpan": 50})

        expected_output = 36.2507008221
        self.assertAlmostEqual(expected_output,
            asset_output.conditional_losses[0.99],
            delta=0.05 * expected_output)

        expected_poes_a2 = [1.0000000000, 1.0000000000, 0.9999999586,
                            0.9996645695, 0.9975213681, 0.9816858268,
                            0.8646666370, 0.8646704246, 0.6321542453]

        expected_losses_a2_lrc = [0.0018204915, 0.0054614744, 0.0091024573,
                                    0.0127434402, 0.0163844231, 0.0200254060,
                                    0.0236663889, 0.0273073718, 0.0309483547]


        expected_losses_a2_lc = [3.6409829079, 10.9229487236, 18.2049145394,
                                 25.4868803551, 32.7688461709, 40.0508119866,
                                 47.3327778023, 54.6147436181, 61.8967094338]

        self.assert_allclose(
            expected_poes_a2, asset_output.loss_ratio_curve.y_values)

        self.assert_allclose(
            expected_losses_a2_lrc, asset_output.loss_ratio_curve.x_values)

        self.assert_allclose(
            expected_poes_a2, asset_output.loss_curve.y_values)

        self.assert_allclose(
            expected_losses_a2_lc, asset_output.loss_curve.x_values)

        asset_output = calculator(input.Asset("a3", "RM", 1000, None),
            {"IMLs": GROUND_MOTION_VALUES_A3, "TSES": 50, "TimeSpan": 50})

        expected_output = 23.4782545574
        self.assertAlmostEqual(expected_output,
            asset_output.conditional_losses[0.99],
            delta=0.05 * expected_output)

        expected_poes_a3 = [1.0000000000, 1.0000000000, 1.0000000000,
                            1.0000000000, 1.0000000000, 0.9999998875,
                            0.9999977397, 0.9998765914, 0.9816858693]

        expected_losses_a3_lrc = [0.0014593438, 0.0043780315, 0.0072967191,
                                0.0102154068, 0.0131340944, 0.0160527820,
                                0.0189714697, 0.0218901573, 0.0248088450]

        expected_losses_a3_lc = [1.4593438219, 4.3780314657, 7.2967191094,
                                10.2154067532, 13.1340943970, 16.0527820408,
                                18.9714696845, 21.8901573283, 24.8088449721]

        self.assert_allclose(
            expected_poes_a3, asset_output.loss_ratio_curve.y_values)

        self.assert_allclose(
            expected_losses_a3_lrc, asset_output.loss_ratio_curve.x_values)

        self.assert_allclose(
            expected_poes_a3, asset_output.loss_curve.y_values)

        self.assert_allclose(
            expected_losses_a3_lc, asset_output.loss_curve.x_values)

        expected_aggregate_poes = [
            1.0000000000, 1.0000000000, 0.9999991685,
            0.9932621249, 0.9502177204, 0.8646647795,
            0.8646752036, 0.6321506245, 0.6321525149]

        expected_aggregate_losses = [
            18.5629274028, 55.6887822085, 92.8146370142,
            129.9404918199, 167.0663466256, 204.1922014313,
            241.3180562370, 278.4439110427, 315.5697658484]

        aggregate_curve = event_based.aggregate_loss_curve(
           [peb_calculator.aggregate_losses], 50, 50, 10)

        self.assert_allclose(
            expected_aggregate_poes, aggregate_curve.y_values)

        self.assert_allclose(
            expected_aggregate_losses, aggregate_curve.x_values)










