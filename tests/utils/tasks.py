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
Task functions for our unit tests.
"""


from celery.decorators import task

from tests.utils import helpers

from openquake import java


@task
def test_data_reflector(job_id, *args, **kwargs):
    """Throw back the data stored in the KVS for the given `job_id`.

    This should be used for testing purposes only. The idea is to store the
    data expected in test setup and then use this task to play that data back
    to the test.

    See :py:class:`DoCurvesTestCase` for an example of how this task should be
    used.
    """
    return helpers.TestStore.lookup(job_id)


@task
def test_compute_hazard_curve(job_id, site_list, realization):
    """This task will be used to test :py:class`ClassicalMixin` code.

    The test setup code will prepare a result set for each `realization`.
    This task will fetch these canned result sets and throw them back
    simulating the real hazard curve calculator.

    See also :py:meth:`DoCurvesTestCase.do_curves`.
    """
    key = "%s/%s" % (job_id, realization + 1)
    return helpers.TestStore.lookup(key)


@task
def reflect_args(*args, **kwargs):
    """Merely returns the parameters received."""
    return (args, kwargs)


@task
def just_say_hello(*args, **kwargs):
    """Merely returns 'hello'."""
    return "hello"


@task
def single_arg_called_a(a):
    """Takes a single argument called `a` and merely returns `True`."""
    return True


@task
def failing_task(data):
    """
    Takes a single argument called `data` and raises a `NotImplementedError`
    exception throwing it back.
    """
    raise NotImplementedError(data)


@java.jtask
def jtask_task(data):
    """
    Takes a single argument called `data` and might raise a Java exception.
    """
    return str(java.jvm().java.lang.Integer(data))


@java.jtask
def failing_jtask_task(data):
    """
    Takes a single argument called `data` and raises a Python exception.
    """
    raise Exception('test exception')


@task
def reflect_data_to_be_processed(data):
    """Merely returns the data received."""
    return data


@task
def reflect_data_with_task_index(data, task_index):
    """Returns the data received with the `task_index` appended."""
    data.append(task_index)
    return data
