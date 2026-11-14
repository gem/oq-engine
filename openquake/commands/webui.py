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

import psutil

from openquake.baselib import config, general
from openquake.commonlib import dbapi
from openquake.commonlib.auth import API_KEY
from openquake.server.db import actions
from openquake.server.utils import check_webserver_running

commands = ['start', 'status', 'stop']


# the health check uses an internal endpoint that is always served with
# status 200, even when the WebUI is disabled (WEBUI = False).
# Calculation 0 does not exist, so the log size returned is always 0:
# only the status code matters here, not the value
def _health_url(hostport):
    return 'http://' + hostport + '/v0/calc/0/log/size'


def _listens(proc, port):
    """True if the process holds a TCP socket listening on the port."""
    try:
        return any(conn.status == psutil.CONN_LISTEN and
                   conn.laddr.port == port
                   for conn in proc.net_connections(kind='tcp'))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def _find_webui_process(hostport):
    """
    Find the topmost process listening on the requested port. With gunicorn
    the master and the workers share the socket, and psutil reports it only
    for a worker: going up to the master, we stop the whole server.
    """
    _host, port = hostport.rsplit(':', 1)
    port = int(port)
    for connection in psutil.net_connections(kind='tcp'):
        if (connection.status == psutil.CONN_LISTEN and
                connection.laddr.port == port):
            try:
                proc = psutil.Process(connection.pid)
                parent = proc.parent()
                while parent is not None and _listens(parent, port):
                    proc, parent = parent, parent.parent()
                return proc
            except psutil.NoSuchProcess:
                return None
    return None


def _status(hostport):
    """Print whether the WebUI responds on the requested address."""
    running = check_webserver_running(
        _health_url(hostport), max_retries=1, warn=False)
    print('running' if running else 'stopped')
    return running


def _stop(hostport):
    """Stop the process serving the requested WebUI port."""
    process = _find_webui_process(hostport)
    if process is None:
        print('WebUI is not running')
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except psutil.TimeoutExpired:
        process.kill()
        process.wait()
    print('stopped')


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

    os.environ.setdefault('OQ_API_KEY', API_KEY)
    api_host, api_port = hostport.rsplit(':', 1)
    if api_host == '0.0.0.0':
        api_host = '127.0.0.1'
    os.environ.setdefault(
        'OQ_WEBAPI_SERVER', 'http://%s:%s' % (api_host, api_port))
    dbpath = os.path.realpath(os.path.expanduser(config.server.dbfile))
    if os.path.isfile(dbpath) and not os.access(dbpath, os.W_OK):
        sys.exit('This command must be run by the proper user: '
                 'see the documentation for details')
    actions.upgrade_db(dbapi.db)
    print('Starting, using version %s' % general.engine_version())
    runserver(hostport, skip_browser)


main.cmd = dict(help='webui command', choices=commands)
main.hostport = 'a string of the form <hostname:port>'
main.skip_browser = 'do not automatically open the browser'
