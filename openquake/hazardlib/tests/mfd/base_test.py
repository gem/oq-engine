# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest

from openquake.hazardlib.mfd.base import BaseMFD


class BaseMFDTestCase(unittest.TestCase):
    class BaseTestMFD(BaseMFD):
        MODIFICATIONS = set()
        check_constraints_call_count = 0

        def check_constraints(self):
            self.check_constraints_call_count += 1

        def get_annual_occurrence_rates(self):
            pass

        def get_min_max_mag(self):
            pass

    def assert_mfd_error(self, func, *args, **kwargs):
        with self.assertRaises(ValueError) as exc_catcher:
            func(*args, **kwargs)
        return exc_catcher.exception


class BaseMFDModificationsTestCase(BaseMFDTestCase):
    def test_modify_missing_method(self):
        class TestMFD(self.BaseTestMFD):
            MODIFICATIONS = ('foo', 'bar')
        mfd = TestMFD()
        exc = self.assert_mfd_error(mfd.modify, 'baz', {})
        self.assertEqual(
            str(exc), 'Modification baz is not supported by TestMFD')

    def test_modify(self):
        class TestMFD(self.BaseTestMFD):
            MODIFICATIONS = ('foo', )
            foo_calls = []

            def modify_foo(self, **kwargs):
                self.foo_calls.append(kwargs)

        mfd = TestMFD()
        self.assertEqual(mfd.check_constraints_call_count, 0)
        mfd.modify('foo', dict(a=1, b='2', c=True))
        self.assertEqual(mfd.foo_calls, [{'a': 1, 'b': '2', 'c': True}])
        self.assertEqual(mfd.check_constraints_call_count, 1)
        self.assertEqual(str(mfd), "<TestMFD>")
