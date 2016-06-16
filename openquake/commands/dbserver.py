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
import socket
import subprocess
from openquake.commonlib import sap
from openquake.engine import logs, config


def runserver():
    subprocess.Popen([sys.executable, '-m', 'openquake.server.dbserver'])


def dbserver(cmd):
    """
    start/stop/restart the database server, or return its status
    """
    if config.get('dserver', 'multi_user'):
        sys.exit('oq dbserver only works in single user mode')

    # check if the DbServer is up
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        err = sock.connect_ex(config.DBS_ADDRESS)
    finally:
        sock.close()
    status = 'not-running' if err else 'running'
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

parser = sap.Parser(dbserver)
parser.arg('cmd', 'dbserver command',
           choices='start stop status restart'.split())
