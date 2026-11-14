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

import os
import sys
import subprocess
import webbrowser

from openquake.baselib import config, general, is_server_installation
from openquake.commonlib import dbapi
from openquake.server.db import actions
from openquake.server.utils import check_webserver_running

commands = ['start', 'status', 'stop']


# the health check uses a public route of the WebUI: any answer means that
# the WebUI is running, whatever its status code
def _health_url(hostport):
    return 'http://' + hostport + '/v1/engine_version'


def _status(hostport):
    """Print whether the WebUI responds on the requested address."""
    running = check_webserver_running(
        _health_url(hostport), max_retries=1, warn=False)
    print('running' if running else 'stopped')
    return running


def _stop(hostport):
    """Stop the process serving the requested WebUI port."""
    _host, port = hostport.rsplit(':', 1)
    if general.stop_listening_process(int(port)):
        print('stopped')
    else:
        print('WebUI is not running')


def runserver(hostport=None, skip_browser=False):
    """Start the Django development server and serve the WebUI application."""
    url = 'http://' + hostport
    health = _health_url(hostport)
    if check_webserver_running(health, max_retries=1, warn=False):
        if not skip_browser:
            webbrowser.open(url)
        return

    args = [sys.executable, '-m', 'openquake.server.manage', 'runserver']
    # the reload functionality of the Django development server interferes
    # with SIGCHLD and causes zombies, thus it is disabled
    args.append('--noreload')
    args.append(hostport)
    process = subprocess.Popen(args)
    if not skip_browser and check_webserver_running(health):
        webbrowser.open(url)
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
    if process.returncode not in (0, -15):
        sys.exit(process.returncode)


def main(cmd, hostport='127.0.0.1:8800', skip_browser: bool = False):
    """
    Start the webui server in foreground. Other webui commands can be launched
    after activating the openquake virtual environment, using Django’s
    command-line utility for administrative tasks, e.g.:
    manage.py <command> [options]
    """
    if cmd == 'status':
        _status(hostport)
        return
    if cmd == 'stop':
        _stop(hostport)
        return

    dbpath = os.path.realpath(os.path.expanduser(config.dbserver.file))
    if os.path.isfile(dbpath) and not os.access(dbpath, os.W_OK):
        sys.exit('This command must be run by the proper user: '
                 'see the documentation for details')
    # in server installations the database is upgraded by the DbServer,
    # which must be started before the WebUI
    if not is_server_installation():
        actions.upgrade_db(dbapi.db)
        # reset the computations left in the 'executing' state; this is
        # not done in server installations, where users may be running
        # calculations while the services are restarted
        actions.reset_is_running(dbapi.db)
    print('Starting, using version %s' % general.engine_version())
    runserver(hostport, skip_browser)


main.cmd = dict(help='webui command', choices=commands)
main.hostport = 'a string of the form <hostname:port>'
main.skip_browser = 'do not automatically open the browser'
