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
Utility functions related to splitting work into tasks.
"""


from celery.task.sets import TaskSet
import itertools
import time


class WrongTaskParameters(Exception):
    """The user specified wrong paramaters for the celery task function."""


class TaskFailed(Exception):
    """At least on (sub)task failed."""


def distribute(cardinality, the_task, (name, data), other_args=None,
               flatten_results=False):
    """Runs `the_task` in a task set with the given `cardinality`.

    The given `data` is portioned across the subtasks in the task set.
    The results returned by the subtasks are returned in a list e.g.:
        [result1, result2, ..]
    If each subtask returns a list that will result in list of lists. Please
    set `flatten_results` to `True` if you want the results to be returned in a
    single list.

    :param int cardinality: The size of the task set.
    :param the_task: A `celery` task callable.
    :param str name: The parameter name under which the portioned `data` is to
        be passed to `the_task`.
    :param data: The `data` that is to be portioned and passed to the subtasks
        for processing.
    :param dict other_args: The remaining (keyword) parameters that are to be
        passed to the subtasks.
    :param bool flatten_results: If set, the results will be returned as a
        single list (as opposed to [[results1], [results2], ..]).
    """
    # Too many local variables (18/15)
    # pylint: disable=R0914

    def kwargs(data_portion):
        """
        Construct the full set of keyword parameters for the task to be
        invoked.
        """
        params = {name: data_portion}
        if other_args:
            params.update(other_args)
        return params

    subtasks = []

    data_length = len(data)
    start = 0
    end = chunk_size = int(data_length / float(cardinality))
    if chunk_size == 0:
        # We were given less data items than the number of subtasks specified.
        # Spawn at least on subtask even if the data to be processed is empty.
        cardinality = data_length if data_length > 0 else 1
        end = chunk_size = 1

    for _ in xrange(cardinality - 1):
        data_portion = data[start:end]
        subtask = the_task.subtask(**kwargs(data_portion))
        subtasks.append(subtask)
        start = end
        end += chunk_size
    # The last subtask takes the rest of the data.
    data_portion = data[start:]
    subtask = the_task.subtask(**kwargs(data_portion))
    subtasks.append(subtask)

    # At this point we have created all the subtasks and each one got a
    # portion of the data that is to be processed. Now we will create and run
    # the task set.
    result = TaskSet(tasks=subtasks).apply_async()

    # Wait for all subtasks to complete.
    while not result.ready():
        time.sleep(0.5)
    try:
        the_results = result.join()
    except TypeError, exc:
        raise WrongTaskParameters(exc.args[0])
    except Exception, exc:
        # At least one subtask failed.
        raise TaskFailed(exc.args[0])

    if flatten_results:
        if the_results:
            if isinstance(the_results, list) or isinstance(the_results, tuple):
                the_results = list(itertools.chain(*the_results))

    return the_results


def parallelize(cardinality, the_task, kwargs, flatten_results=False):
    """Runs `the_task` in a task set with the given `cardinality`.

    Alls subtasks receive the parameters passed via `kwargs`. The results
    returned by the subtasks are returned in a list e.g.:
        [result1, result2, ..]
    If each subtask returns a list that will result in list of lists.

    :param int cardinality: The size of the task set.
    :param the_task: A `celery` task callable.
    :param dict kwargs: The (keyword) parameters that are to be passed
        to *all* subtasks.
    :param bool flatten_results: If set, the results will be returned as a
        single list (as opposed to [[results1], [results2], ..]).
    """
    subtasks = []
    for _ in xrange(cardinality):
        subtask = the_task.subtask(**kwargs)
        subtasks.append(subtask)

    # At this point we have created all the subtasks.
    result = TaskSet(tasks=subtasks).apply_async()

    # Wait for all subtasks to complete.
    while not result.ready():
        time.sleep(0.5)
    try:
        the_results = result.join()
    except TypeError, exc:
        raise WrongTaskParameters(exc.args[0])
    except Exception, exc:
        # At least one subtask failed.
        raise TaskFailed(exc.args[0])

    if flatten_results:
        if the_results:
            if isinstance(the_results, list) or isinstance(the_results, tuple):
                the_results = list(itertools.chain(*the_results))

    return the_results
