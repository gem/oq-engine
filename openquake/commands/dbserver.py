# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2025 GEM Foundation
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
import signal
import getpass
from openquake.baselib import config
from openquake.commonlib import logs
from openquake.server import dbserver


def main(cmd,
         dbhostport=None,
         foreground=False,
         *,
         loglevel='INFO'):
    """
    start/stop/restart the database server, or return its status
    """
    if config.multi_user:
        user = getpass.getuser()
        if user != 'openquake':
            sys.exit(f'Only user openquake can start the dbserver '
                     f'but you are {user}')

    if cmd == 'upgrade':
        sys.exit('Use oq engine --upgrade-db instead')

    if (os.environ.get('OQ_DATABASE', config.dbserver.host) == '127.0.0.1'
        and getpass.getuser() != 'openquake'):
        print('Doing nothing since the DB is local')
        return

    status = dbserver.get_status()
    if cmd == 'status':
        print('dbserver ' + status)
    elif cmd == 'stop':
        if status == 'running':
            pid = logs.dbcmd('getpid')
            os.kill(pid, signal.SIGINT)  # this is trapped by the DbServer
        else:
            print('dbserver already stopped')
    elif cmd == 'start':
        if status == 'not-running':
            dbserver.run_server(dbhostport, loglevel, foreground)
        else:
            print('dbserver already running')


main.cmd = dict(help='dbserver command',
                choices='start stop status upgrade'.split())
main.dbhostport = 'dbhost:port'
main.foreground = 'stay in foreground'
main.loglevel = 'DEBUG|INFO|WARN'
