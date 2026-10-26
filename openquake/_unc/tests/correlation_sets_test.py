"""Regression tests for uncertainty propagation."""
import unittest
import pandas as pd
from types import SimpleNamespace
from openquake._unc.analysis import Analysis


def make_analysis(source_sets, dstores=None):
    dfs = [pd.DataFrame({'srcid': ids}) for ids in source_sets]
    if dstores is None:
        dstores = {srcid: {'oqparam': SimpleNamespace(investigation_time=1)}
                   for ids in source_sets for srcid in ids}
    return Analysis([b'gmpeModel'] * len(dfs), dfs, dstores,
                    'analysis.xml', seed=10)


class CorrelationRegressionTest(unittest.TestCase):
    def test_bridge_merges_all_components(self):
        an = make_analysis([['a', 'b'], ['c', 'd'], ['b', 'c']])
        self.assertEqual(an.get_sets(),
                         ([{'a', 'b', 'c', 'd'}], [{0, 1, 2}]))
