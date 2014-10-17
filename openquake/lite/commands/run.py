import logging

from openquake.commonlib import sap, readinput
from openquake.commonlib.parallel import executor
from openquake.lite.calculators import calculate


def run(job_ini, concurrent_tasks=executor._max_workers, loglevel='INFO'):
    """
    Run a calculation. Optionally, set the number of concurrent_tasks
    (0 to disable the parallelization).
    """
    logging.basicConfig(level=getattr(logging, loglevel))
    with open(job_ini) as f:
        oqparam = readinput.get_oqparam(f)
        oqparam.concurrent_tasks = concurrent_tasks
        for fname in calculate(oqparam):
            print 'exported %s' % fname


parser = sap.Parser(run)
parser.arg('job_ini', 'calculation configuration')
parser.opt('concurrent_tasks', 'hint for the number of tasks to spawn')
parser.opt('loglevel', 'logging level', choices=
           'DEBUG INFO WARN ERROR CRITICAL'.split())
