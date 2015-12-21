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
import types

from celery.result import ResultSet
from celery.app import current_app
from celery.task import task

from openquake.commonlib.parallel import TaskManager, check_mem_usage
from openquake.engine import logs, celery_node_monitor
from openquake.engine.utils import config

SOFT_MEM_LIMIT = int(config.get('memory', 'soft_mem_limit'))
HARD_MEM_LIMIT = int(config.get('memory', 'hard_mem_limit'))
check_mem_usage.__defaults__ = (SOFT_MEM_LIMIT, HARD_MEM_LIMIT)

if celery_node_monitor.CELERY_ON:

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
        task_ids = []

        def _submit(self, pickled_args):
            # submit tasks by using celery
            if isinstance(self.oqtask, types.FunctionType):
                celery_queue = config.get('amqp', 'celery_queue')
                self.oqtask = task(self.oqtask, queue=celery_queue)
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
            if not self.results:
                return acc
            backend = current_app().backend
            amqp_backend = backend.__class__.__name__.startswith('AMQP')
            rset = ResultSet(self.results)
            for task_id, result_dict in rset.iter_native():
                idx = self.task_ids.index(task_id)
                self.task_ids.pop(idx)
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

else:  # no celery

    class OqTaskManager(TaskManager):
        progress = staticmethod(logs.LOG.progress)
        task_ids = []


# convenient aliases
starmap = OqTaskManager.starmap
apply_reduce = OqTaskManager.apply_reduce
