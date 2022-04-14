# this is useful to assess the power of a server and the scaling with
# the number of cores; examples:
# python stress_cpy.py 64 && oq show performance
# python stress_cpy.py 128 && oq show performance

import sys
import numpy
import logging
from openquake.baselib.parallel import Starmap
from openquake.commonlib.datastore import hdf5new


def stress_cpu(zeros, monitor):
    for i in range(len(zeros)):
        for j in range(100_000):
            zeros[i] += numpy.exp(-j)
    return {}


if __name__ == '__main__':
    args = sys.argv[1:]
    ct = int(args[0]) if args else 64
    logging.basicConfig(level=logging.INFO)
    logging.info('Producing %d tasks', ct)
    with hdf5new() as h5:
        Starmap.apply(stress_cpu, (numpy.zeros(10_000),),
                      concurrent_tasks=ct, h5=h5).reduce()
        logging.info('Performance info in %s', h5.filename)
    Starmap.shutdown()
