import os
import sys
import stat
import time
import subprocess
from openquake.baselib import parallel, config

submit_cmd = list(config.distribution.submit_cmd.split())
SLURM_BATCH = '''\
#!/bin/bash
#SBATCH --job-name=oq{job_id}
#SBATCH --time={slurm_time}
#SBATCH --cpus-per-task={num_cores}
#SBATCH --nodes={nodes}
srun python -m openquake.baselib.workerpool {num_cores} {job_id}
'''

def start_workers(job_id, n):
    """
    Start n workerpools which will write on calc_dir/hostcores)
    """
    calc_dir = parallel.calc_dir(job_id)
    slurm_sh = os.path.join(calc_dir, 'slurm.sh')
    print('Using %s' % slurm_sh)
    code = SLURM_BATCH.format(num_cores=config.distribution.num_cores,
                              slurm_time=config.distribution.slurm_time,
                              job_id=job_id, nodes=n)
    with open(slurm_sh, 'w') as f:
        f.write(code)
    os.chmod(slurm_sh, os.stat(slurm_sh).st_mode | stat.S_IEXEC)

    # submit_cmd can be ['sbatch', '-A', 'gem', '-p', 'rome', 'oq', 'run']
    if submit_cmd[0] == 'sbatch':
        subprocess.run(submit_cmd[:-2] + [slurm_sh])
    else:
        print('Faking SLURM with a local WorkerPool')
        subprocess.Popen([sys.executable, '-m', 'openquake.baselib.workerpool',
                          config.distribution.num_cores, str(job_id)])


def wait_workers(job_id, n):
    """
    Wait until the hostcores file is filled with n names
    """
    calc_dir = parallel.calc_dir(job_id)
    fname = os.path.join(calc_dir, 'hostcores')
    while True:
        if not os.path.exists(fname):
            time.sleep(5)
            print(f'Waiting for {fname}')
            continue
        with open(fname) as f:
            hosts = f.readlines()
        print('%d/%d workerpools started' % (len(hosts), n))
        if len(hosts) == n:
            break
        else:
            time.sleep(5)
