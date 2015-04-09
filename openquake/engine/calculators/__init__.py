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
from openquake.commonlib import parallel
from openquake.engine.utils import tasks

# monkey patch the parallel module
parallel.starmap = tasks.starmap
parallel.apply_reduce = tasks.apply_reduce
parallel.litetask = tasks.oqtask

# import the oq-lite calculators  *after* the patching
from openquake.commonlib.calculators import base

# temporarily patching the BaseCalculator class
base.BaseCalculator.post_process = lambda self: None
base.BaseCalculator.export = lambda self, exports='': None
base.BaseCalculator.clean_up = lambda self: None

# an ordered dictionary of calculator classes
calculators = CallableDict(lambda job: job.get_param('calculation_mode'))

import_all('openquake.engine.calculators')
