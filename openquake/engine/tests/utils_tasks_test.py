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
Unit tests for the utils.tasks module.
"""

import unittest

from openquake.engine.utils import tasks

from openquake.engine.tests.utils.tasks import \
    failing_task, just_say_hello, get_even


class TaskManagerTestCase(unittest.TestCase):
    """
    Tests the behaviour of utils.tasks.map_reduce and apply_reduce
    """

    def test_single_item(self):
        expected = ["hello"] * 5
        tm = tasks.OqTaskManager.starmap(
            just_say_hello, [(i, ) for i in range(5)])
        result = tm.reduce(lambda lst, val: lst + [val], [])
        self.assertEqual(expected, result)

    def test_type_error(self):
        try:
            tasks.OqTaskManager.starmap(just_say_hello, range(5))
        except TypeError as exc:
            # the message depend on the OQ_NO_DISTRIBUTE flag
            # "submit() argument after * must be a sequence, not int"
            self.assertIn('int', str(exc))
        else:
            raise Exception("Exception not raised.")

    def test_failing_subtask(self):
        try:
            tasks.apply_reduce(failing_task, ('job_id', [42]),
                               agg=lambda a, x: x)
        except NotImplementedError:
            pass  # expected
        else:
            raise Exception("Exception not raised.")

    def test_apply_reduce(self):
        got = tasks.apply_reduce(
            get_even, (1, [1, 2, 3, 4, 5]), list.__add__, [], 2)
        self.assertEqual(sorted(got), [2, 4])
