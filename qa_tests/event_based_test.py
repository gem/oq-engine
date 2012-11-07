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

import os, collections
import unittest
import numpy

from risklib import api
from risklib.models import input
from risklib import vulnerability_function
from risklib import event_based
from risklib.tests.utils import vectors_from_csv

THISDIR = os.path.dirname(__file__)

gmf = vectors_from_csv('gmf', THISDIR)
gmf_bd = vectors_from_csv('gmf_bd', THISDIR)
gmf_il = vectors_from_csv('gmf_il', THISDIR)

Triplet = collections.namedtuple('Triplet', 'a1 a2 a3')

TestData = collections.namedtuple(
    'TestData', 'input_asset expected_poes expected_losses_lrc '
    'expected_loss_map')

mb = TestData( # mean based test data

    input_asset = Triplet(
        a1=input.Asset("a1", "RM", 3000, None),
        a2=input.Asset("a2", "RC", 2000, None),
        a3=input.Asset("a3", "RM", 1000, None),
        ),
    
    expected_poes = Triplet(
        a1=[1.0000000000, 1.0000000000, 0.9975213575,
            0.9502134626, 0.8646777340, 0.8646647795,
            0.6321490651, 0.6321506245, 0.6321525149],
        a2=[1.0000000000, 1.0000000000, 0.9999999586,
            0.9996645695, 0.9975213681, 0.9816858268,
            0.8646666370, 0.8646704246, 0.6321542453],
        a3=[1.0000000000, 1.0000000000, 1.0000000000,
            1.0000000000, 1.0000000000, 0.9999998875,
            0.9999977397, 0.9998765914, 0.9816858693]
        ),
    
    expected_losses_lrc = Triplet(
        a1=numpy.array([
                0.004893071586, 0.014679214757,
                0.024465357929, 0.034251501100,
                0.044037644271, 0.053823787443,
                0.063609930614, 0.073396073786,
                0.083182216957]),
        a2=numpy.array([
                0.0018204915, 0.0054614744, 0.0091024573,
                0.0127434402, 0.0163844231, 0.0200254060,
                0.0236663889, 0.0273073718, 0.0309483547]),
        a3=numpy.array([
                0.0014593438, 0.0043780315, 0.0072967191,
                0.0102154068, 0.0131340944, 0.0160527820,
                0.0189714697, 0.0218901573, 0.0248088450]),
        ),
        
    expected_loss_map = Triplet( 
        a1=78.1154725900,
        a2=36.2507008221,
        a3=23.4782545574,
        ),
    )

sb = TestData( # sample based test data

    input_asset = mb.input_asset,
    
    expected_poes = Triplet(
        a1=[1.0, 0.601480958915, 0.147856211034,
            0.130641764601, 0.113079563283, 0.0768836536134,
            0.0768836536134, 0.0198013266932, 0.0198013266932],
        a2=[1.0, 0.831361852731, 0.302323673929,
            0.130641764601, 0.0768836536134, 0.0768836536134,
            0.0582354664158, 0.0582354664158, 0.0392105608477],
        a3=[1.0, 0.999088118034, 0.472707575957,
            0.197481202038, 0.095162581964, 0.0392105608477,
            0.0198013266932, 0.0198013266932, 0.0198013266932],
        ),
    
    expected_losses_lrc = Triplet(
        a1=numpy.array([
                0.0234332852886, 0.0702998558659,
                0.117166426443, 0.16403299702,
                0.210899567598, 0.257766138175,
                0.304632708752, 0.351499279329,
                0.398365849907]),
        a2=numpy.array([
                0.0112780780331, 0.0338342340993,
                0.0563903901655, 0.0789465462317,
                0.101502702298, 0.124058858364,
                0.14661501443, 0.169171170497,
                0.191727326563]),
        a3=numpy.array([
                0.00981339568577, 0.0294401870573,
                0.0490669784288, 0.0686937698004,
                0.0883205611719, 0.107947352543,
                0.127574143915, 0.147200935287,
                0.166827726658]),
        ),
        
    expected_loss_map = Triplet( 
        a1=73.8279109206,
        a2=25.2312514028,
        a3=29.7790495007,
        ),
    )

