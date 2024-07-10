import sys
from openquake.baselib.parallel import slurm_tasks

if __name__ == '__main__':
    slurm_tasks(*sys.argv[1:])
