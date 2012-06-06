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

import mock
import unittest
import time
import uuid

from openquake import engine
from openquake.utils import tasks
from openquake.db.models import model_equals

from tests.utils.helpers import demo_file
from tests.utils.helpers import patch
from tests.utils.helpers import TestStore
from tests.utils.tasks import (
    failing_task, ignore_result, just_say_1, just_say_hello, reflect_args,
    reflect_data_to_be_processed, single_arg_called_a)


# The keyword args below are injected by the celery framework.
celery_injected_kwargs = set((
    "delivery_info", "logfile", "loglevel", "task_id", "task_is_eager",
    "task_name", "task_retries"))


class DistributeTestCase(unittest.TestCase):
    """Tests the behaviour of utils.tasks.distribute()."""

    def test_distribute_uses_the_specified_number_of_subtasks(self):
        """One subtasks per data item is actually spawned."""
        expected = ["hello"] * 5
        result = tasks.distribute(just_say_hello, ("data", range(5)))
        self.assertEqual(expected, result)

    def test_distribute_with_task_returning_single_item(self):
        """distribute() copes with tasks that return a single item."""
        expected = [1] * 5
        result = tasks.distribute(just_say_1, ("data", range(5)))
        self.assertEqual(expected, result)

    def test_distribute_with_no_other_args(self):
        """The subtask is only invoked with the data to be processed."""
        # We expect the subtasks to see no positional arguments. The
        # data to be processed is passed in the keyword arguments.
        expected = [
            (), {"data_to_process": 11}, (), {"data_to_process": 12}]
        result = tasks.distribute(reflect_args, ("data_to_process", [11, 12]),
                                  flatten_results=True)
        self.assertEqual(expected, result)

    def test_distribute_with_other_args(self):
        """
        The subtask is invoked with the data to be processed as well as with
        other parameters.
        """
        # The keyword arguments below will be passed to the celery subtasks in
        # addition to the data that is to be processed.
        tf_args = {"1+1": 2, "2/1": 1}

        # We expect the subtasks to see the following positional and keyword
        # arguments respectively.
        expected = [
            ((), {"data_to_process": [13], "1+1": 2, "2/1": 1}),
            ((), {"data_to_process": [14], "1+1": 2, "2/1": 1})]

        # Two subtasks will be spawned and just return the arguments they
        # received.
        result = tasks.distribute(reflect_args,
                                  ("data_to_process", [[13], [14]]),
                                  tf_args=tf_args)
        self.assertEqual(expected, result)

    def test_distribute_with_keyword_argument_not_expected_by_task(self):
        """
        An unexpected keyword argument is passed to the subtask triggering a
        `TypeError` exception.
        """
        try:
            tasks.distribute(single_arg_called_a, ("data", range(5)))
        except Exception, exc:
            self.assertEqual(
                "single_arg_called_a() got an unexpected keyword argument "
                "'data'", exc.args[0])
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
                tasks.distribute(single_arg_called_a, ("a", range(5)))
        except Exception, exc:
            self.assertEqual((), exc.args)
        else:
            raise Exception("Exception not raised.")

    def test_distribute_with_failing_subtask(self):
        """At least one subtask failed, a `TaskFailed` exception is raised."""
        try:
            tasks.distribute(failing_task, ("data", range(5)))
        except Exception, exc:
            # The exception is raised by the first task.
            self.assertEqual(0, exc.args[0])
        else:
            raise Exception("Exception not raised.")

    def test_distribute_returns_results_in_right_order_when_flattened(self):
        """Results are returned in the right order when flattened."""
        expected = range(7)
        result = tasks.distribute(reflect_data_to_be_processed,
                                  ("data", range(7)), flatten_results=True)
        self.assertEqual(expected, result)

    def test_distribute_returns_results_wo_flattening(self):
        """Results are returned in the right order."""
        expected = [[i] for i in range(7)]
        result = tasks.distribute(reflect_data_to_be_processed,
                                  ("data", [[i] for i in range(7)]))
        self.assertEqual(expected, result)


class GetRunningCalculationTestCase(unittest.TestCase):
    """Tests for :function:`openquake.utils.tasks.get_running_job`."""

    def setUp(self):
        self.job = engine.prepare_job()
        self.job_profile, self.params, _sections = (
            engine.import_job_profile(demo_file(
                'simple_fault_demo_hazard/config.gem'), self.job))

        self.params['debug'] = 'warn'

        # Cache the calc proxy data into the kvs:
        job_ctxt = engine.JobContext(
            self.params, self.job.id, oq_job_profile=self.job_profile,
            oq_job=self.job)
        job_ctxt.to_kvs()

    def test_get_running_job(self):
        self.job.status = 'pending'
        self.job.save()

        # No 'JobCompletedError' should be raised.
        job_ctxt = tasks.get_running_job(self.job.id)

        self.assertEqual(self.params, job_ctxt.params)
        self.assertTrue(model_equals(
            self.job_profile, job_ctxt.oq_job_profile,
            ignore=('_owner_cache',)))
        self.assertTrue(model_equals(
            self.job, job_ctxt.oq_job,
            ignore=('_owner_cache',)))

    def test_get_completed_calculation(self):
        self.job.status = 'succeeded'
        self.job.save()

        try:
            tasks.get_running_job(self.job.id)
        except tasks.JobCompletedError as exc:
            self.assertEqual(exc.message, self.job.id)
        else:
            self.fail("JobCompletedError wasn't raised")

    def test_completed_failure(self):
        self.job.status = 'failed'
        self.job.save()

        try:
            tasks.get_running_job(self.job.id)
        except tasks.JobCompletedError as exc:
            self.assertEqual(exc.message, self.job.id)
        else:
            self.fail("JobCompletedError wasn't raised")


class IgnoreResultsTestCase(unittest.TestCase):
    """
    Tests the behaviour of utils.tasks.distribute() with tasks whose results
    are ignored.
    """
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

        result = tasks.distribute(ignore_result, ("data", [[d] for d in data]))
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

        args = ("data", [[d] for d in data])
        result = tasks.distribute(ignore_result, args, ath=ath,
                                  ath_args=dict(data=data))
        self.assertEqual(sorted(keys), sorted(result))

        for key, value in data:
            self.assertEqual(value.upper(), TestStore.get(key))


class CalculatorForTaskTestCase(unittest.TestCase):
    """Tests for :function:`openquake.utils.tasks.calculator_for_task`."""

    def test_calculator_for_task(self):
        """Load up a sample calculation (into the db and cache) and make sure
        we can instantiate the correct calculator for a given calculation id.
        """
        from openquake.calculators.hazard.classical.core import (
            ClassicalHazardCalculator)
        job = engine.prepare_job()
        job_profile, params, sections = engine.import_job_profile(demo_file(
            'simple_fault_demo_hazard/config.gem'), job)

        job_ctxt = engine.JobContext(params, job.id,
                                             oq_job_profile=job_profile,
                                             oq_job=job)
        job_ctxt.to_kvs()

        with patch(
            'openquake.utils.tasks.get_running_job') as grc_mock:

            # Loading of the JobContext is done by
            # `get_running_job`, which is covered by other tests.
            # So, we just want to make sure that it's called here.
            grc_mock.return_value = job_ctxt

            calculator = tasks.calculator_for_task(job.id, 'hazard')

            self.assertTrue(isinstance(calculator, ClassicalHazardCalculator))
            self.assertEqual(1, grc_mock.call_count)
