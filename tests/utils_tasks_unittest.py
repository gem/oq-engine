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

import mock
import unittest
import time
import uuid

from openquake import engine
from openquake.utils import tasks
from openquake.db.models import model_equals
from openquake.db.models import OqCalculation

from tests.utils.helpers import demo_file
from tests.utils.helpers import patch
from tests.utils.helpers import TestStore
from tests.utils.tasks import (
    failing_task, ignore_result, just_say_hello, reflect_args,
    reflect_data_to_be_processed, single_arg_called_a,
    reflect_data_with_task_index)

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
    """Tests the behaviour of utils.tasks.distribute()."""

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
        except Exception, exc:
            self.assertEqual(
                "single_arg_called_a() got an unexpected keyword argument "
                "'data'",
                exc.args[0])
        else:
            raise Exception("Exception not raised.")

    def test_distribute_with_type_error_and_no_exception_msg(self):
        """
        Exceptions without error messages should not result in another
        exception when being reraised.
        """
        from celery.result import TaskSetResult
        try:
            with patch('celery.task.sets.TaskSet.apply_async') as m2:
                m2.return_value = mock.Mock(spec=TaskSetResult)
                m2.return_value.join_native.side_effect = TypeError
                tasks.distribute(2, single_arg_called_a, ("a", range(5)))
        except Exception, exc:
            self.assertEqual((), exc.args)
        else:
            raise Exception("Exception not raised.")

    def test_distribute_with_failing_subtask(self):
        """At least one subtask failed, a `TaskFailed` exception is raised."""
        try:
            tasks.distribute(1, failing_task, ("data", range(5)))
        except Exception, exc:
            self.assertEqual(range(5), exc.args[0])
        else:
            raise Exception("Exception not raised.")

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


