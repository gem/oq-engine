#
# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025 GEM Foundation
#
#                `.......      `....     `..`...     `..`... `......
#                `..    `..  `..    `..  `..`. `..   `..     `..
#                `..    `..`..        `..`..`.. `..  `..     `..
#                `.......  `..        `..`..`..  `.. `..     `..
#                `..       `..        `..`..`..   `. `..     `..
#                `..         `..     `.. `..`..    `. ..     `..
#                `..           `....     `..`..      `..     `..
#
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8
import os
import unittest
import numpy as np
from openquake._unc.analysis import Analysis, get_patterns, get_hcurves_ids

# Base Data Path
BDP = os.path.join(os.path.dirname(__file__), 'data_calc')

# Testing
aac = np.testing.assert_allclose
aeq = np.testing.assert_equal


class AnalysisTestCase(unittest.TestCase):
    """
    Tests various methods of the :class:`openquake._unc.analysis.Analysis`
    class.
    """

    def setUp(self):
        self.fname = os.path.join(BDP, 'test_case02', 'analysis.xml')
        self.an01 = Analysis.read(self.fname)

    def test01(self):
        """ Check the info describing correlation """
        an01 = self.an01
        expected = {('b', 2, 'ssc'): 'bs1', ('c', 3, 'ssc'): 'bs1',
                    ('a', 0, 'gmc'): 'bs2', ('b', 0, 'gmc'): 'bs2'}
        self.assertEqual(an01.corbs_per_src, expected)

    def test_get_sets_01(self):
        """ Check the groups with correlated uncertainties """
        an01 = self.an01
        computed, _ = an01.get_sets()
        expected = [set(['b', 'a', 'c']), set(['d'])]
        self.assertEqual(computed, expected)

    def test_get_imls(self):
        """ Check the IMLs for PGA """
        an01 = self.an01
        imtls = an01.get_imls()
        expected = np.logspace(np.log10(0.00001), np.log10(3.00), num=25)
        aac(expected, imtls['PGA'])

    def test_get_patterns(self):
        """ Test the patterns created to select the realizations """
        an01 = self.an01
        root_path = os.path.dirname(self.fname)
        rlzs, _, _ = an01.read_dstores(root_path, 'hcurves', 'PGA' )
        patterns = get_patterns(rlzs, an01)
        # These are the patterns for the first uncertainty and source 'b'.
        # Overall the SSC LT for source 'b' contains 4 branchsets and the
        # correlated uncertainty is the third one.
        expected = ['^.+.+A.+~.+', '^.+.+B.+~.+']
        self.assertEqual(patterns['bs1']['b'], expected)

    def test_get_curves_and_weights(self):
        """ Test the curve IDs """
        an01 = self.an01
        root_path = os.path.dirname(self.fname)
        rlzs, poes, weights = an01.read_dstores(root_path, 'hcurves', 'PGA')
        # Get the patterns
        patterns = get_patterns(rlzs, an01)
        # Get for each set of correlated uncertaintiess the source the IDs
        # and the IDs of the realizations belonging to a sub-set of
        # correlated branches and the corresponding weights
        hcids, weis = get_hcurves_ids(rlzs, patterns, weights)
        # Test
        expected = [0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19]
        aeq(hcids['bs1']['b'][0], expected)
        aac(weis['bs1']['b'][0], 0.8)


class AnalysisDisaggregationTestCase(unittest.TestCase):

    def setUp(self):
        tmp_path = os.path.join(BDP, 'disaggregation', 'test_case01')
        self.fname = os.path.join(tmp_path, 'analysis.xml')
        self.an01 = Analysis.read(self.fname)

    def test_read_dstore_disagg(self):
        an01 = self.an01
        root_path = os.path.dirname(self.fname)
        rlzs, poes, weights = an01.read_dstores(root_path, 'mde', 'PGA')
        self.assertEqual(['a', 'b'], list(poes.keys()))
        self.assertEqual((17, 17, 8, 24), poes['a'].shape)
