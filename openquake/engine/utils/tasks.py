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

"""Utility functions related to splitting work into tasks."""

from celery.result import ResultSet
from celery.app import current_app
from celery.task import task

from openquake.hazardlib.gsim.base import GroundShakingIntensityModel
from openquake.commonlib.parallel import \
    TaskManager, safely_call, check_mem_usage
from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.writer import CacheInserter

SOFT_MEM_LIMIT = int(config.get('memory', 'soft_mem_limit'))
HARD_MEM_LIMIT = int(config.get('memory', 'hard_mem_limit'))
check_mem_usage.__defaults__ = (SOFT_MEM_LIMIT, HARD_MEM_LIMIT)


class JobNotRunning(Exception):
    pass


class OqTaskManager(TaskManager):
    """
    A celery-based task manager. The usage is::

      oqm = OqTaskManager(do_something, logs.LOG.progress)
      oqm.send(arg1, arg2)
      oqm.send(arg3, arg4)
      print oqm.aggregate_results(agg, acc)

    Progress report is built-in.
    """
    progress = staticmethod(logs.LOG.progress)

    def _submit(self, pickled_args):
        # submit tasks by using celery
        return self.oqtask.delay(*pickled_args)

    def aggregate_result_set(self, agg, acc):
        """
        Loop on a set of celery AsyncResults and update the accumulator
        by using the aggregation function.

        :param agg: the aggregation function, (acc, val) -> new acc
        :param acc: the initial value of the accumulator
        :returns: the final value of the accumulator
        """
        if not self.results:
            return acc
        backend = current_app().backend
        amqp_backend = backend.__class__.__name__.startswith('AMQP')
        rset = ResultSet(self.results)
        for task_id, result_dict in rset.iter_native():
            check_mem_usage()  # warn if too much memory is used
            result = result_dict['result']
            if isinstance(result, BaseException):
                raise result
            self.received.append(len(result))
            acc = agg(acc, result.unpickle())
            if amqp_backend:
                # work around a celery bug
                del backend._cache[task_id]
        return acc

# convenient aliases
starmap = OqTaskManager.starmap
apply_reduce = OqTaskManager.apply_reduce


def oqtask(task_func):
    """
    Task function decorator which sets up logging and catches (and logs) any
    errors which occur inside the task. Also checks to make sure the job is
    actually still running. If it is not running, the task doesn't get
    executed, so we don't do useless computation.

    :param task_func: the function to decorate
    """
    def wrapped(*args):
        """
        Initialize logs, make sure the job is still running, and run the task
        code surrounded by a try-except. If any error occurs, log it as a
        critical failure.
        """
        # the last argument is assumed to be a monitor
        monitor = args[-1]
        job = models.OqJob.objects.get(id=monitor.job_id)
        if job.is_running is False:
            # the job was killed, it is useless to run the task
            raise JobNotRunning(monitor.job_id)

        # it is important to save the task id soon, so that
        # the revoke functionality can work
        with monitor('storing task id', task=tsk, autoflush=True):
            pass

        with logs.handle(job):
            check_mem_usage()  # warn if too much memory is used
            # run the task
            try:
                total = 'total ' + task_func.__name__
                with monitor(total, task=tsk):
                    with GroundShakingIntensityModel.forbid_instantiation():
                        return task_func(*args)
            finally:
                # save on the db
                CacheInserter.flushall()
                # the task finished, we can remove from the performance
                # table the associated row 'storing task id'
                models.Performance.objects.filter(
                    oq_job=job,
                    operation='storing task id',
                    task_id=tsk.request.id).delete()
    celery_queue = config.get('amqp', 'celery_queue')
    f = lambda *args: safely_call(wrapped, args, pickle=True)
    f.__name__ = task_func.__name__
    f.__module__ = task_func.__module__
    tsk = task(f, queue=celery_queue)
    tsk.__func__ = tsk
    tsk.task_func = task_func
    return tsk


# ######### oq-lite support: this is hackish for the time being ############# #

from openquake.commonlib import parallel

# monkey patch the parallel module
parallel.starmap = starmap
parallel.apply_reduce = apply_reduce
parallel.litetask = oqtask
