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
import subprocess
import webbrowser

from openquake.baselib import sap, config
from openquake.server import dbserver
from openquake.server.utils import check_webserver_running

commands = ['start', 'migrate', 'createsuperuser', 'collectstatic']


def rundjango(subcmd, hostport=None, skip_browser=False):
    args = [sys.executable, '-m', 'openquake.server.manage', subcmd]
    if subcmd == 'start':
        # the reload functionality of the Django development server interferes
        # with SIGCHLD and causes zombies, thus it is disabled
        args.append('--noreload')
    if hostport:
        args.append(hostport)
    p = subprocess.Popen(args)
    if subcmd == 'runserver' and not skip_browser:
        url = 'http://' + hostport
        if check_webserver_running(url):
            webbrowser.open(url)
    p.wait()

    if p.returncode != 0:
        sys.exit(p.returncode)


@sap.script
def webui(cmd, hostport='127.0.0.1:8800', skip_browser=False):
    """
    start the webui server in foreground or perform other operation on the
    django application
    """
    dbpath = os.path.realpath(os.path.expanduser(config.dbserver.file))
    if os.path.isfile(dbpath) and not os.access(dbpath, os.W_OK):
        sys.exit('This command must be run by the proper user: '
                 'see the documentation for details')
    if cmd == 'start':
        dbserver.ensure_on()  # start the dbserver in a subprocess
        rundjango('runserver', hostport, skip_browser)
    elif cmd in commands:
        rundjango(cmd)


webui.arg('cmd', 'webui command', choices=commands)
webui.arg('hostport', 'a string of the form <hostname:port>')
webui.flg('skip_browser', 'do not automatically open the browser')
