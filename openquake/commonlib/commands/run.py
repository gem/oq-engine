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
