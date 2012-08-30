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
Task functions for our unit tests.
"""


from celery.task import task

from openquake import java
from openquake.utils import stats

from tests.utils import helpers


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


@task(ignore_result=True)
def test_async_data_reflector(job_id, *args, **kwargs):
    """Throw back the data stored in the KVS for the given `job_id`.

    This should be used for testing purposes only. The idea is to store the
    data expected in test setup and then use this task to play that data back
    to the test.

    See :py:class:`DoCurvesTestCase` for an example of how this task should be
    used.
    """
    return helpers.TestStore.lookup(job_id)


@task(ignore_result=True)
def test_compute_hazard_curve(job_id, sites, realization):
    """This task will be used to test
    :class`openquake.calculators.hazard.classical.core
    .ClassicalHazardCalculator` code.

    The test setup code will prepare a result set for each `realization`.
    This task will fetch these canned result sets and throw them back
    simulating the real hazard curve calculator.

    See also :py:meth:`DoCurvesTestCase.do_curves`.
    """
    key = "%s/%s" % (job_id, realization + 1)
    return helpers.TestStore.lookup(key)


@task(ignore_result=True)
@java.unpack_exception
@stats.count_progress("h", data_arg="sites")
def fake_compute_hazard_curve(job_id, sites, realization):
    """Fake hazard curve computation function."""
    raise NotImplementedError("Fake and failing hazard curve computation!")


@task
def reflect_args(*args, **kwargs):
    """Merely returns the parameters received."""
    return (args, kwargs)


@task
def just_say_hello(*args, **kwargs):
    """Merely returns 'hello'."""
    return "hello"


@task
def just_say_1(*args, **kwargs):
    """Merely returns 1."""
    return 1


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


@task
@java.unpack_exception
def jtask_task(data):
    """
    Takes a single argument called `data` and might raise a Java exception.
    """
    return str(java.jvm().java.lang.Integer(data))


@task
@java.unpack_exception
def failing_jtask_task(data):
    """
    Takes a single argument called `data` and raises a Python exception.
    """
    raise Exception('test exception')


@task
def reflect_data_to_be_processed(data):
    """Merely returns the data received."""
    return data


@task(ignore_result=True)
def ignore_result(data):
    """Write the data using the given test store key."""
    key, value = data[0]
    helpers.TestStore.set(key, value)
    # Results will be ignored.
    return data
