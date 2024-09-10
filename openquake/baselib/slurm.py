import os
import sys
import stat
import time
import pickle
import subprocess
from openquake.baselib import parallel, config

submit_cmd = list(config.distribution.submit_cmd.split())
SLURM_BATCH = '''\
#!/bin/bash
#SBATCH --job-name=workerpool
#SBATCH --time={slurm_time}
#SBATCH --cpus-per-task={num_cores}
#SBATCH --nodes={nodes}
srun python -m openquake.baselib.workerpool {num_cores} {job_id}
'''

def start_workers(job_id, n):
    """
    Start n workerpools which will write on scratch_dir/hostcores)
    """
    job_id = str(job_id)
    calc_dir = parallel.scratch_dir(job_id)
    slurm_sh = os.path.join(calc_dir, 'slurm.sh')
    print('Using %s' % slurm_sh)
    code = SLURM_BATCH.format(num_cores=config.distribution.num_cores,
                              slurm_time=config.distribution.slurm_time,
                              job_id=job_id, nodes=n)
    with open(slurm_sh, 'w') as f:
        f.write(code)
    os.chmod(slurm_sh, os.stat(slurm_sh).st_mode | stat.S_IEXEC)

    assert submit_cmd[0] == 'sbatch', submit_cmd
    # submit_cmd can be ['sbatch', '-A', 'gem', '-p', 'rome', 'oq', 'run']
    subprocess.run(submit_cmd[:-2] + [slurm_sh])


def wait_workers(job_id, n):
    """
    Wait until the hostcores file is filled with n names
    """
    calc_dir = parallel.scratch_dir(job_id)
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


def ssh(jobs):
    """
    Run the jobs on the first host
    """
    scratch_dir = parallel.scratch_dir(jobs[0].calc_id)
    pik = os.path.join(scratch_dir, 'jobs.pik')
    with open(pik, 'w') as f:
        pickle.dump(jobs, f)
    with open(os.path.join(scratch_dir, 'hostcores')) as f:
        line = f.read().split('\n')[0]
    host, _cores = line.split()
    cmd = ['ssh', host, sys.executable, '-m', 'openquake.engine.engine', pik]
    print(' '.join(ssh))
    subprocess.run(cmd)
