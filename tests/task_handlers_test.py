# -*- coding: utf-8 -*-
# unittest.TestCase base class does not honor the following coding
# convention
# pylint: disable=C0103,R0904

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
Test task queue handling with OO interface.
"""

import unittest
import random
from openquake.utils import task_handlers


class DummyTask():
    """
    Just a dummy task that stores a field and returns it
    """
    def __init__(self, arg):
        self.arg = arg

    def run(self):
        """
        Just return a field
        """
        return self.arg


class DummyTaskThatFail():
    def run(self):
        """
        It will fail
        """
        raise RuntimeError("Expected fail")


class SimpleTaskHandlerTestCase(unittest.TestCase):
    """
    Test simple task queue OO interface
    """
    def setUp(self):
        self.task_cls = DummyTask
        self.task_handler = task_handlers.SimpleTaskHandler()

    def test_apply_async(self):
        a_number = random.random()
        self.task_handler.enqueue(self.task_cls, a_number)
        self.task_handler.apply_async()
        ret = self.task_handler.wait_for_results()
        self.assertEqual([a_number], list(ret))

    def test_sequential_enqueue(self):
        a_number = random.random()
        another_number = random.random()
        self.task_handler.enqueue(self.task_cls, a_number)
        self.task_handler.enqueue(self.task_cls, another_number)
        self.task_handler.apply_async()
        ret = self.task_handler.wait_for_results()
        self.assertEqual([a_number, another_number], list(ret))

    def test_fail_sync(self):
        self.task_handler.enqueue(DummyTaskThatFail)
        try:
            ret = self.task_handler.apply()
            self.assertEqual(ret.successful(), False)
        except RuntimeError:
            self.assertTrue(True)

    def test_apply(self):
        a_number = random.random()
        self.task_handler.enqueue(self.task_cls, a_number)
        ret = self.task_handler.apply()
        self.assertEqual([a_number], list(ret))


class CeleryTaskHandlerTestCase(SimpleTaskHandlerTestCase):
    """
    Inherit tests from simple task handler but use celery.
    Requires a celery server up and running
    """
    def setUp(self):
        self.task_cls = DummyTask
        self.task_handler = task_handlers.CeleryTaskHandler()
