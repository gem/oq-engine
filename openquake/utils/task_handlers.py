# -*- coding: utf-8 -*-
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232


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
OO Interface to manage task queueing.
"""

from celery.task import task
from openquake import logs
from celery.task.sets import TaskSet
import traceback

class SimpleTaskHandler(object):
    """
    A task queue handler that never consumes its tasks asynchronously
    """
    def __init__(self):
        self._ret = None
        self._tasks = []

    def enqueue(self, plain_task_cls, *args, **kwargs):
        """
        Build a task from a plain task callable with *args and **kwargs
        then append the built task to the queue
        """
        plain_task = plain_task_cls(*args, **kwargs)
        self._tasks.append(plain_task)

    def apply(self):
        """
        Execute all tasks and returns a list of results
        """
        return [t.run() for t in self._tasks]

    def apply_async(self):
        """
        Execute each tasks and save their value
        """
        self._ret = self.apply()

    def wait_for_results(self):
        """
        Returns values got by apply_async
        """
        return self._ret


class CeleryTaskHandler(SimpleTaskHandler):
    """
    A task queue handler for celery task queueing
    """
    def __init__(self):
        super(CeleryTaskHandler, self).__init__()
        self._taskset = None
        self._async_ret = None

    def _create_taskset(self):
        """
        Create a celery TaskSet suitable for apply_* function
        """
        tasks = [CELERY_TASK.subtask((t,)) for t in self._tasks]
        self._taskset = TaskSet(tasks)

    def apply_async(self):
        """
        Consume the whole queue executing the task asynchronously
        """
        self._create_taskset()
        self._async_ret = self._taskset.apply_async()

    def wait_for_results(self):
        """
        Wait the results, if an async execution has been requested
        """
        return self._async_ret.join()

    def apply(self):
        """
        Consume the whole queue executing the task synchronously
        """
        self._create_taskset()
        return self._taskset.apply()


@task
def celery_task(a_task):
    """
    Delegate to a_task#run just to decouple celery from a concrete
    task.
    Log any occurring exception
    """
    try:
        return a_task.run()
    except Exception, err:
        logs.LOG.debug(traceback.format_exc())
        logs.LOG.critical('Error occurred in task %s: %s' % (
            a_task, str(err)))
        logs.LOG.exception(err)
        raise err
CELERY_TASK = celery_task
