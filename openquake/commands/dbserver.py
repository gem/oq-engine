# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
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
from openquake.baselib import sap, config
from openquake.commonlib import logs
from openquake.server import dbserver as dbs


@sap.script
def dbserver(cmd, dbhostport=None,
             dbpath=os.path.expanduser(config.dbserver.file),
             loglevel='INFO', foreground=False):
    """
    start/stop/restart the database server, or return its status
    """
    if config.dbserver.multi_user and getpass.getuser() != 'openquake':
        sys.exit('oq dbserver only works in single user mode')

    status = dbs.get_status()
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
            dbs.run_server(dbpath, dbhostport, loglevel, foreground)
        else:
            print('dbserver already running')


dbserver.arg('cmd', 'dbserver command',
             choices='start stop status'.split())
dbserver.arg('dbhostport', 'dbhost:port')
dbserver.arg('dbpath', 'dbpath')
dbserver.opt('loglevel', 'DEBUG|INFO|WARN')
dbserver.flg('foreground', 'stay in foreground')
