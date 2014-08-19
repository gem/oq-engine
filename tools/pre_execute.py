#!/usr/bin/env python
import sys
import time
import logging
from openquake.engine.engine import (
    job_from_file, getpass, get_calculator_class, LogStreamHandler)
from openquake.engine import logs


def pre_execute(job_ini):
    job = job_from_file(job_ini, getpass.getuser(), 'info', [])

    calc_mode = job.hazard_calculation.calculation_mode
    calculator = get_calculator_class('hazard', calc_mode)(job)
    calc = job.calculation

    handler = LogStreamHandler('hazard', calc)
    logging.root.addHandler(handler)
    logs.set_level('info')

    t0 = time.time()
    try:
        calculator.pre_execute()
    finally:
        duration = time.time() - t0
        logs.LOG.info('Pre_execute time: %s s', duration)
        logging.root.removeHandler(handler)

if __name__ == '__main__':
    pre_execute(sys.argv[1])
