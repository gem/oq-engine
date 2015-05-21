import unittest
import os.path
import shutil
import tempfile

import numpy
from scipy.stats import mstats
from openquake.commonlib import writers, tests
from openquake.risklib import scientific, workflows

aaae = numpy.testing.assert_array_almost_equal


class MeanCurveTestCase(unittest.TestCase):

    def test_compute_mean_curve(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]

        expected_mean_curve = numpy.array([0.83, 0.67333333, 0.54333333, 0.17])
        numpy.testing.assert_allclose(
            expected_mean_curve, scientific.mean_curve(curves))

    def test_compute_mean_curve_weighted(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = [0.5, 0.3, 0.2]

        expected_mean_curve = numpy.array([0.885, 0.735, 0.586, 0.213])
        numpy.testing.assert_allclose(
            expected_mean_curve,
            scientific.mean_curve(curves, weights=weights))

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
            expected_mean_curve,
            scientific.mean_curve(curves, weights=weights))

    def test_compute_mean_curve_invalid_weights(self):
        curves = [
            [1.0, 0.85, 0.67, 0.3],
            [0.87, 0.76, 0.59, 0.21],
            [0.62, 0.41, 0.37, 0.0],
        ]
        weights = [0.6, None, 0.4]
        with self.assertRaises(TypeError):
            # None is not a valid weight
            scientific.mean_curve(curves, weights)


class QuantileCurveTestCase(unittest.TestCase):

    def test_compute_quantile_curve(self):
        expected_curve = numpy.array([
            9.9178000e-01, 9.8892000e-01, 9.6903000e-01, 9.4030000e-01,
            8.8405000e-01, 7.8782000e-01, 6.4897250e-01, 4.8284250e-01,
            3.4531500e-01, 3.2337000e-01, 1.8880500e-01, 9.5574000e-02,
            4.3707250e-02, 1.9643000e-02, 8.1923000e-03, 2.9157000e-03,
            7.9955000e-04, 1.5233000e-04, 1.5582000e-05])

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
        actual_curve = scientific.quantile_curve(curves, quantile)

        # TODO(LB): Check with our hazard experts to see if this is reasonable
        # tolerance. Better yet, get a fresh set of test data. (This test data
        # was just copied verbatim from from some old tests in
        # `tests/hazard_test.py`.
        numpy.testing.assert_allclose(expected_curve, actual_curve, atol=0.005)

        # Since this implementation is an optimized but equivalent version of
        # scipy's `mquantiles`, compare algorithms just to prove they are the
        # same:
        scipy_curve = mstats.mquantiles(curves, prob=quantile, axis=0)[0]
        numpy.testing.assert_allclose(scipy_curve, actual_curve)

    def test_compute_weighted_quantile_curve_case1(self):
        expected_curve = numpy.array([0.69909, 0.60859, 0.50328])

        quantile = 0.3

        curves = [
            [9.9996e-01, 9.9962e-01, 9.9674e-01],
            [6.9909e-01, 6.0859e-01, 5.0328e-01],
            [1.0000e+00, 9.9996e-01, 9.9947e-01],
        ]
        weights = [0.5, 0.3, 0.2]

        actual_curve = scientific.quantile_curve(curves, quantile, weights)

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

        actual_curve = scientific.quantile_curve(curves, quantile, weights)

        numpy.testing.assert_allclose(expected_curve, actual_curve)


class NormalizeTestCase(unittest.TestCase):

    def test_normalize_all_trivial(self):
        poes = numpy.linspace(1, 0, 11)
        losses = numpy.zeros(11)
        curves = [[losses, poes], [losses, poes / 2]]
        exp_losses, (poes1, poes2) = scientific.normalize_curves_eb(curves)

        numpy.testing.assert_allclose(exp_losses, losses)
        numpy.testing.assert_allclose(poes1, poes)
        numpy.testing.assert_allclose(poes2, poes / 2)

    def test_normalize_one_trivial(self):
        trivial = [numpy.zeros(6), numpy.linspace(1, 0, 6)]
        curve = [numpy.linspace(0., 1., 6), numpy.linspace(1., 0., 6)]
        with numpy.errstate(invalid='ignore', divide='ignore'):
            exp_losses, (poes1, poes2) = scientific.normalize_curves_eb(
                [trivial, curve])

        numpy.testing.assert_allclose(exp_losses, curve[0])
        numpy.testing.assert_allclose(poes1, [numpy.nan, 0., 0., 0., 0., 0.])
        numpy.testing.assert_allclose(poes2, curve[1])


def asset(ref, value, deductibles=None,
          insurance_limits=None,
          retrofitting_values=None):
    return workflows.Asset(ref, 'taxonomy', 1, (0, 0), dict(structural=value),
                           1, deductibles, insurance_limits,
                           retrofitting_values)


# return a matrix N x 2 x R with n=2, R=5
def loss_curves(assets, baselosses, seed):
    numpy.random.seed(seed)
    lcs = []
    for asset in assets:
        poes = sorted(numpy.random.rand(5), reverse=True)
        losses = sorted(baselosses * asset.value('structural') + seed)
        lcs.append((losses, poes))
    return numpy.array(lcs)


class StatsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assets = [asset('a1', 101), asset('a2', 151), asset('a3', 91),
                  asset('a4', 81)]
        asset_refs = [a.id for a in assets]
        outputs = []
        weights = [0.3, 0.7]
        baselosses = numpy.array([.10, .14, .17, .20, .21])
        for i, w in enumerate(weights):
            lc = loss_curves(assets, baselosses, i)
            out = scientific.Output(asset_refs, 'structural', weight=w,
                                    loss_curves=lc, insured_curves=None)
            outputs.append(out)
        cls.stats = scientific.StatsBuilder(
            quantiles=[0.1, 0.9],
            conditional_loss_poes=[0.35, 0.24, 0.13],
            poes_disagg=[]).build(outputs)
        cls.tempdir = tempfile.mkdtemp()

    def test_get_stat_curves(self):
        curves, ins_curves, maps = scientific.get_stat_curves(self.stats)

        actual = os.path.join(self.tempdir, 'expected_loss_curves.csv')
        writers.write_csv(actual, curves, fmt='%05.2f')
        tests.check_equal(__file__, 'expected_loss_curves.csv', actual)

        actual = os.path.join(self.tempdir, 'expected_ins_curves.csv')
        writers.write_csv(actual, ins_curves, fmt='%05.2f')
        tests.check_equal(__file__, 'expected_ins_curves.csv', actual)

        actual = os.path.join(self.tempdir, 'expected_loss_maps.csv')
        writers.write_csv(actual, maps, fmt='%05.2f')
        tests.check_equal(__file__, 'expected_loss_maps.csv', actual)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)