class ParallelizeTestCase(unittest.TestCase):
    """Tests the behaviour of utils.tasks.parallelize()."""

    def __init__(self, *args, **kwargs):
        super(ParallelizeTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_parallelize_uses_the_specified_number_of_subtasks(self):
        """The specified number of subtasks is actually spawned."""
        expected = ["hello"] * 5
        result = tasks.parallelize(
            5, just_say_hello, dict(), index_tasks=False)
        self.assertEqual(expected, result)

    def test_parallelize_with_params(self):
        """All subtasks are invoked with the same parameters."""
        # The keyword arguments below will be passed to *all* celery subtasks.
        args = {"1+1": 2, "2/1": 1}

        # We expect the subtasks to see the following positional and keyword
        # arguments respectively.
        expected = [
            ((), {"1+1": 2, "2/1": 1}), ((), {"1+1": 2, "2/1": 1})]

        # Two subtasks will be spawned and just return the arguments they
        # received.
        result = tasks.parallelize(2, reflect_args, args, index_tasks=False)
        # Remove celery-injected keyword arguments.
        actual = []
        for args, kwargs in result:
            actual.append((args, actual_kwargs(kwargs)))
        self.assertEqual(expected, actual)

    def test_parallelize_with_argument_not_expected_by_task(self):
        """
        An unexpected argument is passed to the subtask triggering a
        `TypeError` exception.
        """
        try:
            tasks.parallelize(2, single_arg_called_a, dict(data=range(5)),
            index_tasks=False)
        except Exception, exc:
            self.assertEqual(
                "single_arg_called_a() got an unexpected keyword argument "
                "'data'",
                exc.args[0])
        else:
            raise Exception("Exception not raised.")

    def test_parallelize_with_failing_subtask(self):
        """At least one subtask failed, a `TaskFailed` exception is raised."""
        try:
            tasks.parallelize(1, failing_task, dict(data=range(5)),
            index_tasks=False)
        except Exception, exc:
            self.assertEqual(range(5), exc.args[0])
        else:
            raise Exception("Exception not raised.")

    def test_parallelize_returns_correct_results(self):
        """Correct results are returned."""
        expected = [range(3)] * 3
        result = tasks.parallelize(
            3, reflect_data_to_be_processed, dict(data=range(3)),
            index_tasks=False)
        self.assertEqual(expected, result)

    def test_parallelize_returns_flattened_and_correct_results(self):
        """Flattened and correct results are returned."""
        expected = range(3) * 3
        result = tasks.parallelize(
            3, reflect_data_to_be_processed, dict(data=range(3)),
            flatten_results=True, index_tasks=False)
        self.assertEqual(expected, result)

    def test_parallelize_with_params_and_task_index(self):
        """
        All subtasks are invoked with the same parameters but will receive a
        task index parameter.
        """
        # The keyword arguments below will be passed to *all* celery subtasks.
        args = {"1+1": 2, "2/1": 1}

        # We expect the subtasks to see the following positional and keyword
        # arguments respectively.
        expected = [
            ((), {"1+1": 2, "2/1": 1, "task_index": 0}),
            ((), {"1+1": 2, "2/1": 1, "task_index": 1})]

        # Two subtasks will be spawned and just return the arguments they
        # received.
        result = tasks.parallelize(2, reflect_args, args)
        # Remove celery-injected keyword arguments.
        actual = []
        for args, kwargs in result:
            actual.append((args, actual_kwargs(kwargs)))
        self.assertEqual(expected, actual)

    def test_parallelize_returns_results_in_the_right_order(self):
        """Results are returned in the right order."""
        expected = [[5, 6, 0], [5, 6, 1], [5, 6, 2]]
        result = tasks.parallelize(
            3, reflect_data_with_task_index, dict(data=range(5, 7)))
        self.assertEqual(expected, result)

    def test_parallelize_with_params_not_passed_in_dict(self):
        """The task parameters must be passed in a dictionary."""
        try:
            tasks.parallelize(3, reflect_data_with_task_index, range(5, 7))
        except AssertionError, exc:
            self.assertEqual(
                "Parameters must be passed in a dict.", exc.args[0])
        else:
            raise Exception("Exception not raised.")


class GetRunningCalculationTestCase(unittest.TestCase):
    """Tests for :function:`openquake.utils.tasks.get_running_calculation`."""

    def setUp(self):
        self.job_profile, self.params, _sections = (
            engine.import_job_profile(demo_file(
                'simple_fault_demo_hazard/config.gem')))

        self.params['debug'] = 'warn'

        self.calculation = OqCalculation(
            owner=self.job_profile.owner,
            oq_job_profile=self.job_profile)
        self.calculation.save()

        # Cache the calc proxy data into the kvs:
        calc_proxy = engine.CalculationProxy(
            self.params, self.calculation.id, oq_job_profile=self.job_profile,
            oq_calculation=self.calculation)
        calc_proxy.to_kvs()

    def test_get_running_calculation(self):
        self.calculation.status = 'pending'
        self.calculation.save()

        # No 'JobCompletedError' should be raised.
        calc_proxy = tasks.get_running_calculation(self.calculation.id)

        self.assertEqual(self.params, calc_proxy.params)
        self.assertTrue(model_equals(
            self.job_profile, calc_proxy.oq_job_profile,
            ignore=('_owner_cache',)))
        self.assertTrue(model_equals(
            self.calculation, calc_proxy.oq_calculation,
            ignore=('_owner_cache',)))

    def test_get_completed_calculation(self):
        self.calculation.status = 'succeeded'
        self.calculation.save()

        try:
            tasks.get_running_calculation(self.calculation.id)
        except tasks.JobCompletedError as exc:
            self.assertEqual(exc.message, self.calculation.id)
        else:
            self.fail("JobCompletedError wasn't raised")

    def test_completed_failure(self):
        self.calculation.status = 'failed'
        self.calculation.save()

        try:
            tasks.get_running_calculation(self.calculation.id)
        except tasks.JobCompletedError as exc:
            self.assertEqual(exc.message, self.calculation.id)
        else:
            self.fail("JobCompletedError wasn't raised")


class IgnoreResultsTestCase(unittest.TestCase):
    """
    Tests the behaviour of utils.tasks.distribute() with tasks whose results
    are ignored.
    """

    def __init__(self, *args, **kwargs):
        super(IgnoreResultsTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        # Make sure we have no obsolete test data in the kvs.
        kvs = TestStore.kvs()
        existing_data = kvs.keys("irtc:*")
        if existing_data:
            kvs.delete(*existing_data)

    def test_distribute_with_ignore_result_set(self):
        """
        The specified number of subtasks is actually spawned even for tasks
        with ignore_result=True and these run and complete.

        Since the results of the tasks are ignored, the only way to know that
        they ran and completed is to verify that the data they were supposed
        to write the key value store is actually there.
        """

        def value(key):
            """Construct a test value for the given key."""
            return key[-3:] * 2

        keys = ["irtc:%s" % str(uuid.uuid4())[:8] for _ in xrange(5)]
        values = [value(uid) for uid in keys]
        data = zip(keys, values)

        result = tasks.distribute(5, ignore_result, ("data", data))
        # An empty list is returned for tasks with ignore_result=True
        # and no asynchronous task handler function.
        self.assertEqual(False, bool(result))

        # Give the tasks a bit of time to complete.
        time.sleep(0.1)

        for key, value in data:
            self.assertEqual(value, TestStore.get(key))

    def test_distribute_with_ignore_result_set_and_ath(self):
        """
        The specified number of subtasks is actually spawned (even for tasks
        with ignore_result=True) and the asynchronous task handler function is
        run.
        """

        def value(key):
            """Construct a test value for the given key."""
            return key[-3:] * 2

        def ath(data):
            """
            An asynchronous task handler function that converts all task
            results to upper case and returns the list of keys found.
            """
            items_expected = len(data)
            items_found = []
            while len(items_found) < items_expected:
                for key, _ in data:
                    if key in items_found:
                        continue
                    value = TestStore.get(key)
                    if value is not None:
                        TestStore.set(key, value.upper())
                        items_found.append(key)
                time.sleep(0.05)
            return items_found

        keys = ["irtc:%s" % str(uuid.uuid4())[:8] for _ in xrange(5)]
        values = [value(uid) for uid in keys]
        data = zip(keys, values)

        result = tasks.distribute(5, ignore_result, ("data", data), ath=ath)
        self.assertEqual(sorted(keys), sorted(result))

        for key, value in data:
            self.assertEqual(value.upper(), TestStore.get(key))


class PrepareKwargsTestCase(unittest.TestCase):
    """
    Tests the behaviour of utils.tasks._prepare_kwargs().
    """

    def test_prepare_kwargs_with_data_only(self):
        """Simplest case: no other args and no function passed"""
        self.assertEqual(dict(a=1), tasks._prepare_kwargs("a", 1, None))

    def test_prepare_kwargs_with_other_data(self):
        """Pass `other_args` that is not `None`."""
        self.assertEqual(dict(a=1, c=3, d=4),
                         tasks._prepare_kwargs("a", 1, dict(c=3, d=4)))

    def test_prepare_kwargs_with_data_only_and_func_params_mismatch(self):
        """A function is passed, its params do not match."""

        def ath(x):
            pass

        self.assertEqual(dict(), tasks._prepare_kwargs("a", 1, None, ath))

    def test_prepare_kwargs_with_data_only_and_func_params_match(self):
        """A function is passed, its params *do* match."""

        def ath(a):
            pass

        self.assertEqual(dict(a=1), tasks._prepare_kwargs("a", 1, None, ath))

    def test_prepare_kwargs_with_func_params_mismatch(self):
        """
        Other args and a function is passed, the latter's params do not match.
        """

        def ath(x):
            pass

        self.assertEqual(dict(),
                         tasks._prepare_kwargs("a", 1, dict(c=3, d=4), ath))

    def test_prepare_kwargs_with_func_params_match(self):
        """
        Other args and a function is passed, the latter's params *do* match.
        """

        def ath(a, d):
            pass

        self.assertEqual(dict(a=1, d=4),
                         tasks._prepare_kwargs("a", 1, dict(c=3, d=4), ath))

    def test_prepare_kwargs_with_full_func_params_match(self):
        """
        Other args and a function is passed, the latter's params all match.
        """

        def ath(a, c, d):
            pass

        self.assertEqual(dict(a=1, c=3, d=4),
                         tasks._prepare_kwargs("a", 1, dict(c=3, d=4), ath))


class CalculatorForTaskTestCase(unittest.TestCase):
    """Tests for :function:`openquake.utils.tasks.calculator_for_task`."""

    def test_calculator_for_task(self):
        """Load up a sample calculation (into the db and cache) and make sure
        we can instantiate the correct calculator for a given calculation id.
        """
        from openquake.calculators.hazard.classical.core import ClassicalMixin
        job_profile, params, sections = engine.import_job_profile(demo_file(
            'simple_fault_demo_hazard/config.gem'))

        calculation = OqCalculation(owner=job_profile.owner,
                                    oq_job_profile=job_profile)
        calculation.save()

        calc_proxy = engine.CalculationProxy(params, calculation.id,
                                             oq_job_profile=job_profile,
                                             oq_calculation=calculation)
        calc_proxy.to_kvs()

        with patch(
            'openquake.utils.tasks.get_running_calculation') as grc_mock:

            # Loading of the CalculationProxy is done by
            # `get_running_calculation`, which is covered by other tests.
            # So, we just want to make sure that it's called here.
            grc_mock.return_value = calc_proxy

            calculator = tasks.calculator_for_task(calculation.id, 'hazard')

            self.assertTrue(isinstance(calculator, ClassicalMixin))
            self.assertEqual(1, grc_mock.call_count)
