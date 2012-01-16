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

from tests.utils import helpers


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


class FlagSetTestCase(helpers.ConfigTestMixin, unittest.TestCase):
    """
    Tests for openquake.utils.general.flag_set()
    """

    def setUp(self):
        self.setup_config()

    def tearDown(self):
        self.teardown_config()

    def test_flag_set_with_absent_key(self):
        """
        flag_set() returns False if the setting
        is not present in the configuration file.
        """
        self.prepare_config("a")
        self.assertFalse(general.flag_set("a", "z"))

    def test_flag_set_with_number(self):
        """
        flag_set() returns False if the setting is present but
        not equal to 'true'.
        """
        self.prepare_config("b", {"y": "123"})
        self.assertFalse(general.flag_set("b", "y"))

    def test_flag_set_with_text_but_not_true(self):
        """
        flag_set() returns False if the setting is present but
        not equal to 'true'.
        """
        self.prepare_config("c", {"x": "blah"})
        self.assertFalse(general.flag_set("c", "x"))

    def test_flag_set_with_true(self):
        """
        flag_set() returns True if the setting is present and equal to 'true'.
        """
        self.prepare_config("d", {"w": "true"})
        self.assertTrue(general.flag_set("d", "w"))

    def test_flag_set_with_True(self):
        """
        flag_set() returns True if the setting is present and equal to 'true'.
        """
        self.prepare_config("e", {"v": " True 	 "})
        self.assertTrue(general.flag_set("e", "v"))


class AdHocObjectTestCase(unittest.TestCase):
    """
    Tests for the openquake.utils.general.AdHocObject class.
    """

    def test_init_with_no_default_or_data(self):
        """All properties should be initialized with `None`."""
        aho = general.AdHocObject("Test1", "a b c".split())
        self.assertEqual(dict(a=None, b=None, c=None), aho._ia_data)

    def test_init_with_no_default_but_with_data(self):
        """All properties should be initialized with the data supplied."""
        aho = general.AdHocObject("Test1", "d e f".split(), range(1, 4))
        self.assertEqual(dict(d=1, e=2, f=3), aho._ia_data)

    def test_init_with_a_default_but_no_data(self):
        """All properties should be initialized with the default supplied."""
        aho = general.AdHocObject("Test1", "g h i".split(), default=-1)
        self.assertEqual(dict(g=-1, h=-1, i=-1), aho._ia_data)

    def test_get_property_access_with_existing(self):
        """Getting for a predefined property works."""
        aho = general.AdHocObject("Test1", "j k".split(), default=-2)
        self.assertEqual(-2, aho.j)

    def test_get_property_access_non_existent(self):
        """An attempt to get a missing property raises `AttributeError`."""
        aho = general.AdHocObject("Test1", "l".split(), default=-3)
        try:
            aho.k
        except AttributeError:
            pass
        else:
            self.fail("AttributeError not raised for non-existent property.""")

    def test_set_property_access_with_existing(self):
        """Setting a predefined property works."""
        aho = general.AdHocObject("Test1", "m n".split(), default=-4)
        aho.m = -5
        self.assertEqual(-5, aho.m)

    def test_set_property_access_non_existent(self):
        """An attempt to set a missing property raises `AttributeError`."""
        aho = general.AdHocObject("Test1", "o".split(), default=-6)
        try:
            aho.n = -7
        except AttributeError:
            pass
        else:
            self.fail("AttributeError not raised for non-existent property.""")

    def test_equality_with_same_data(self):
        """Two `AdHocObject` instances with the same data are equal."""
        aho1 = general.AdHocObject("Test1", "p q".split(), default=-8)
        aho2 = general.AdHocObject("Test1", "p q".split(), default=-8)
        self.assertEqual(aho1, aho2)

    def test_equality_with_different_data(self):
        """Two `AdHocObject` instances with different data are not equal."""
        aho1 = general.AdHocObject("Test1", "r s".split(), default=-9)
        aho2 = general.AdHocObject("Test1", "r s".split(), default=-10)
        self.assertNotEqual(aho1, aho2)

    def test_non_equality_with_same_data(self):
        """Two `AdHocObject` instances with the same data are equal."""
        aho1 = general.AdHocObject("Test1", "t u".split(), default=-8)
        aho2 = general.AdHocObject("Test1", "t u".split(), default=-8)
        self.assertFalse(aho1 != aho2)

    def test_non_equality_with_different_data(self):
        """Two `AdHocObject` instances with different data are not equal."""
        aho1 = general.AdHocObject("Test1", "v w".split(), default=-9)
        aho2 = general.AdHocObject("Test1", "v w".split(), default=-10)
        self.assertTrue(aho1 != aho2)

    def test_iter(self):
        """The iterator returned yields all the data."""
        aho = general.AdHocObject("Test1", "x y".split(), [-11, -12])
        self.assertEqual(sorted([('y', -12), ('x', -11)]),
                         sorted(list(iter(aho))))