il = TestData( # insured loss test data

    input_asset = Triplet(
        a1 = input.Asset("a1", "RM", 3000, None, ins_limit=125, deductible=40),
        a2 = input.Asset("a2", "RC", 2000, None, ins_limit=50, deductible=15),
        a3 = input.Asset("a3", "RM", 1000, None, ins_limit=24, deductible=13),
        ),
    
    expected_poes = Triplet(
        a1=[0.999999999241817, 0.999999999241756,
            0.999999999241818, 0.999999994397740,
            0.999664553654242, 0.981685826817424,
            0.950213638037609, 0.864670424561284,
            0.864677109328630],
        a2=[0.999999887469239, 0.999999887472202,
            0.999999887466752, 0.999997739830177,
            0.999664538439969, 0.997521316464728,
            0.981684445676922, 0.950213415220451,
            0.864675860594400],
        a3=[0.999999999994891, 0.999999999994891,
            0.999999999994891, 0.999999999994891,
            0.999999999994891, 0.999999999986112,
            0.999997739824223, 0.999876598280200,
            0.999088132862596],
        ),
    
    expected_losses_lrc = Triplet(
        a1=numpy.array([
                0.00231481481481481, 0.00694444444444445,
                0.0115740740740741, 0.0162037037037037,
                0.0208333333333333, 0.0254629629629630,
                0.0300925925925926, 0.0347222222222222,
                0.0393518518518519]),
        a2=numpy.array([
                0.00138888888888889, 0.00416666666666667,
                0.00694444444444445, 0.00972222222222222,
                0.0125000000000000, 0.0152777777777778,
                0.0180555555555556, 0.0208333333333333,
                0.0236111111111111]),
        a3=numpy.array([
                0.00133333333333333, 0.00400000000000000,
                0.00666666666666667, 0.00933333333333333,
                0.0120000000000000, 0.0146666666666667,
                0.0173333333333333, 0.0200000000000000,
                0.0226666666666667]),
        ),

    expected_loss_map = None
    )

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

        peb_conditional_losses = api.conditional_losses([0.99], peb_calculator)

        for i in range(3):
            asset_output = peb_conditional_losses(
                mb.input_asset[i], {"IMLs": gmf[i], "TSES": 50, "TimeSpan": 50})
            self.check(asset_output, mb, i)

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

    def check(self, asset_output, testdata, i):
        self.assertAlmostEqual(
            testdata.expected_loss_map[i],
            asset_output.conditional_losses[0.99],
            delta=0.05 * testdata.expected_loss_map[i])

        self.assert_allclose(
            testdata.expected_poes[i],
            asset_output.loss_ratio_curve.y_values)
        
        self.assert_allclose(
            testdata.expected_losses_lrc[i], 
            asset_output.loss_ratio_curve.x_values)

        self.assert_allclose(
            testdata.expected_poes[i],
            asset_output.loss_curve.y_values)

        expected_losses_lc = (testdata.expected_losses_lrc[i] * 
                              asset_output.asset.value)
        self.assert_allclose(
            expected_losses_lc, asset_output.loss_curve.x_values)

    def test_sample_based_beta(self):
        vulnerability_function_rm = (
            vulnerability_function.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.0001, 0.0001, 0.0001, 0.0001, 0.0001], "BT"))

        vulnerability_function_rc = (
            vulnerability_function.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.0035, 0.07, 0.14, 0.28, 0.56],
                [0.0001, 0.0001, 0.0001, 0.0001, 0.0001], "BT"))

        vulnerability_model = {"RM": vulnerability_function_rm,
                               "RC": vulnerability_function_rc}

        peb_calculator = api.probabilistic_event_based(
            vulnerability_model, 10, None, None)
        peb_conditional_losses = api.conditional_losses([0.99], peb_calculator)

        for i in range(3):
            asset_output = peb_conditional_losses(
                sb.input_asset[i],
                {"IMLs": gmf_bd[i], "TSES": 2500, "TimeSpan": 50})
            self.check(asset_output, sb, i)

        aggregate_curve = event_based.aggregate_loss_curve(
            [peb_calculator.aggregate_losses], 2500, 50, 10)

        expected_aggregate_poes = [1.0, 0.732864698034, 0.228948414196,
                                    0.147856211034, 0.0768836536134,
                                    0.0768836536134, 0.0198013266932,
                                    0.0198013266932, 0.0198013266932]

        expected_aggregate_losses = [
            102.669407618, 308.008222854, 513.347038089,
            718.685853325, 924.024668561, 1129.3634838,
            1334.70229903, 1540.04111427, 1745.3799295]

        self.assert_allclose(
            expected_aggregate_poes, aggregate_curve.y_values)

        self.assert_allclose(
            expected_aggregate_losses, aggregate_curve.x_values)

    def test_insured_loss_mean_based(self):
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
        peb_conditional_losses = api.conditional_losses([0.99], peb_calculator)
        peb_insured_losses = api.insured_losses(peb_conditional_losses)
        peb_insured_curves = api.insured_curves(
            vulnerability_model, 10, None, None, peb_insured_losses)

        for i in range(3):
            asset_output = peb_insured_curves(
                il.input_asset[i],
                {"IMLs": gmf_il[i], "TSES": 50, "TimeSpan": 50})
            self.check_il(asset_output, i)

    def check_il(self, asset_output, i):
        self.assert_allclose(
            il.expected_poes[i], asset_output.insured_loss_ratio_curve.y_values)

        self.assert_allclose(
            il.expected_losses_lrc[i],
            asset_output.insured_loss_ratio_curve.x_values)

        self.assert_allclose(
            il.expected_poes[i], asset_output.insured_loss_curve.y_values)

        expected_losses_lc = (
            il.expected_losses_lrc[i] * asset_output.asset.value)
        self.assert_allclose(
            expected_losses_lc, asset_output.insured_loss_curve.x_values)
