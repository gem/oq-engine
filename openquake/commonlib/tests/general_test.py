# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Test related to code in openquake/utils/general.py
"""

import unittest

from openquake.commonlib.general import block_splitter, split_in_blocks


class BlockSplitterTestCase(unittest.TestCase):
    """Tests for :function:`openquake.commonlib.general.block_splitter`."""

    DATA = range(10)

    def test_block_splitter(self):
        expected = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [9],
        ]
        actual = [x for x in block_splitter(self.DATA, 3)]
        self.assertEqual(expected, actual)

    def test_block_splitter_block_size_eq_data_len(self):
        expected = [self.DATA]
        actual = [x for x in block_splitter(self.DATA, 10)]
        self.assertEqual(expected, actual)

    def test_block_splitter_block_size_gt_data_len(self):
        expected = [self.DATA]
        actual = [x for x in block_splitter(self.DATA, 11)]
        self.assertEqual(expected, actual)

    def test_block_splitter_zero_block_size(self):
        gen = block_splitter(self.DATA, 0)
        self.assertRaises(ValueError, gen.next)

    def test_block_splitter_block_size_lt_zero(self):
        gen = block_splitter(self.DATA, -1)
        self.assertRaises(ValueError, gen.next)

    def test_block_splitter_with_generator(self):
        # Test the block with a data set of unknown length
        # (such as a generator)
        data = xrange(10)
        expected = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [9],
        ]
        actual = [x for x in block_splitter(data, 3)]
        self.assertEqual(expected, actual)

    def test_block_splitter_with_iter(self):
        # Test the block with a data set of unknown length
        data = iter(range(10))
        expected = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [9],
        ]
        actual = [x for x in block_splitter(data, 3)]
        self.assertEqual(expected, actual)

    def test_split_with_weight(self):
        weigths = dict([('a', 11), ('b', 10), ('c', 100), ('d', 15), ('e', 20),
                        ('f', 5), ('g', 30), ('h', 17), ('i', 25)])
        blocks = list(block_splitter('abcdefghi', 50, weigths.get))
        self.assertEqual(repr(blocks), "[<WeightedSequence ['a', 'b'], weight=21>, <WeightedSequence ['c'], weight=100>, <WeightedSequence ['d', 'e', 'f'], weight=40>, <WeightedSequence ['g', 'h'], weight=47>, <WeightedSequence ['i'], weight=25>]")

    def test_split_in_blocks(self):
        weigths = dict([('a', 11), ('b', 10), ('c', 100), ('d', 15), ('e', 20),
                        ('f', 5), ('g', 30), ('h', 17), ('i', 25)])
        blocks = list(split_in_blocks('abcdefghi', 1, weigths.get))
        self.assertEqual(len(blocks), 1)
        blocks = list(split_in_blocks('abcdefghi', 2, weigths.get))
        self.assertEqual(len(blocks), 3)
        self.assertEqual(repr(blocks), "[<WeightedSequence ['a', 'b'], weight=21>, <WeightedSequence ['c', 'd'], weight=115>, <WeightedSequence ['e', 'f', 'g', 'h', 'i'], weight=97>]")
