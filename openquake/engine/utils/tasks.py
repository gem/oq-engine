# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""Utility functions related to splitting work into tasks."""
import types

from openquake.baselib.performance import Monitor
from openquake.commonlib import parallel, valid
from openquake.engine.utils import config

litetask = parallel.litetask
celery_queue = config.get('amqp', 'celery_queue')
SOFT_MEM_LIMIT = int(config.get('memory', 'soft_mem_limit'))
HARD_MEM_LIMIT = int(config.get('memory', 'hard_mem_limit'))
USE_CELERY = valid.boolean(config.get('celery', 'use_celery') or 'false')
parallel.check_mem_usage.__defaults__ = (
    Monitor(), SOFT_MEM_LIMIT, HARD_MEM_LIMIT)

if USE_CELERY:
    from celery.result import ResultSet
    from celery.app import current_app
    from celery.task import task

    class OqTaskManager(parallel.TaskManager):
        """
        A celery-based task manager. The usage is::

          oqm = OqTaskManager(do_something, logs.LOG.progress)
          oqm.send(arg1, arg2)
          oqm.send(arg3, arg4)
          print oqm.aggregate_results(agg, acc)

        Progress report is built-in.
        """
        task_ids = []

        def _submit(self, pickled_args):
            if isinstance(self.oqtask, types.FunctionType):
                # don't use celery
                return super(OqTaskManager, self)._submit(pickled_args)
            # else use celery
            res = self.oqtask.delay(*pickled_args)
            self.task_ids.append(res.task_id)
            return res

        def aggregate_result_set(self, agg, acc):
            """
            Loop on a set of celery AsyncResults and update the accumulator
            by using the aggregation function.

            :param agg: the aggregation function, (acc, val) -> new acc
            :param acc: the initial value of the accumulator
            :returns: the final value of the accumulator
            """
            if isinstance(self.oqtask, types.FunctionType):
                # don't use celery
                return super(OqTaskManager, self).aggregate_result_set(
                    agg, acc)
            if not self.results:
                return acc
            backend = current_app().backend
            amqp_backend = backend.__class__.__name__.startswith('AMQP')
            rset = ResultSet(self.results)
            for task_id, result_dict in rset.iter_native():
                idx = self.task_ids.index(task_id)
                self.task_ids.pop(idx)
                parallel.check_mem_usage()  # warn if too much memory is used
                result = result_dict['result']
                if isinstance(result, BaseException):
                    raise result
                self.received.append(len(result))
                acc = agg(acc, result.unpickle())
                if amqp_backend:
                    # work around a celery bug
                    del backend._cache[task_id]
            return acc

    def oqtask(task_func):
        """
        Wrapper around celery.task and parallel.litetask
        """
        tsk = task(litetask(task_func), queue=celery_queue)
        tsk.__func__ = tsk
        tsk.task_func = task_func
        return tsk

    # hack
    parallel.TaskManager = OqTaskManager
    parallel.litetask = oqtask
    parallel.apply_reduce = OqTaskManager.apply_reduce
    parallel.starmap = OqTaskManager.starmap
