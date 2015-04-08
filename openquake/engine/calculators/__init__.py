# Copyright (c) 2010-2015, GEM Foundation.
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


"""This package contains Hazard and Risk calculator classes."""

from openquake.baselib.general import CallableDict, import_all
from openquake.commonlib.source import TrtModel
from openquake.commonlib.parallel import TaskManager
from openquake.commonlib.calculators import base
from openquake.engine.utils import tasks, config
from openquake.engine.performance import EnginePerformanceMonitor

# an ordered dictionary of calculator classes
calculators = CallableDict(lambda job: job.get_param('calculation_mode'))


# monkey patch the base.BaseCalculator class
def __init__(self, job):
    self.job = job
    self.oqparam = self.job.get_oqparam()
    if not hasattr(self.oqparam, 'concurrent_tasks'):
        self.oqparam.concurrent_tasks = int(
            config.get('celery', 'concurrent_tasks'))
    if not hasattr(self.oqparam, 'usecache'):
        self.oqparam.usecache = False
    self.monitor = EnginePerformanceMonitor('', job.id)
    self.max_input_weight = float(
        config.get('hazard', 'max_input_weight'))
    self.max_output_weight = float(
        config.get('hazard', 'max_output_weight'))
    TrtModel.POINT_SOURCE_WEIGHT = float(
        config.get('hazard', 'point_source_weight'))
base.BaseCalculator.__init__ = __init__


# monkey patch the parallel.TaskManager class
def _submit(self, piks):
    oqtask = tasks.oqtask(self.oqtask.task_func)
    return oqtask.delay(*piks)
TaskManager._submit = _submit
TaskManager.aggregate_result_set = (
    tasks.OqTaskManager.aggregate_result_set.__func__)

# make aliases for the oq-lite calculators
for name in list(base.calculators):
    calculators[name + '_lite'] = base.calculators[name]

import_all('openquake.engine.calculators')
