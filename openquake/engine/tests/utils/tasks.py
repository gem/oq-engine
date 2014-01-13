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

from openquake.engine.utils import config

from openquake.engine.tests.utils import helpers


def test_task(func, *args, **kwargs):
    kwargs['queue'] = config.get('amqp', 'celery_queue')
    return task(func, *args, **kwargs)


@test_task
def reflect_args(*args, **kwargs):
    """Merely returns the parameters received."""
    return (args, kwargs)


@test_task
def just_say_hello(*args, **kwargs):
    """Merely returns 'hello'."""
    return "hello"


@test_task
def just_say_1(*args, **kwargs):
    """Merely returns 1."""
    return 1


@test_task
def single_arg_called_a(a):
    """Takes a single argument called `a` and merely returns `True`."""
    return True


@test_task
def failing_task(data):
    """
    Takes a single argument called `data` and raises a `NotImplementedError`
    exception throwing it back.
    """
    raise NotImplementedError(data)


@test_task
def reflect_data_to_be_processed(data):
    """Merely returns the data received."""
    return data
