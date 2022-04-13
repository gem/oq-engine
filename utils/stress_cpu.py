# this is useful to assess the power of a server and the scaling with
# the number of cores; examples:
# python stress_cpy.py 64
# python stress_cpy.py 128

import sys
import numpy
import logging
from openquake.baselib.parallel import Starmap


def stress_cpu(zeros, monitor):
    for i in range(len(zeros)):
        for j in range(100_000):
            zeros[i] += numpy.exp(-j)
    return {}


if __name__ == '__main__':
    args = sys.argv[1:]
    ct = args[0] if args else 64
    logging.basicConfig(level=logging.INFO)
    logging.info('Producing %d tasks', ct)
    Starmap.apply(stress_cpu, (numpy.zeros(10_000),),
                  concurrent_tasks=ct).reduce()
    Starmap.shutdown()
