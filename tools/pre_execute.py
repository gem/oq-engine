#!/usr/bin/env python

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

import sys
import time
from openquake.engine.engine import (
    job_from_file, getpass, get_calculator_class)
from openquake.engine import logs


def pre_execute(job_ini):
    """
    Run a hazard calculation, but stops it immediately after the
    pre_execute phase. In this way it is possible to determine
    the input_weight and output_weight of the calculation without
    running it.
    """
    job = job_from_file(job_ini, getpass.getuser(), 'info', [])

    calc_mode = job.get_param('calculation_mode')
    calculator = get_calculator_class('hazard', calc_mode)(job)

    t0 = time.time()
    with logs.handle(job):
        calculator.pre_execute()
        duration = time.time() - t0
        logs.LOG.info('Pre_execute time: %s s', duration)

if __name__ == '__main__':
    pre_execute(sys.argv[1])
