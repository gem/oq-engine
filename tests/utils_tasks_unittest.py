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
Unit tests for the utils.tasks module.
"""

import unittest

from openquake.utils import tasks

from tests.utils.tasks import (
    failing_task, just_say_hello, reflect_args, reflect_data_to_be_processed,
    single_arg_called_a)

# The keyword args below are injected by the celery framework.
celery_injected_kwargs = set((
    "delivery_info", "logfile", "loglevel", "task_id", "task_is_eager",
    "task_name", "task_retries"))


def actual_kwargs(kwargs):
    """Filter the keyword arguments injected by celery.

    :param dict kwargs: The keyword arguments thrown back by a celery task.
    :returns: The keyword arguments that were actually passed.
    :rtype: dict
    """
    filtered_args = []
    for k, v in kwargs.iteritems():
        if k not in celery_injected_kwargs:
            filtered_args.append((k, v))
    return dict(filtered_args)


class DistributeTestCase(unittest.TestCase):
    """Tests the behaviour of tasks.distribute()."""

    def __init__(self, *args, **kwargs):
        super(DistributeTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_distribute_uses_the_specified_number_of_subtasks(self):
        """The specified number of subtasks is actually spawned."""
        expected = ["hello"] * 5
        result = tasks.distribute(5, just_say_hello, ("data", range(5)))
        self.assertEqual(expected, result)

    def test_distribute_with_no_other_args(self):
        """The subtask is only invoked with the data to be processed."""
        # We expect the subtasks to see no positional arguments. The
        # data to be processed is passed in the keyword arguments.
        expected = [
            ((), {"data_to_process": [100]}),
            ((), {"data_to_process": [101]})]
        actual = []
        result = tasks.distribute(
            2, reflect_args, ("data_to_process", [100, 101]))
        # Remove celery-injected keyword arguments.
        for args, kwargs in result:
            actual.append((args, actual_kwargs(kwargs)))
        self.assertEqual(expected, actual)

    def test_distribute_with_other_args(self):
        """
        The subtask is invoked with the data to be processed as well as with
        other parameters.
        """
        # The keyword arguments below will be passed to the celery subtasks in
        # addition to the data that is to be processed.
        other_args = {"1+1": 2, "2/1": 1}

        # We expect the subtasks to see the following positional and keyword
        # arguments respectively.
        expected = [
            ((), {"data_to_process": [88], "1+1": 2, "2/1": 1}),
            ((), {"data_to_process": [99], "1+1": 2, "2/1": 1})]
        actual = []

        # Two subtasks will be spawned and just return the arguments they
        # received.
        result = tasks.distribute(
            2, reflect_args, ("data_to_process", [88, 99]),
            other_args=other_args)
        # Remove celery-injected keyword arguments.
        for args, kwargs in result:
            actual.append((args, actual_kwargs(kwargs)))
        self.assertEqual(expected, actual)

    def test_distribute_with_empty_data_and_cardinality_one(self):
        """A *single* subtask will be spawned even with an empty data set."""
        expected = ((), {"data_to_process": []})
        [(args, kwargs)] = tasks.distribute(
            1, reflect_args, ("data_to_process", []))
        self.assertEqual(expected, (args, actual_kwargs(kwargs)))

    def test_distribute_with_non_empty_data_and_cardinality_one(self):
        """A single subtask will receive all the data to be processed."""
        expected = ((), {"data_to_process": range(5)})
        [(args, kwargs)] = tasks.distribute(
            1, reflect_args, ("data_to_process", range(5)))
        self.assertEqual(expected, (args, actual_kwargs(kwargs)))

    def test_distribute_with_even_data_and_cardinality_above_one(self):
        """The data set divides evenly among the subtasks in the task set."""
        expected = (
            (), {"data_to_process": range(2)},
            (), {"data_to_process": range(2, 4)})
        [(args1, kwargs1), (args2, kwargs2)] = tasks.distribute(
            2, reflect_args, ("data_to_process", range(4)))
        self.assertEqual(
            expected,
            (args1, actual_kwargs(kwargs1), args2, actual_kwargs(kwargs2)))

    def test_distribute_with_noneven_data_and_cardinality_above_one(self):
        """
        The data set does *not* divide evenly among the subtasks in the task
        set. The last subtask gets all the remaining data.
        """
        expected = (
            (), {"data_to_process": range(2)},
            (), {"data_to_process": range(2, 5)})
        [(args1, kwargs1), (args2, kwargs2)] = tasks.distribute(
            2, reflect_args, ("data_to_process", range(5)))
        self.assertEqual(
            expected,
            (args1, actual_kwargs(kwargs1), args2, actual_kwargs(kwargs2)))

    def test_distribute_with_keyword_argument_not_expected_by_task(self):
        """
        An unexpected keyword argument is passed to the subtask triggering a
        `TypeError` exception.
        """
        try:
            tasks.distribute(2, single_arg_called_a, ("data", range(5)))
        except tasks.WrongTaskParameters, exc:
            self.assertEqual(
                "single_arg_called_a() got an unexpected keyword argument "
                "'data'",
                exc.args[0])
        else:
            self.assertTrue(False, "Exception not raised")

    def test_distribute_with_failing_subtask(self):
        """At least one subtask failed, a `TaskFailed` exception is raised."""
        try:
            tasks.distribute(1, failing_task, ("data", range(5)))
        except tasks.TaskFailed, exc:
            self.assertEqual(range(5), exc.args[0])
        else:
            self.assertTrue(False, "Exception not raised")

    def test_distribute_with_too_little_data(self):
        """
        When the data to be processed is a list of N items and the specified
        cardinality was M where (N < M), only N subtasks are invoked.
        """
        expected = ["hello"] * 3
        result = tasks.distribute(5, just_say_hello, ("data", range(3)))
        self.assertEqual(expected, result)

    def test_distribute_returns_results_in_the_right_order(self):
        """Results are returned in the right order."""
        expected = [[0, 1], [2, 3], [4, 5, 6]]
        result = tasks.distribute(
            3, reflect_data_to_be_processed, ("data", range(7)))
        self.assertEqual(expected, result)

    def test_distribute_returns_flattened_results_in_right_order(self):
        """Flattened results are returned in the right order."""
        expected = range(7)
        result = tasks.distribute(
            3, reflect_data_to_be_processed, ("data", range(7)),
            flatten_results=True)
        self.assertEqual(expected, result)
