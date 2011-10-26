# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
Test related to code in openquake/utils/general.py
"""


import unittest

from openquake.utils import general


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


class MemoizerTestCase(unittest.TestCase):
    """Tests the behaviour of utils.general.MemoizeMutable"""

    def setUp(self):
        self.counter = 0

    def test_unashable_types(self):
        """ Tests 'unhashable' types like dict, lists """

        @general.MemoizeMutable
        def my_memoized_method(*args, **kwargs):
            """ the memoized decorated method """
            self.counter += 1
            return self.counter

        # not cached
        my_memoized_method([1, 2, 3],
                           {'key1': 'value1', 'key2': 'value2'})

        # cached with return values
        self.assertEqual(1, my_memoized_method([1, 2, 3],
                           {'key1': 'value1', 'key2': 'value2'}))

        # should be called only one time
        self.assertEqual(self.counter, 1)

    def test_memoizer(self):
        """ Tests the caching of 'normal' types """

        @general.MemoizeMutable
        def my_memoized_method(mystring, myint):
            """ the memoized decorated method """
            self.counter += 1
            return self.counter

        # not cached
        my_memoized_method('bla', 1)

        # cached with return values
        self.assertEqual(1, my_memoized_method('bla', 1))

        # should be called only one time
        self.assertEqual(self.counter, 1)


class Str2intTestCase(unittest.TestCase):
    """Tests the behaviour of utils.general.str2int()"""

    def test_with_none(self):
        """str2int() raises `ValueError` when called with `None`."""
        self.assertRaises(ValueError, general.str2int, None)

    def test_with_empty_string(self):
        """str2int() raises `ValueError` when called with an empty string."""
        self.assertRaises(ValueError, general.str2int, "")

    def test_with_whitespace(self):
        """str2int() raises `ValueError` when called with whitespace only."""
        self.assertRaises(ValueError, general.str2int, " 	")

    def test_with_non_number(self):
        """str2int() raises `ValueError` when called with non-numeric text."""
        self.assertRaises(ValueError, general.str2int, "hello!")

    def test_with_whitespace_and_number(self):
        """str2int() tolerates whitespace-wrapped numbers."""
        self.assertEqual(331, general.str2int("  331  "))

    def test_with_number(self):
        """str2int() returns the number contained in the string."""
        self.assertEqual(-11, general.str2int("-11"))
