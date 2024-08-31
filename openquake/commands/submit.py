# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import stat
from openquake.baselib import config, parallel
from openquake.commonlib import readinput
from openquake.engine.engine import create_jobs

script = '''#!/bin/bash
job_id=(`oq create_jobs %(n)d`)
%(lines)s
time oq collect_jobs ${job_id[@]}
'''

SLURM_BATCH = '''\
#!/bin/bash
#SBATCH --job-name=workerpool
#SBATCH --time=10:00:00
#SBATCH --cpus-per-task={num_cores}
#SBATCH --nodes={nodes}
srun python -m openquake.baselib.workerpool {num_cores} {job_id}
'''

def create_job(n, job_ini):
    dic = readinput.get_params(job_ini)
    if 'concurrent_tasks' not in dic:
        ct = 2 * int(config.distribution.num_cores) * n
        dic['concurrent_tasks'] = str(ct)
    [job] = create_jobs([dic])
    return job.calc_id


def main(n: int, job_ini):
    """
    Print a bash script generating many calculations
    """
    try:
        num_cores = config.distribution.num_cores
    except AttributeError:
        num_cores = parallel.tot_cores
    submit_cmd = config.distribution.submit_cmd.split()
    if False:
        if submit_cmd[0] == 'sbatch':
            submit_cmd.insert(1, '--cpus-per-task=%s' % num_cores)
        descr = readinput.get_params(job_ini)['description']
        lines = []
        pp = 'OQ_DISTRIBUTE=processpool '
        for i in range(n):
            spec = '[%d,%d]' % (i+1, n) 
            params = "tile_spec='%s' description=\"%s%s\" job_id=${job_id[%d]}" % (
                spec, descr, spec, i)
            lines.append(pp + ' '.join(submit_cmd) + f" {job_ini} -p {params}")
        print(script % dict(n=len(lines), lines='\n'.join(lines)))
    else:
        job_id = create_job(n, job_ini)
        code = SLURM_BATCH.format(num_cores=config.distribution.num_cores,
                                  job_id=job_id, nodes=n)
        with open('slurm.sh', 'w') as f:
            f.write(code)
        os.chmod('slurm.sh', os.stat('slurm.sh').st_mode | stat.S_IEXEC)
        submit = ' '.join(submit_cmd[:-2])
        runcalc = f'''#!/bin/bash
        trap 'oq workers stop' EXIT
        {submit} slurm.sh
        {submit.replace('sbatch', 'srun')} -c16 oq run {job_ini} -p job_id={job_id}'''
        print(runcalc)

main.n = dict(help='number of jobs to generate')
main.job_ini = dict(help='path to .ini file')
