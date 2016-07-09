#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import sys
import subprocess
from openquake.risklib import valid
from openquake.commonlib import sap
from openquake.engine import logs, config
from openquake.server.dbserver import get_status


def runserver():
    subprocess.Popen([sys.executable, '-m', 'openquake.server.dbserver'])


@sap.Parser
def dbserver(cmd):
    """
    start/stop/restart the database server, or return its status
    """
    if valid.boolean(config.get('dbserver', 'multi_user')):
        sys.exit('oq dbserver only works in single user mode')

    status = get_status()
    if cmd == 'status':
        print(status)
    elif cmd == 'stop':
        if status == 'running':
            logs.dbcmd('stop')
            print('stopped')
        else:
            print('already stopped')
    elif cmd == 'start':
        if status == 'not-running':
            runserver()
            print('started')
        else:
            print('already running')
    elif cmd == 'restart':
        if status == 'running':
            logs.dbcmd('stop')
            print('stopped')
        runserver()
        print('started')

dbserver.arg('cmd', 'dbserver command',
             choices='start stop status restart'.split())
