#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging

from openquake.commonlib import sap, readinput
from openquake.commonlib.parallel import executor, PerformanceMonitor
from openquake.commonlib.calculators import base


def run(job_ini, concurrent_tasks=executor.num_tasks_hint,
        loglevel='info', usecache=False, exports='csv'):
    """
    Run a calculation. Optionally, set the number of concurrent_tasks
    (0 to disable the parallelization).
    """
    logging.basicConfig(level=getattr(logging, loglevel.upper()))
    oqparam = readinput.get_oqparam(job_ini)
    oqparam.concurrent_tasks = concurrent_tasks
    oqparam.usecache = usecache
    oqparam.exports = exports
    with PerformanceMonitor('total', monitor_csv=os.path.join(
            oqparam.export_dir, 'performance_csv'), autoflush=True) as monitor:
        calc = base.calculators(oqparam, monitor)
        with monitor('pre_execute'):
            calc.pre_execute()
        with monitor('execute'):
            result = calc.execute()
        with monitor('post_execute'):
            out = calc.post_execute(result)
        with monitor('save_pik'):
            calc.save_pik(result)
    for item in sorted(out.iteritems()):
        logging.info('exported %s: %s', *item)
    logging.info('Total time spent: %s s', monitor.duration)
    logging.info('Memory allocated: %s M', monitor.mem / 1024. / 1024.)

parser = sap.Parser(run)
parser.arg('job_ini', 'calculation configuration file '
           '(or files, comma-separated)')
parser.opt('concurrent_tasks', 'hint for the number of tasks to spawn',
           type=int)
parser.opt('loglevel', 'logging level',
           choices='debug info warn error critical'.split())
parser.flg('usecache', 'use the hazard output cache if possible')
