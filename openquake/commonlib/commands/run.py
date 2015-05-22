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

from openquake.commonlib import sap, readinput, valid
from openquake.commonlib.parallel import executor, PerformanceMonitor
from openquake.commonlib.calculators import base


def run(job_ini, concurrent_tasks=executor.num_tasks_hint,
        loglevel='info', hc=None, exports='csv'):
    """
    Run a calculation. Optionally, set the number of concurrent_tasks
    (0 to disable the parallelization).
    """
    logging.basicConfig(level=getattr(logging, loglevel.upper()))
    oqparam = readinput.get_oqparam(job_ini)
    oqparam.concurrent_tasks = concurrent_tasks
    oqparam.hazard_calculation_id = hc
    oqparam.exports = exports
    monitor = PerformanceMonitor('total', autoflush=True)
    calc = base.calculators(oqparam, monitor)
    monitor.monitor_csv = os.path.join(
        calc.datastore.calc_dir, 'performance.csv')
    with monitor:
        calc.run()
    logging.info('Calculation %s saved in %s',
                 calc.datastore.calc_id, calc.datastore.calc_dir)
    logging.info('Total time spent: %s s', monitor.duration)
    logging.info('Memory allocated: %s M', monitor.mem / 1024. / 1024.)

parser = sap.Parser(run)
parser.arg('job_ini', 'calculation configuration file '
           '(or files, comma-separated)')
parser.opt('concurrent_tasks', 'hint for the number of tasks to spawn',
           type=int)
parser.opt('loglevel', 'logging level',
           choices='debug info warn error critical'.split())
parser.opt('hc', 'previous calculation ID', type=int)
parser.opt('exports', 'export formats as a comma-separated string',
           type=valid.export_formats)
