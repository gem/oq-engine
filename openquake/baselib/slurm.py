import sys
from openquake.baselib.parallel import slurm_task

if __name__ == '__main__':
    slurm_task(*sys.argv[1:])
