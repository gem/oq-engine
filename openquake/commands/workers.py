#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
import getpass
from openquake.baselib import config, workerpool, parallel as p
from openquake.commonlib import logs

CHOICES = 'start stop status restart wait kill debug'.split()


def main(cmd, job_id: int=-1):
    """
    start/stop the workers, or return their status
    """
    if (cmd != 'status' and config.multi_user and
            getpass.getuser() not in 'openquake'):
        sys.exit('oq workers only works in single user mode')
    dist = p.oq_distribute()
    if dist == 'zmq':
        master = workerpool.WorkerMaster(config.zworkers)
        print(getattr(master, cmd)())
    elif dist == 'slurm':
        job = logs.dbcmd('get_job', job_id)
        master = workerpool.WorkerMaster(job.id)
        print(getattr(master, cmd)())
    else:
        print('Nothing to do: oq_distribute=%s' % dist)


main.cmd = dict(help='command', choices=CHOICES)
main.job_id = dict(help='running job')
