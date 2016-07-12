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
from openquake.engine import config
from openquake.server.dbserver import get_status
from openquake.commands import dbserver


def rundjango(subcmd, hostport=None):
    args = [sys.executable, '-m', 'openquake.server.manage', subcmd]
    if hostport:
        args.append(hostport)
    subprocess.call(args)


@sap.Script
def webui(cmd, hostport='127.0.0.1:8800'):
    """
    start the webui server in foreground or perform other operation on the
    django application
    """
    dbstatus = get_status()
    if dbstatus == 'not-running':
        if valid.boolean(config.get('dbserver', 'multi_user')):
            sys.exit('Please start the DbServer: '
                     'see the documentation for details')
        dbserver.runserver()

    if cmd == 'start':
        rundjango('runserver', hostport)
    elif cmd == 'syncdb':
        rundjango('syncdb')

webui.arg('cmd', 'webui command', choices='start syncdb'.split())
webui.arg('hostport', 'a string of the form <hostname:port>')
