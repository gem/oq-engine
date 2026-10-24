"""Regression tests for uncertainty propagation."""
import unittest
import pandas as pd
from types import SimpleNamespace
from openquake._unc.analysis import Analysis
from openquake._unc.processing.convolution import get_grp_ids, get_rlzs


def make_analysis(source_sets, dstores=None):
    dfs = [pd.DataFrame({'srcid': ids}) for ids in source_sets]
    if dstores is None:
        dstores = {srcid: {'oqparam': SimpleNamespace(investigation_time=1)}
                   for ids in source_sets for srcid in ids}
    return Analysis([b'gmpeModel'] * len(dfs), dfs, dstores,
                    'analysis.xml', seed=10)


class CorrelationRegressionTest(unittest.TestCase):
    def test_disconnected_component(self):
        an = make_analysis([['a', 'b'], ['c', 'd']])
        groups = {(1, src): [[0, 2], [1, 3]] for src in ['c', 'd']}
        ids, weights = get_grp_ids({'c', 'd'}, [1], an, groups)
        self.assertEqual(ids, [(0,), (1,)])
        self.assertEqual(weights, {'c': 1, 'd': 1})
        self.assertEqual(get_rlzs(an, 'c', groups, (1,), [1]), [1, 3])

    def test_nonconsecutive_uncertainties(self):
        an = make_analysis([['a', 'b'], ['c', 'd'], ['a', 'b']])
        groups = {(unc, src): vals
                  for unc, vals in [(0, [[0, 1], [2, 3]]),
                                    (2, [[0, 2], [1, 3]])]
                  for src in ['a', 'b']}
        ids, _ = get_grp_ids({'a', 'b'}, [0, 2], an, groups)
        self.assertEqual(ids, [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertEqual(get_rlzs(an, 'a', groups, (1, 0), [0, 2]), [2])
