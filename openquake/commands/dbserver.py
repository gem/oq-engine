# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2026 GEM Foundation
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
from openquake.baselib import is_server_installation
from openquake.commonlib import logs
from openquake.server import dbserver


def main(cmd, foreground=False):
    """
    start/stop the database server, or return its status
    """
    if not is_server_installation():
        print('Doing nothing since the database is accessed directly '
              'in user and devel installations')
        return
    user = getpass.getuser()
    if cmd in ('start', 'stop') and user != 'openquake':
        sys.exit(f'Only user openquake can {cmd} the dbserver '
                 f'but you are {user}')
    if cmd == 'status':
        print('dbserver ' + dbserver.get_status())
    elif cmd == 'stop':
        if dbserver.stop_server():
            print('dbserver stopped')
        else:
            print('dbserver already stopped')
    elif dbserver.get_status() == 'running':
        print('dbserver already running on ' + logs.dbserver_url())
    else:  # start
        logfile = dbserver.run_server(foreground)
        print('dbserver started on %s, log in %s' % (
            logs.dbserver_url(), logfile))


main.cmd = dict(help='dbserver command',
                choices='start stop status'.split())
main.foreground = 'stay in foreground'
