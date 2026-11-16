"""Regression tests for uncertainty propagation."""
import unittest
import numpy as np
import pandas as pd
from types import SimpleNamespace
from openquake._unc.analysis import Analysis
from unittest.mock import Mock
from openquake._unc.processing.sampling import sampling


class Store(dict):
    """Minimal datastore interface, also accepting real HDF5 datasets."""
    def getitem(self, key):
        return self[key]


def make_analysis(source_sets, dstores=None):
    dfs = [pd.DataFrame({'srcid': ids}) for ids in source_sets]
    if dstores is None:
        dstores = {srcid: {'oqparam': SimpleNamespace(investigation_time=1)}
                   for ids in source_sets for srcid in ids}
    return Analysis([b'gmpeModel'] * len(dfs), dfs, dstores,
                    'analysis.xml', seed=10)


class SamplingRegressionTest(unittest.TestCase):
    def test_preserves_branch_probabilities(self):
        for weights in [[0.004, 0.996], [0.336, 0.336, 0.326, 0.002]]:
            with self.subTest(weights=weights):
                n = len(weights)
                poes = np.arange(1, n + 1).reshape(1, n, 1, 1) / 100.
                stores = {src: Store({
                    'oqparam': SimpleNamespace(investigation_time=50,
                                              hazard_imtls={'PGA': [0.1]}),
                    'weights': np.array(weights), 'hcurves-rlzs': poes})
                    for src in ['a', 'b']}
                an = make_analysis([['a', 'b']], stores)
                an.rng = Mock(wraps=an.rng)
                groups = {(0, src): [[i] for i in range(n)]
                          for src in stores}
                _, afes = sampling(an, groups, 20)
                p = an.rng.choice.call_args_list[0].kwargs['p']
                np.testing.assert_allclose(p, weights, rtol=1e-14)
                self.assertTrue((p > 0).all())
                np.testing.assert_allclose(afes[:, 0], afes[:, 1])
