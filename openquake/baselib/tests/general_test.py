# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2010-2017 GEM Foundation
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

import mock
import unittest
from operator import attrgetter
from collections import namedtuple

from openquake.baselib.general import (
    block_splitter, split_in_blocks, search_module, assert_close,
    deprecated, DeprecationWarning)


class BlockSplitterTestCase(unittest.TestCase):
    """Tests for :func:`openquake.baselib.general.block_splitter`."""

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
        with self.assertRaises(ValueError):
            next(gen)

    def test_block_splitter_block_size_lt_zero(self):
        gen = block_splitter(self.DATA, -1)
        with self.assertRaises(ValueError):
            next(gen)

    def test_block_splitter_with_generator(self):
        # Test the block with a data set of unknown length
        # (such as a generator)
        data = range(10)
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
        data = range(10)
        expected = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [9],
        ]
        actual = [x for x in block_splitter(data, 3)]
        self.assertEqual(expected, actual)

    def test_split_with_weight(self):
        weights = dict([('a', 11), ('b', 10), ('c', 100), ('d', 15), ('e', 20),
                        ('f', 5), ('g', 30), ('h', 17), ('i', 25)])
        blocks = list(block_splitter('abcdefghi', 50, weights.get))
        self.assertEqual(repr(blocks), "[<WeightedSequence ['a', 'b'], weight=21>, <WeightedSequence ['c'], weight=100>, <WeightedSequence ['d', 'e', 'f'], weight=40>, <WeightedSequence ['g', 'h'], weight=47>, <WeightedSequence ['i'], weight=25>]")

    def test_split_in_blocks(self):
        weights = dict([('a', 11), ('b', 10), ('c', 100), ('d', 15), ('e', 20),
                        ('f', 5), ('g', 30), ('h', 17), ('i', 25)])
        blocks = list(split_in_blocks('abcdefghi', 1, weights.get))
        self.assertEqual(len(blocks), 1)
        blocks = list(split_in_blocks('abcdefghi', 2, weights.get))
        self.assertEqual(len(blocks), 3)
        self.assertEqual(repr(blocks), "[<WeightedSequence ['a', 'b'], weight=21>, <WeightedSequence ['c', 'd'], weight=115>, <WeightedSequence ['e', 'f', 'g', 'h', 'i'], weight=97>]")

    def test_split_with_kind(self):
        Source = namedtuple('Source', 'typology, weight')
        s1 = Source('point', 1)
        s2 = Source('point', 1)
        s3 = Source('area', 2)
        s4 = Source('area', 4)
        s5 = Source('area', 4)
        blocks = list(
            block_splitter([s1, s2, s3, s4, s5], max_weight=6,
                           weight=attrgetter('weight'),
                           kind=attrgetter('typology')))
        self.assertEqual(list(map(len, blocks)), [2, 2, 1])
        self.assertEqual([b.weight for b in blocks], [2, 6, 4])

        blocks = list(
            split_in_blocks([s1, s2, s3, s4, s5], hint=6,
                            weight=attrgetter('weight'),
                            key=attrgetter('typology')))
        self.assertEqual(list(map(len, blocks)), [1, 1, 1, 2])
        self.assertEqual([b.weight for b in blocks], [2, 4, 4, 2])


class SearchModuleTestCase(unittest.TestCase):
    def test_existing_module_simple(self):
        self.assertIsNotNone(search_module('os'))

    def test_non_existing_module_simple(self):
        self.assertIsNone(search_module('do_not_exist'))

    def test_non_existing_module_in_package(self):
        self.assertIsNone(search_module('openquake.do_not_exist'))

    def test_existing_module_in_package(self):
        self.assertIsNotNone(search_module('openquake.baselib.general'))


class AssertCloseTestCase(unittest.TestCase):
    def test_different(self):
        a = [1, 2]
        b = [1, 2, 3]
        with self.assertRaises(AssertionError):  # different lenghts
            assert_close(a, b)

        with self.assertRaises(AssertionError):  # different floats
            assert_close([1, 2, 3.1], b)

        with self.assertRaises(AssertionError):  # None and float
            assert_close([1, 2, None], b)

        with self.assertRaises(AssertionError):  # nested dicts
            gmf1 = {'a': {'PGA': [0.1, 0.2], 'SA(0.1)': [0.3, 0.4]}}
            gmf2 = {'a': {'PGA': [0.1, 0.2], 'SA(0.1)': [0.3, 0.41]}}
            assert_close(gmf1, gmf2)

        class C(object):
            pass

        c1 = C()
        c2 = C()
        c2.a = 1
        with self.assertRaises(AssertionError):  # different attributes
            assert_close(c1, c2)


class DeprecatedTestCase(unittest.TestCase):
    def test(self):
        @deprecated('Use dummy_new instead.')
        def dummy():
            pass

        # check that a DeprecationWarning is printed
        with mock.patch('warnings.warn') as warn:
            dummy()
        warning_msg, warning_type = warn.call_args[0]
        self.assertIs(warning_type, DeprecationWarning)
        self.assertIn(
            'general_test.dummy has been deprecated. Use dummy_new instead.',
            warning_msg)

        # check that at the second call the warning is not printed
        with mock.patch('warnings.warn') as warn:
            dummy()
        self.assertIsNone(warn.call_args)
