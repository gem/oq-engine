# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2023 GEM Foundation
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
from openquake.commonlib import logs, dbapi
from openquake.server import dbserver, db


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
        if user != config.dbserver.user:
            sys.exit(f'Only user {config.dbserver.user} can start the dbserver '
                     f'but you are {user}')

    if cmd == 'upgrade':
        applied = db.actions.upgrade_db(dbapi.db)
        if applied:
            print('Applied upgrades', applied)
        else:
            print('Already upgraded')
        dbapi.db.close()
        return

    if os.environ.get('OQ_DATABASE', config.dbserver.host) == 'local':
        print('Doing nothing since OQ_DATABASE=local')
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
