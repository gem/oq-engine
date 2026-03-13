# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025-2026 GEM Foundation
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
from openquake._unc.analysis import Analysis, rlz_groups

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
    @classmethod
    def setUpClass(cls):
        fname = os.path.join(BDP, 'test_case02', 'analysis.xml')
        cls.an01 = Analysis.read(fname)

    def test_get_sets_01(self):
        # Check the groups with correlated uncertainties
        computed, _ = self.an01.get_sets()
        expected = [{'b', 'a', 'c'}, {'d'}]
        self.assertEqual(computed, expected)

        # check the correlation dataframe
        exp = '''\
    srcid  ipath
unc             
0       b      2
0       c      3
1       a     -1
1       b     -1'''
        self.assertEqual(str(self.an01.to_dframe()), exp)

    def test_get_imtls(self):
        # Check the IMLs for PGA
        an01 = self.an01
        imtls = an01.get_imtls()
        expected = np.logspace(np.log10(0.00001), np.log10(3.00), num=25)
        aac(expected, imtls['PGA'])

    def test_get_patterns(self):
        # Test the patterns created to select the realizations
        an01 = self.an01
        # - Source 'd' in the current test overall has 24 realizations (6 in
        #   the SSClt and 4 in the GMClt). It does not have correlated
        #   uncertainties
        # - Source 'c' has also 24 realizations (3x2) in the SSC and 4 in the
        #   GMClt. This source has correlated uncertainties with sources 'b'
        #   and 'c'
        rlzs, _, _ = an01.read_dstores('hcurves', 'PGA')
        patterns = an01.get_patterns(rlzs)
        # These are the patterns for the first uncertainty and source 'b'.
        # Overall the SSC LT for source 'b' contains 4 branchsets and the
        # correlated uncertainty is the third one.
        self.assertEqual(patterns[0]['b'], ['..A.~.', '..B.~.'])

        # Checking the patterns for the GMC
        expected = ['....~A', '....~B', '....~C', '....~D']
        self.assertEqual(patterns[1]['b'], expected)

    def test_rlz_groups(self):
        rlzs, poes, weights = self.an01.read_dstores('hcurves', 'PGA')
        patterns = self.an01.get_patterns(rlzs)
        grp = rlz_groups(rlzs, patterns)
        aeq(grp[0, 'b'], [[0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19],
                          [4, 5, 6, 7, 12, 13, 14, 15, 20, 21, 22, 23]])
        aeq(grp[0, 'c'], [[0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 20, 24,
                           25, 26, 30, 31, 32],
                          [3, 4, 5, 9, 10, 11, 15, 16, 17, 21, 22, 23,
                           27, 28, 29, 33, 34, 35]])
        aeq(grp[1, 'a'], [[0, 4, 8, 12, 16, 20], [1, 5, 9, 13, 17, 21],
                          [2, 6, 10, 14, 18, 22], [3, 7, 11, 15, 19, 23]])
        aeq(grp[1, 'b'], [[0, 4, 8, 12, 16, 20], [1, 5, 9, 13, 17, 21],
                          [2, 6, 10, 14, 18, 22], [3, 7, 11, 15, 19, 23]])


class AnalysisDisaggregationTestCase(unittest.TestCase):

    def test_read_dstore_disagg(self):
        fname = os.path.join(
            BDP, 'disaggregation', 'test_case01', 'analysis.xml')
        an01 = Analysis.read(fname)
        rlzs, poes, weights = an01.read_dstores('mde', 'PGA')
        self.assertEqual(['a', 'b'], list(rlzs))
        self.assertEqual(['a', 'b'], list(poes))
        self.assertEqual((17, 17, 8, 24), poes['a'].shape)
