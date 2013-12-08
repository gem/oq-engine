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
Unit tests for the utils.tasks module.
"""

import unittest

from openquake.engine.utils import tasks

from tests.utils.tasks import failing_task, just_say_hello


class MapReduceTestCase(unittest.TestCase):
    """
    Tests the behaviour of utils.tasks.map_reduce and utils.tasks.parallelize
    """

    def test_single_item(self):
        expected = ["hello"] * 5
        result = tasks.map_reduce(
            just_say_hello, [(i, ) for i in range(5)],
            lambda lst, val: lst + [val], [])
        self.assertEqual(expected, result)

    def test_type_error(self):
        try:
            tasks.map_reduce(just_say_hello, range(5),
                             lambda lst, val: lst + [val], [])
        except TypeError as exc:
            # the message depend on the OQ_NO_DISTRIBUTE flag
            self.assertIn('int', str(exc))
        else:
            raise Exception("Exception not raised.")

    def test_failing_subtask(self):
        try:
            tasks.parallelize(failing_task, [(42, )], None)
        except NotImplementedError as exc:
            self.assertEqual(42, exc.args[0])
        else:
            raise Exception("Exception not raised.")

    def test_parallelize(self):
        lst = []
        res = tasks.parallelize(just_say_hello, [(i, ) for i in range(5)],
                                lst.append)
        self.assertEqual(res, None)
        self.assertEqual(lst, ['hello'] * 5)
