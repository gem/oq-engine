import unittest
import numpy
from openquake.hazardlib.stats import mean_curve, quantile_curve

aaae = numpy.testing.assert_array_almost_equal


class MeanCurveTestCase(unittest.TestCase):

    def test_compute_mean_curve(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]

        expected_mean_curve = numpy.array([0.83, 0.67333333, 0.54333333, 0.17])
        numpy.testing.assert_allclose(expected_mean_curve, mean_curve(curves))

    def test_compute_mean_curve_weighted(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = [0.5, 0.3, 0.2]

        expected_mean_curve = numpy.array([0.885, 0.735, 0.586, 0.213])
        numpy.testing.assert_allclose(
            expected_mean_curve, mean_curve(curves, weights=weights))

    def test_compute_mean_curve_weights_None(self):
        # If all weight values are None, ignore the weights altogether
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = None

        expected_mean_curve = numpy.array([0.83, 0.67333333, 0.54333333, 0.17])
        numpy.testing.assert_allclose(
            expected_mean_curve, mean_curve(curves, weights=weights))


class QuantileCurveTestCase(unittest.TestCase):

    def test_compute_quantile_curve(self):
        expected_curve = numpy.array(
            [0.9910475, 0.9879525, 0.9667025, 0.9366125, 0.8806675, 0.7864,
             0.64627, 0.47537, 0.335625, 0.3135875, 0.1807475, 0.091399,
             0.042766, 0.0191415, 0.00796135, 0.002823625, 0.00077053,
             0.0001457375, 1.489975e-05])

        quantile = 0.75

        curves = [
            [9.8161000e-01, 9.7837000e-01, 9.5579000e-01, 9.2555000e-01,
             8.7052000e-01, 7.8214000e-01, 6.5708000e-01, 5.0526000e-01,
             3.7044000e-01, 3.4740000e-01, 2.0502000e-01, 1.0506000e-01,
             4.6531000e-02, 1.7548000e-02, 5.4791000e-03, 1.3377000e-03,
             2.2489000e-04, 2.2345000e-05, 4.2696000e-07],
            [9.7309000e-01, 9.6857000e-01, 9.3853000e-01, 9.0089000e-01,
             8.3673000e-01, 7.4057000e-01, 6.1272000e-01, 4.6467000e-01,
             3.3694000e-01, 3.1536000e-01, 1.8340000e-01, 9.2412000e-02,
             4.0202000e-02, 1.4900000e-02, 4.5924000e-03, 1.1126000e-03,
             1.8647000e-04, 1.8882000e-05, 4.7123000e-07],
            [9.9178000e-01, 9.8892000e-01, 9.6903000e-01, 9.4030000e-01,
             8.8405000e-01, 7.8782000e-01, 6.4627000e-01, 4.7537000e-01,
             3.3168000e-01, 3.0827000e-01, 1.7279000e-01, 8.8360000e-02,
             4.2766000e-02, 1.9643000e-02, 8.1923000e-03, 2.9157000e-03,
             7.9955000e-04, 1.5233000e-04, 1.5582000e-05],
            [9.8885000e-01, 9.8505000e-01, 9.5972000e-01, 9.2494000e-01,
             8.6030000e-01, 7.5574000e-01, 6.1009000e-01, 4.4217000e-01,
             3.0543000e-01, 2.8345000e-01, 1.5760000e-01, 8.0225000e-02,
             3.8681000e-02, 1.7637000e-02, 7.2685000e-03, 2.5474000e-03,
             6.8347000e-04, 1.2596000e-04, 1.2853000e-05],
            [9.9178000e-01, 9.8892000e-01, 9.6903000e-01, 9.4030000e-01,
             8.8405000e-01, 7.8782000e-01, 6.4627000e-01, 4.7537000e-01,
             3.3168000e-01, 3.0827000e-01, 1.7279000e-01, 8.8360000e-02,
             4.2766000e-02, 1.9643000e-02, 8.1923000e-03, 2.9157000e-03,
             7.9955000e-04, 1.5233000e-04, 1.5582000e-05],
        ]
        actual_curve = quantile_curve(quantile, curves)
        numpy.testing.assert_allclose(expected_curve, actual_curve, atol=0.005)

    def test_compute_weighted_quantile_curve_case1(self):
        expected_curve = numpy.array([0.69909, 0.60859, 0.50328])

        quantile = 0.3

        curves = [
            [9.9996e-01, 9.9962e-01, 9.9674e-01],
            [6.9909e-01, 6.0859e-01, 5.0328e-01],
            [1.0000e+00, 9.9996e-01, 9.9947e-01],
        ]
        weights = [0.5, 0.3, 0.2]

        actual_curve = quantile_curve(quantile, curves, weights)

        numpy.testing.assert_allclose(expected_curve, actual_curve)

    def test_compute_weighted_quantile_curve_case2(self):
        expected_curve = numpy.array([0.89556, 0.83045, 0.73646])

        quantile = 0.3

        curves = [
            [9.2439e-01, 8.6700e-01, 7.7785e-01],
            [8.9556e-01, 8.3045e-01, 7.3646e-01],
            [9.1873e-01, 8.6697e-01, 7.8992e-01],
        ]
        weights = [0.2, 0.3, 0.5]

        actual_curve = quantile_curve(quantile, curves, weights)

        numpy.testing.assert_allclose(expected_curve, actual_curve)
