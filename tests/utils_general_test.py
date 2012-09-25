# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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

from openquake.utils import general
from openquake.utils.general import block_splitter


class SingletonTestCase(unittest.TestCase):
    """Tests the behaviour of utils.general.singleton()."""

    def test_singleton(self):
        """
        A class decorated with @singleton will always return the same
        instance upon creation.
        """

        @general.singleton
        class MySingleton(object):
            pass

        instance1 = MySingleton()
        instance2 = MySingleton()
        self.assertTrue(instance2 is instance1)
        instance3 = MySingleton()
        self.assertTrue(instance3 is instance1)


class BlockSplitterTestCase(unittest.TestCase):
    """Tests for :function:`openquake.utils.general.block_splitter`."""

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
