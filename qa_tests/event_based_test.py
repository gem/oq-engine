# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
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
import collections
import unittest
import numpy

from risklib import api
from risklib import scientific
from risklib.tests.utils import vectors_from_csv

#: The conditional loss poes used for testing
CONDITIONAL_LOSS_POES = 0.50

THISDIR = os.path.dirname(__file__)

gmf = vectors_from_csv('gmf', THISDIR)

TestData = collections.namedtuple(
    'TestData', 'input_models_asset expected_poes expected_losses '
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

#: mean based test data
mb = TestData(

    input_models_asset=[
        scientific.Asset(3000), scientific.Asset(1000), scientific.Asset(2000)
    ],

    expected_poes=[0, 0.0204, 0.0408, 0.0612, 0.0816, 0.102, 0.1224, 0.1429,
                   0.1633, 0.1837, 0.2041, 0.2245, 0.2449, 0.2653, 0.2857,
                   0.3061, 0.3265, 0.3469, 0.3673, 0.3878, 0.4082, 0.4286,
                   0.449, 0.4694, 0.4898, 0.5102, 0.5306, 0.551, 0.5714,
                   0.5918, 0.6122, 0.6327, 0.6531, 0.6735, 0.6939, 0.7143,
                   0.7347, 0.7551, 0.7755, 0.7959, 0.8163, 0.8367, 0.8571,
                   0.8776, 0.898, 0.9184, 0.9388, 0.9592, 0.9796, 1][::-1],

    expected_losses=numpy.array([
        [264.2259, 260.5148, 256.8037, 253.0926, 249.3815,
         245.6704, 241.9593, 238.2482, 234.5371, 230.8261,
         227.115, 223.4039, 219.6928, 215.9817, 212.2706,
         208.5595, 204.8484, 201.1373, 197.4262, 193.7152,
         190.0041, 186.293, 182.5819, 178.8708, 175.1597,
         171.4486, 167.7375, 164.0264, 160.3153, 156.6043,
         152.8932, 149.1393, 143.7887, 138.4381, 133.0875,
         127.7369, 122.3862, 117.0356, 111.685, 106.3344,
         100.9838, 95.6332, 90.2826, 85.5154, 81.0887,
         76.662, 72.2353, 68.2291, 64.759, 34.233][::-1],
        [49.612, 49.4029, 49.1938, 48.9847, 48.7757, 48.5666,
         48.3575, 48.1484, 47.9394, 47.7303, 47.5212, 47.3121,
         47.1031, 46.894, 46.6849, 46.4758, 46.2668, 46.0577,
         45.8486, 45.6395, 45.4304, 45.2214, 45.0123, 44.8032,
         44.5941, 44.3851, 44.176, 43.9669, 43.7578, 43.5488,
         43.3397, 43.117, 42.3848, 41.6526, 40.9204, 40.1882,
         39.456, 38.7239, 37.9917, 37.2595, 36.5273, 35.7951,
         35.0629, 34.2983, 33.5148, 32.7313, 31.9478, 29.8488,
         26.0726, 11.3905][::-1],
        [31.04076788, 31.03280999, 31.02485209, 31.0168942,
         31.00893631, 31.00097841, 30.99302052, 30.98506262,
         30.97710473, 30.96914683, 30.96118894, 30.95323104,
         30.94527315, 30.93731525, 30.92935736, 30.92139946,
         30.91344157, 30.90548367, 30.89752578, 30.88956788,
         30.88160999, 30.87365209, 30.8656942, 30.8577363,
         30.84977841, 30.84182052, 30.83386262, 30.82590473,
         30.81794683, 30.80998894, 30.80203104, 30.79256074,
         30.72664001, 30.66071928, 30.59479855, 30.52887782,
         30.46295709, 30.39703636, 30.33111562, 30.26519489,
         30.19927416, 30.13335343, 30.0674327, 29.72848172,
         29.23016035, 28.73183899, 28.23351762, 27.06330665,
         25.03645701, 8.80769991][::-1],
    ]),

    expected_loss_map=[173.30415881565, 44.4896055766335, 30.845799462654]
)


il = TestData(  # insured loss test data

    input_models_asset=[
        scientific.Asset(3000, ins_limit=1250, deductible=40),
        scientific.Asset(1000, ins_limit=40, deductible=13),
        scientific.Asset(2000, ins_limit=500, deductible=15),
    ],

    expected_poes=[
        [1., 0.947368, 0.894737, 0.842105, 0.789474, 0.736842, 0.684211,
            0.631579, 0.578947, 0.526316, 0.473684, 0.421053, 0.368421,
            0.315789, 0.263158, 0.210526, 0.157895, 0.105263, 0.052632, 0.],
        [1., 0.98063792, 0.96127585, 0.94191377, 0.9225517,
            0.90318962, 0.88382754, 0.86446547, 0.84510339, 0.82574132,
            0.80637924, 0.78701717, 0.76765509, 0.74829301, 0.72893094,
            0.70956886, 0.69020679, 0.67084471, 0.65148263, 0.63212056],
        [1., 0.947368, 0.894737, 0.842105, 0.789474, 0.736842,
            0.684211, 0.631579, 0.578947, 0.526316, 0.473684, 0.421053,
            0.368421, 0.315789, 0.263158, 0.210526, 0.157895, 0.105263,
            0.052632, 0.],
    ],

    expected_losses=numpy.array([
        [40.5835007, 70.37142354, 81.78761801, 94.22512956,
         108.02407352, 121.82301747, 135.62196142, 149.37739409,
         158.94810005, 168.51880601, 178.08951197, 187.66021794,
         197.2309239, 206.80162986, 216.37233582,
         225.94304178, 235.51374774, 245.0844, 254.65515, 264.225865],
        [13.1976005, 25.87908519, 29.46172057, 31.82735019,
         32.57069097, 33.31403175, 34.05737253, 34.79752526,
         35.23106482, 35.66460438, 36.09814394, 36.53168351,
         36.96522307, 37.39876263, 37.83230219, 38.26584175,
         38.69938131, 39.13292088, 39.56646044, 40.],
        [15.04698321, 28.02375039, 29.30889206, 30.11601202,
         30.28601773, 30.45602344, 30.62602916, 30.79449254,
         30.81501549, 30.83553843, 30.85606138, 30.87658432,
         30.89710727, 30.91763021, 30.93815316,
         30.9586761, 30.97919905, 30.99972199, 31.02024494,
         31.04076788],
    ]),

    expected_loss_map=None)


class EventBasedTestCase(unittest.TestCase):

    def assert_allclose(self, expected, actual):
        return numpy.testing.assert_allclose(
            expected, actual, atol=0.0, rtol=0.05)

    def test_mean_based(self):
        vulnerability_function_rm = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        vulnerability_function_rc = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.0035, 0.07, 0.14, 0.28, 0.56],
                [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        calculator_rm = api.ConditionalLosses(
            [CONDITIONAL_LOSS_POES],
            api.ProbabilisticEventBased(
                vulnerability_function_rm, 50, 50))

        calculator_rc = api.ConditionalLosses(
            [CONDITIONAL_LOSS_POES],
            api.ProbabilisticEventBased(
                vulnerability_function_rc, 50, 50))

        asset_outputs_rm = calculator_rm(mb.input_models_asset[0:2], gmf[0:2])
        [asset_output_rc] = calculator_rc([mb.input_models_asset[2]], [gmf[2]])

        for i, asset_output in enumerate(asset_outputs_rm):
            self.assertAlmostEqual(
                mb.expected_loss_map[i],
                asset_output.conditional_losses[CONDITIONAL_LOSS_POES],
                delta=0.05 * mb.expected_loss_map[i])

            self.assert_allclose(mb.expected_poes,
                                 asset_output.loss_ratio_curve.ordinates)

            self.assert_allclose(mb.expected_poes,
                                 asset_output.loss_curve.ordinates)

            self.assert_allclose(mb.expected_losses[i],
                                 asset_output.loss_curve.abscissae)

        self.assert_allclose(
            mb.expected_losses[2] / mb.input_models_asset[2].value,
            asset_output_rc.loss_ratio_curve.abscissae)

        self.assertAlmostEqual(
            mb.expected_loss_map[2],
            asset_output_rc.conditional_losses[CONDITIONAL_LOSS_POES],
            delta=0.05 * mb.expected_loss_map[2])

        self.assert_allclose(mb.expected_poes,
                             asset_output_rc.loss_ratio_curve.ordinates)

        self.assert_allclose(mb.expected_poes,
                             asset_output_rc.loss_curve.ordinates)

        self.assert_allclose(mb.expected_losses[2],
                             asset_output_rc.loss_curve.abscissae)

        self.assert_allclose(
            mb.expected_losses[2] / mb.input_models_asset[2].value,
            asset_output_rc.loss_ratio_curve.abscissae)

    def test_insured_loss_mean_based(self):
        vulnerability_function_rm = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.01, 0.1, 0.2, 0.4, 0.8],
                [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        vulnerability_function_rc = (
            scientific.VulnerabilityFunction(
                [0.001, 0.2, 0.3, 0.5, 0.7], [0.0035, 0.07, 0.14, 0.28, 0.56],
                [0.0, 0.0, 0.0, 0.0, 0.0], "LN"))

        calculator_rm = api.InsuredLosses(api.ProbabilisticEventBased(
            vulnerability_function_rm, time_span=50, tses=50,
            curve_resolution=20))

        calculator_rc = api.InsuredLosses(api.ProbabilisticEventBased(
            vulnerability_function_rc, time_span=50, tses=50,
            curve_resolution=20))

        asset_output_rm = calculator_rm(il.input_models_asset[0:2], gmf[0:2])
        asset_output_rc = calculator_rc([il.input_models_asset[2]], [gmf[2]])

        for i, asset_output in enumerate(asset_output_rm + asset_output_rc):
            self.assert_allclose(
                il.expected_poes[i],
                asset_output.insured_losses.ordinates)

            self.assert_allclose(
                il.expected_losses[i],
                asset_output.insured_losses.abscissae)
