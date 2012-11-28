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
    'TestData', 'input_asset expected_poes expected_losses '
    'expected_loss_map')

mean_based_loss_curve_poes = [
    1.0, 1.0, 0.992492256, 0.9849845130, 0.9774767690, 0.9699690250,
    0.962461282, 0.954953538, 0.947445794, 0.939938051, 0.932430307,
    0.924922563, 0.917414819, 0.909907076, 0.902399332, 0.894891588,
    0.887383845, 0.879876101, 0.872368357, 0.864860614, 0.857352870,
    0.849845126, 0.842337382, 0.834829639, 0.827321895, 0.819814151,
    0.812306408, 0.804798664, 0.79729092, 0.789783177, 0.7822754330,
    0.774767689, 0.767259945, 0.759752202, 0.752244458, 0.744736714,
    0.737228971, 0.729721227, 0.722213483, 0.71470574, 0.7071979960,
    0.699690252, 0.692182508, 0.684674765, 0.677167021, 0.669659277,
    0.662151534, 0.65464379, 0.647136046, 0.639628303, 0.6321205590]

mb = TestData( # mean based test data

    input_asset = Triplet(
        a1=input.Asset("a1", "RM", 3000, None),
        a2=input.Asset("a2", "RC", 2000, None),
        a3=input.Asset("a3", "RM", 1000, None),
        ),
    
    expected_poes = Triplet(
        a1=mean_based_loss_curve_poes,
        a2=mean_based_loss_curve_poes,
        a3=mean_based_loss_curve_poes,
        ),
    
    expected_losses = Triplet(
        a1=numpy.array([0.0, 34.65, 64.759, 68.2291, 72.2353, 76.662, 81.0887,
                        85.5154, 90.2826, 95.6332, 100.9838, 106.3344000,
                        111.685, 117.0356, 122.3862, 127.7369, 133.08750,
                        138.4381, 143.7887, 149.1393, 152.8932, 156.6043,
                        160.3153, 164.0264, 167.7375, 171.4486, 175.1597,
                        178.8708, 182.5819, 186.293, 190.0041, 193.71520,
                        197.4262, 201.1373, 204.8484, 208.5595, 212.2706,
                        215.9817, 219.6928, 223.4039, 227.115, 230.82610,
                        234.5371, 238.2482, 241.9593, 245.6704, 249.3815,
                        253.0926, 256.8037, 260.5148, 264.2259]),
        a2=numpy.array([0.0, 8.82073591, 25.03645701, 27.06330664,
                        28.23351762, 28.73183898, 29.23016035, 29.728481720,
                        30.06743270, 30.13335343, 30.19927416, 30.265194890,
                        30.33111562, 30.39703636, 30.46295709, 30.528877820,
                        30.59479855, 30.66071928, 30.72664001, 30.792560740,
                        30.80203104, 30.80998894, 30.81794683, 30.825904730,
                        30.83386262, 30.84182052, 30.849778410, 30.85773630,
                        30.8656942, 30.87365209, 30.88160999, 30.8895678800,
                        30.89752578, 30.90548367, 30.91344157, 30.921399460,
                        30.92935736, 30.93731525, 30.94527315, 30.953231040,
                        30.96118894, 30.96914683, 30.97710473, 30.985062620,
                        30.99302052, 31.00097841, 31.00893631, 31.016894200,
                        31.024852090, 31.03280999, 31.04076788]),
        a3=numpy.array([0.0, 11.52942291, 26.0726, 29.8488, 31.9478, 32.7313,
                        33.5148, 34.2983, 35.0629, 35.7951, 36.52730,
                        37.2595, 37.9917, 38.7239, 39.456, 40.188200,
                        40.9204, 41.6526, 42.38480, 43.117, 43.33970,
                        43.5488, 43.7578, 43.9669, 44.17600, 44.3851,
                        44.5941, 44.8032, 45.0123, 45.2214, 45.43040,
                        45.6395, 45.8486, 46.0577, 46.2668, 46.47580,
                        46.6849, 46.894, 47.1031, 47.3121, 47.521200,
                        47.7303, 47.93940, 48.1484, 48.3575, 48.5666,
                        48.7757, 48.9847, 49.1938, 49.4029, 49.61200]),
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
    
    expected_losses = Triplet(
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
    
    expected_losses = Triplet(
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

        self.assert_allclose(testdata.expected_poes[i],
            asset_output.loss_ratio_curve.y_values)

        self.assert_allclose(
            testdata.expected_losses[i] / asset_output.asset.value,
            asset_output.loss_ratio_curve.x_values)

        self.assert_allclose(testdata.expected_poes[i],
            asset_output.loss_curve.y_values)

        self.assert_allclose(testdata.expected_losses[i],
            asset_output.loss_curve.x_values)

    @unittest.skip
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

    @unittest.skip
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
