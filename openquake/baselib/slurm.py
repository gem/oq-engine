import os
import stat
import time
import subprocess
from openquake.baselib import parallel, config, zeromq

submit_cmd = list(config.distribution.submit_cmd.split())
SLURM_BATCH = '''\
#!/bin/bash
#SBATCH --job-name=workerpool
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task={num_cores}
#SBATCH --nodes={nodes}
srun python -m openquake.baselib.workerpool {num_cores} {job_id}
'''

def start_workers(n, job_id):
    """
    Start n workerpools which will write on scratch_dir/hostcores)
    """
    job_id = str(job_id)
    calc_dir = parallel.scratch_dir(job_id)
    slurm_sh = os.path.join(calc_dir, 'slurm.sh')
    code = SLURM_BATCH.format(num_cores=config.distribution.num_cores,
                              job_id=job_id, nodes=n)
    with open(slurm_sh, 'w') as f:
        f.write(code)
    os.chmod(slurm_sh, os.stat(slurm_sh).st_mode | stat.S_IEXEC)

    assert submit_cmd[0] == 'sbatch', submit_cmd
    # submit_cmd can be ['sbatch', '-A', 'gem', '-p', 'rome', 'oq', 'run']
    subprocess.run(submit_cmd[:-2] + [slurm_sh])


def wait_workers(n, job_id):
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


def stop_workers(job_id: str):
    """
    Stop all the started workerpools (read from the file scratch_dir/hostcores)
    """
    fname = os.path.join(parallel.scratch_dir(job_id), 'hostcores')
    with open(fname) as f:
        hostcores = f.readlines()
    for line in hostcores:
        host, _ = line.split()
        ctrl_url = 'tcp://%s:%s' % (host, config.zworkers.ctrl_port)
        print('Stopping %s' % host)
        with zeromq.Socket(ctrl_url, zeromq.zmq.REQ, 'connect') as sock:
            sock.send('stop')
