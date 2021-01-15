# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2021 GEM Foundation
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

import os
import sys
import getpass
import subprocess
from pprint import pprint
from openquake.baselib import config, workerpool as w

ro_commands = ('status', 'inspect')
oqdist = os.environ.get('OQ_DISTRIBUTE', config.distribution.oq_distribute)


def start_dask():
    """
    Start the remote workers with ssh and the scheduler locally
    """
    remote_python = config.zworkers.remote_python or sys.executable
    sched = config.distribution.dask_scheduler
    for hostcores in config.zworkers.host_cores.split(','):
        host, cores = hostcores.split()
        args = ['ssh', '-f', '-T', host, remote_python, '-m',
                'distributed.cli.dask_worker', sched, '--nprocs', cores]
        subprocess.Popen(args)
    host, port = sched.split(':')
    subprocess.check_output([
        sys.executable, '-m', 'distributed.cli.dask_scheduler',
        '--host', host, '--port', port])


def main(cmd):
    """
    start/stop/restart the workers, or return their status
    """
    if (cmd not in ro_commands and config.dbserver.multi_user and
            getpass.getuser() not in 'openquake'):
        sys.exit('oq workers only works in single user mode')
    if oqdist == 'zmq':
        zmaster = w.WorkerMaster(**config.zworkers)
        pprint(getattr(zmaster, cmd)())
    elif oqdist == 'dask':
        start_dask()
    else:
        print('Nothing to do: oq_distribute=%s' % oqdist)


main.cmd = dict(help='command',
                choices='start stop status restart inspect wait'.split())
