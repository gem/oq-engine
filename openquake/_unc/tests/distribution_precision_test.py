"""Reference checks for zero atoms, rare branches and binning precision."""
import itertools
import tempfile
from pathlib import Path
import unittest

import h5py
import numpy as np

from openquake._unc.convolution import HistoGroup
from openquake._unc.hazard_pmf import mixture
from openquake._unc.utils import weighted_percentile


def histogram(values, weights, res=50):
    """Build a one-column distribution with supplied realization weights."""
    return HistoGroup.new(np.asarray(values, dtype=float)[:, None],
                          np.asarray(weights), res)


def total_mass(h):
    """Return complete masses, including the atom outside logarithmic bins."""
    return np.array([z + (0. if pmf is None else pmf.sum())
                     for z, pmf in zip(h.zero_mass, h.pmfs)])


class ZeroMassTest(unittest.TestCase):
    def test_mixture_zero_atom_controls_percentiles(self):
        zero = histogram([0.], [1.])
        positive = histogram([.2], [1.])
        zero.weight, positive.weight = .8, .2
        result = mixture([zero, positive])
        np.testing.assert_allclose(result.zero_mass, [.8], atol=1e-15)
        np.testing.assert_allclose(total_mass(result), [1.], atol=1e-15)
        stats = result.get_stats([-1, 0., .5, .8, .9, 1.])[0]
        self.assertAlmostEqual(stats[0], .04)
        np.testing.assert_array_equal(stats[1:4], [0., 0., 0.])
        np.testing.assert_allclose(stats[4:], [.2, .2], rtol=.025)

    def test_realizations_keep_exact_zero_and_small_positive_rates(self):
        rates = np.array([[0.], [1e-25], [.2]])
        weights = np.array([.6, .1, .3])
        original = rates.copy()
        rates.flags.writeable = False
        h = HistoGroup.new(rates, weights, 10)
        np.testing.assert_allclose(h.zero_mass, [.6], atol=1e-15)
        self.assertEqual(h.minpow[0], -25)
        self.assertAlmostEqual(h.pmfs[0].sum(), .4)
        self.assertEqual(h.get_stats([.5])[0, 0], 0.)
        np.testing.assert_array_equal(rates, original)

    def test_convolution_includes_zero_positive_cross_terms(self):
        a = histogram([0., .1], [.7, .3], 100)
        b = histogram([0., .2], [.6, .4], 100)
        result = a * b
        np.testing.assert_allclose(result.zero_mass, [.42], atol=1e-15)
        self.assertAlmostEqual(result.pmfs[0].sum(), .58)
        np.testing.assert_allclose(total_mass(result), [1.], atol=1e-15)
        values = result.get_stats([-1, .4, .5, .8, .99])[0]
        np.testing.assert_allclose(values[:2], [.11, 0.], atol=1e-15)
        # Enumerated states: 0 (.42), .1 (.18), .2 (.28), .3 (.12).
        bins = np.logspace(result.minpow[0],
                           result.minpow[0] + result.numpow[0],
                           len(result.pmfs[0]) + 1)
        mids = bins[:-1] + np.diff(bins) / 2
        for target, mass in [(.1, .18), (.2, .28), (.3, .12)]:
            found = np.abs(mids / target - 1.) < .04
            self.assertAlmostEqual(result.pmfs[0][found].sum(), mass)

    def test_pure_zero_identity_ignores_histogram_resolution(self):
        zero = histogram([0.], [1.], res=1)
        h = histogram([0., .02, .2], [.3, .4, .3], res=20)
        for result in [zero * h, h * zero]:
            np.testing.assert_allclose(result.zero_mass, h.zero_mass)
            np.testing.assert_allclose(result.get_stats([-1, .2, .7]),
                                       h.get_stats([-1, .2, .7]))
            np.testing.assert_allclose(total_mass(result), [1.])

    def test_unnormalized_mixtures_keep_relative_zero_mass(self):
        zero = histogram([0.], [1.])
        positive = histogram([.2], [1.])
        zero.weight, positive.weight = 8., 2.
        result = mixture([zero, positive])
        np.testing.assert_allclose(total_mass(result), [10.])
        self.assertEqual(result.get_stats([.5])[0, 0], 0.)
        convolved = result * histogram([0.], [1.])
        np.testing.assert_allclose(total_mass(convolved), [1.])
        np.testing.assert_allclose(convolved.zero_mass, [.8])
        self.assertEqual(convolved.get_stats([.5])[0, 0], 0.)

    def test_histogram_only_mean_includes_zero_mass(self):
        h = HistoGroup([np.array([.2])], [-1], [1], zero_mass=[.8])
        self.assertAlmostEqual(h.get_stats([-1])[0, 0], .55 * .2)
        self.assertEqual(h.get_stats([.5])[0, 0], 0.)

    def test_serialization_preserves_complete_distribution(self):
        h = histogram([0., .2], [.8, .2])
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'distribution.hdf5')
            h.save(path)
            with h5py.File(path, 'r') as saved:
                zero = saved['zero_mass'][:]
                positive = np.nansum(saved['histograms'][:], axis=0)
                np.testing.assert_allclose(zero, [.8])
                np.testing.assert_allclose(zero + positive, [1.])


