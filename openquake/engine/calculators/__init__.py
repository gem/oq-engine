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
from openquake.commonlib import parallel
from openquake.engine.utils import tasks, config
from openquake.engine.performance import EnginePerformanceMonitor

# monkey patch the parallel module
parallel.starmap = tasks.starmap
parallel.apply_reduce = tasks.apply_reduce
parallel.litetask = tasks.oqtask

# import the oq-lite calculators  *after* the patching
from openquake.commonlib.calculators import base


# monkey patch the base.BaseCalculator class
def __init__(self, oqparam):
    self.oqparam = oqparam
    if not hasattr(self.oqparam, 'concurrent_tasks'):
        self.oqparam.concurrent_tasks = int(
            config.get('celery', 'concurrent_tasks'))
    if not hasattr(self.oqparam, 'usecache'):
        self.oqparam.usecache = False
    self.max_input_weight = float(
        config.get('hazard', 'max_input_weight'))
    self.max_output_weight = float(
        config.get('hazard', 'max_output_weight'))
    TrtModel.POINT_SOURCE_WEIGHT = float(
        config.get('hazard', 'point_source_weight'))

base.BaseCalculator.__init__ = __init__
base.BaseCalculator.post_process = lambda self: None
base.BaseCalculator.export = lambda self, exports='': None
base.BaseCalculator.clean_up = lambda self: None

# an ordered dictionary of calculator classes
calculators = CallableDict(lambda job: job.get_param('calculation_mode'))

import_all('openquake.engine.calculators')
