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

import logging

from openquake.commonlib import sap, readinput
from openquake.commonlib.parallel import executor, PerformanceMonitor
from openquake.commonlib.calculators import calculators


def run(job_ini, concurrent_tasks=executor._max_workers, loglevel='INFO'):
    """
    Run a calculation. Optionally, set the number of concurrent_tasks
    (0 to disable the parallelization).
    """
    logging.basicConfig(level=getattr(logging, loglevel))
    with open(job_ini) as f, PerformanceMonitor():
        oqparam = readinput.get_oqparam(f)
        oqparam.concurrent_tasks = concurrent_tasks
        calc = calculators(oqparam)
        for item in calc.run().items():
            logging.info('exported %s: %s', *item)


parser = sap.Parser(run)
parser.arg('job_ini', 'calculation configuration file')
parser.opt('concurrent_tasks', 'hint for the number of tasks to spawn',
           type=int)
parser.opt('loglevel', 'logging level', choices=
           'DEBUG INFO WARN ERROR CRITICAL'.split())