class RareMassTest(unittest.TestCase):
    def test_float32_weights_preserve_rare_branch(self):
        weights = np.array([1., 1e-8], dtype=np.float32)
        original = weights.copy()
        h = histogram([.015, .075], weights, res=2)
        self.assertEqual(h.pmfs[0].dtype, np.dtype('float64'))
        self.assertAlmostEqual(h.pmfs[0][1] / h.pmfs[0][0],
                               float(weights[1]), places=20)
        np.testing.assert_array_equal(weights, original)

    def test_direct_bin_accumulation_keeps_sub_epsilon_branch(self):
        h = histogram([.015, .075], [1., 1e-20], res=2)
        self.assertEqual(h.pmfs[0][1], 1e-20)
        self.assertGreater(h.get_stats([1.])[0, 0], .06)

    def test_zero_probability_bins_do_not_change_quantile_endpoints(self):
        values = np.array([1., 2., 3., 4.])
        weights = np.array([0., .25, .75, 0.], dtype=np.float32)
        result = weighted_percentile(values, weights, [0., 1.])
        np.testing.assert_array_equal(result, [2., 3.])

    def test_float32_cdf_uses_float64_accumulation(self):
        count = 100000
        values = np.arange(count, dtype=float)
        weights = np.full(count, 1. / count, dtype=np.float32)
        quantiles = np.array([.16, .5, .84])
        expected = count * quantiles - .5
        np.testing.assert_allclose(
            weighted_percentile(values, weights, quantiles), expected,
            rtol=0, atol=1e-6)

    def test_zero_atom_does_not_hide_rare_positive_endpoint(self):
        h = histogram([0., .2], [1., 1e-20])
        self.assertEqual(h.get_stats([.5])[0, 0], 0.)
        self.assertGreater(h.get_stats([1.])[0, 0], .19)


class BinningConvergenceTest(unittest.TestCase):
    def setUp(self):
        self.values = [np.geomspace(.01, .1, 17),
                       np.geomspace(.02, .12, 19),
                       np.geomspace(.005, .08, 13)]
        states = np.array(list(itertools.product(*self.values)))
        exact = states.sum(axis=1)
        self.quantiles = [.16, .5, .84]
        self.reference = weighted_percentile(
            exact, np.ones(len(exact)), self.quantiles)

    def convolve(self, res, order=(0, 1, 2)):
        hs = [histogram(v, np.ones(len(v)), res) for v in self.values]
        result = hs[order[0]]
        for index in order[1:]:
            result *= hs[index]
        np.testing.assert_allclose(total_mass(result), [1.], atol=1e-14)
        return result.get_stats(self.quantiles)[0]

    def test_resolution_convergence_against_enumeration(self):
        errors = []
        for res in [50, 100, 200, 400]:
            result = self.convolve(res)
            errors.append(np.max(np.abs(result / self.reference - 1.)))
        self.assertLess(errors[-1], .005)
        self.assertLess(errors[-1], errors[0])

    def test_source_order_sensitivity_is_bounded(self):
        results = np.array([self.convolve(400, order)
                            for order in itertools.permutations(range(3))])
        np.testing.assert_allclose(results,
                                   np.tile(self.reference, (6, 1)), rtol=.01)
        relative_spread = np.ptp(results, axis=0) / self.reference
        self.assertLess(relative_spread.max(), .005)


class SamplingWeightPrecisionTest(unittest.TestCase):
    def test_float32_stored_weights_are_normalized_in_float64(self):
        from types import SimpleNamespace
        from openquake._unc.analysis import Analysis
        from openquake._unc.processing.sampling import sampling
        from unittest.mock import Mock

        weights = np.array([1. / 3] * 3, dtype=np.float32)
        original = weights.copy()
        store = {'oqparam': SimpleNamespace(investigation_time=1.,
                                           hazard_imtls={'PGA': [.1]}),
                 'weights': weights,
                 'hcurves-rlzs': np.array([.01, .02, .03]).reshape(1, 3, 1, 1)}
        an = Analysis([], [], {'a': store}, 'analysis.xml', 10)
        an.rng = Mock(wraps=an.rng)
        sampling(an, {}, 10)
        probabilities = an.rng.choice.call_args_list[0].kwargs['p']
        self.assertEqual(probabilities.dtype, np.dtype('float64'))
        self.assertAlmostEqual(probabilities.sum(), 1., places=15)
        np.testing.assert_array_equal(weights, original)
