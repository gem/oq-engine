"""Means from original rates, independently of histogram approximation."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

import h5py
import numpy as np
import pandas as pd

from openquake._unc.analysis import Analysis
from openquake._unc.convolution import HistoGroup
from openquake._unc.hazard_pmf import mixture
from openquake._unc.processing.convolution import convolution


def histograms(rates, weights, res=2):
    """Construct histograms from realization rates with a fixed shape."""
    return HistoGroup.new(np.asarray(rates, dtype=float),
                          np.asarray(weights, dtype=float), res)


class Store(dict):
    """Minimal datastore for testing correlated source means."""
    def getitem(self, key):
        return self[key]


def source_store(rates, weights):
    """Represent supplied rates as stored hazard-curve probabilities."""
    rates = np.asarray(rates, dtype=float)
    return Store({
        'oqparam': SimpleNamespace(investigation_time=1.,
                                  hazard_imtls={'PGA': np.arange(
                                      rates.shape[1], dtype=float)}),
        'sitecol/sids': [0], 'weights': np.asarray(weights, dtype=float),
        'hcurves-rlzs': -np.expm1(-rates)[None, :, None, :]})


class RealizationMeanTest(unittest.TestCase):
    def test_weighted_means_do_not_depend_on_resolution(self):
        rates = np.array([[.011, 0., 1e-25], [.079, .22, 3e-25]])
        original = rates.copy()
        rates.flags.writeable = False
        expected = np.array([.0705, .1925, 2.75e-25])
        for res in [1, 5, 25]:
            with self.subTest(res=res):
                h = HistoGroup.new(rates, np.array([.125, .875]), res)
                np.testing.assert_allclose(h.mean_rates, expected, rtol=1e-15)
                np.testing.assert_allclose(h.get_stats([-1])[:, 0],
                                           expected[h.idxs], rtol=1e-15)
        np.testing.assert_array_equal(rates, original)

    def test_selected_realizations_normalize_their_weights(self):
        rates = np.array([[.011], [.039], [.082]])
        weights = np.array([.1, .2, .7])
        h = HistoGroup.new(rates, weights, 2, rlzs=[0, 2])
        expected = (.011 * .1 + .082 * .7) / .8
        self.assertAlmostEqual(h.get_stats([-1])[0, 0], expected, places=15)

    def test_float32_inputs_have_float64_means(self):
        rates = np.array([[.011], [.079]], dtype=np.float32)
        weights = np.array([.125, .875], dtype=np.float32)
        h = HistoGroup.new(rates, weights, 1)
        expected = float(rates[0, 0]) * .125 + float(rates[1, 0]) * .875
        self.assertEqual(h.mean_rates.dtype, np.dtype('float64'))
        self.assertEqual(h.mean_rates[0], expected)

    def test_independent_sources_add_original_means(self):
        a = histograms([[.011, .021], [.079, .18]], [.2, .8])
        b = histograms([[.041, .006], [.122, .061]], [.2, .8])
        result = a * b
        expected = np.array([.011 * .2 + .079 * .8 + .041 * .2 + .122 * .8,
                             .021 * .2 + .18 * .8 + .006 * .2 + .061 * .8])
        np.testing.assert_allclose(result.get_stats([-1])[:, 0], expected,
                                   rtol=1e-15)

    def test_percentiles_and_histogram_only_means_remain_available(self):
        h = histograms([[.011], [.079]], [.125, .875], res=1)
        binned = HistoGroup(h.pmfs, h.minpow, h.numpow)
        np.testing.assert_array_equal(h.get_stats([.16, .5, .84]),
                                      binned.get_stats([.16, .5, .84]))
        self.assertIsNone(binned.mean_rates)
        self.assertNotAlmostEqual(h.get_stats([-1])[0, 0],
                                  binned.get_stats([-1])[0, 0], places=3)

    def test_mixture_combines_original_means(self):
        a = histograms([[.01], [.09]], [.5, .5])
        b = histograms([[.2], [.4]], [.25, .75])
        a.weight, b.weight = 2., 6.
        result = mixture([a, b])
        self.assertAlmostEqual(result.get_stats([-1])[0, 0], .275, places=15)

    def test_mixture_accounts_for_zero_rate_groups(self):
        zero = histograms([[0.], [0.]], [.5, .5])
        positive = histograms([[.2], [.2]], [.5, .5])
        zero.weight, positive.weight = .25, .75
        result = mixture([zero, positive])
        self.assertAlmostEqual(result.get_stats([-1])[0, 0], .15, places=15)

    def test_zero_and_empty_histograms_keep_zero_means(self):
        zero = histograms([[0., 0.]], [1.])
        empty = histograms(np.empty((0, 2)), [])
        positive = histograms([[.011, .12]], [1.])
        for h in [zero, empty]:
            np.testing.assert_array_equal(h.mean_rates, [0., 0.])
            self.assertEqual(h.get_stats([-1]).shape, (0, 1))
            np.testing.assert_array_equal((h * positive).mean_rates,
                                          positive.mean_rates)

    def test_export_preserves_original_means(self):
        h = histograms([[0., .011], [0., .079]], [.125, .875])
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'histograms.hdf5')
            h.save(path)
            with h5py.File(path, 'r') as saved:
                np.testing.assert_array_equal(saved['mean_rates'][:],
                                              h.mean_rates)
                self.assertEqual(saved['histograms'].shape[1], 2)


class CorrelatedRealizationMeanTest(unittest.TestCase):
    def test_correlated_and_independent_sources_use_marginal_means(self):
        rates = {'a': [[.011, .022], [.079, .18]],
                 'b': [[.041, .006], [.122, .061]],
                 'c': [[.025, .021], [.041, .034]]}
        weights = {'a': [.2, .8], 'b': [.2, .8], 'c': [.65, .35]}
        stores = {src: source_store(values, weights[src])
                  for src, values in rates.items()}
        an = Analysis([b'gmpeModel'], [pd.DataFrame({'srcid': ['a', 'b']})],
                      stores, 'analysis.xml', 10)
        groups = {(0, src): [[0], [1]] for src in ['a', 'b']}
        # Enumerate joint states as an independent reference.
        expected = np.zeros(2)
        for shared in range(2):
            for independent in range(2):
                total = (np.array(rates['a'][shared]) +
                         np.array(rates['b'][shared]) +
                         np.array(rates['c'][independent]))
                expected += (weights['a'][shared] *
                             weights['c'][independent] * total)
        for res in [1, 5]:
            with self.subTest(res=res):
                h = convolution(an, groups, 'PGA', 'hcurves', res)
                np.testing.assert_allclose(h.get_stats([-1])[:, 0], expected,
                                           rtol=1e-15)

    def test_partially_shared_uncertainties_with_unequal_weights(self):
        rates = {'a': [[.011], [.071]],
                 'b': [[.018], [.039], [.095], [.16]],
                 'c': [[.025], [.082]]}
        weights = {'a': [.2, .8], 'b': [.06, .14, .24, .56], 'c': [.3, .7]}
        stores = {src: source_store(values, weights[src])
                  for src, values in rates.items()}
        dfs = [pd.DataFrame({'srcid': ['a', 'b']}),
               pd.DataFrame({'srcid': ['b', 'c']})]
        an = Analysis([b'maxMag', b'gmpeModel'], dfs, stores,
                      'analysis.xml', 10)
        groups = {(0, 'a'): [[0], [1]], (0, 'b'): [[0, 1], [2, 3]],
                  (1, 'b'): [[0, 2], [1, 3]], (1, 'c'): [[0], [1]]}
        # The middle source depends on both correlated branch selections.
        expected = np.zeros(1)
        for first in range(2):
            for second in range(2):
                total = (np.array(rates['a'][first]) +
                         np.array(rates['b'][2 * first + second]) +
                         np.array(rates['c'][second]))
                expected += weights['a'][first] * weights['c'][second] * total
        h = convolution(an, groups, 'PGA', 'hcurves', res=1)
        np.testing.assert_allclose(h.mean_rates, expected, rtol=1e-15)
        np.testing.assert_allclose(h.get_stats([-1])[:, 0], expected,
                                   rtol=1e-15)
