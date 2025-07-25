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
from openquake._unc.analysis import Analysis, get_hcurves_ids

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

        exp = '''\
  bsid srcid  ordinal
0  bs3     b        2
1  bs4     c        3
2  bs1     a        0
3  bs1     b        0'''
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
        # This returns a triple. The first element is a dictionary with key the
        # ID of each source and with value a list. The list contains three
        # elements: an array with the paths for each realization of the SSClt,
        # and array witht the paths for each realization of the GMClt and a
        # list with the final paths for all the realizations.
        # -  Source 'a' in the current test overall it has 24 realizations (6 in
        #    the SSClt and 4 in the GMClt). It does not have correlated
        #    uncertainties
        # - Source 'b' has also 24 realizations (3x2) in the SSC and 4 in the
        #   GMClt. This source has correlated uncertainties with sources 'b'
        #   and 'c'
        rlzs, _, _ = an01.read_dstores('hcurves', 'PGA')
        patterns = an01.get_patterns(rlzs)
        # These are the patterns for the first uncertainty and source 'b'.
        # Overall the SSC LT for source 'b' contains 4 branchsets and the
        # correlated uncertainty is the third one.
        expected = ['^...A.~.', '^...B.~.']
        self.assertEqual(patterns[0]['b'], expected)
        # Checking the patterns for the GMC
        expected = ['^.....~A', '^.....~B', '^.....~C', '^.....~D']
        self.assertEqual(patterns[1]['b'], expected)

    def test_get_curves_and_weights(self):
        # Test the curve IDs
        an01 = self.an01
        rlzs, poes, weights = an01.read_dstores('hcurves', 'PGA')
        # Get the patterns
        patterns = an01.get_patterns(rlzs)
        # Get for each set of correlated uncertainties the source IDs
        # and the IDs of the realizations belonging to a sub-set of
        # correlated branches
        hcids = get_hcurves_ids(rlzs, patterns)
        # Test
        expected = [0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19]
        aeq(hcids[0]['b'][0], expected)


class AnalysisDisaggregationTestCase(unittest.TestCase):

    def test_read_dstore_disagg(self):
        fname = os.path.join(
            BDP, 'disaggregation', 'test_case01', 'analysis.xml')
        an01 = Analysis.read(fname)
        rlzs, poes, weights = an01.read_dstores('mde', 'PGA')
        self.assertEqual(['a', 'b'], list(poes))
        self.assertEqual((17, 17, 8, 24), poes['a'].shape)
