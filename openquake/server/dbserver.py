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
"""
The DbServer is a Django service serving the v0 API (see dbserver_urls.py)
on the host and port of the [dbserver] section of openquake.cfg. It is
used in server installations by the regular users, which cannot write on
the database; the user openquake (i.e. the WebUI) and the user and devel
installations access the database directly.
"""
import os
import sys
import time
import subprocess
import requests

from openquake.baselib import config, general
from openquake.commonlib import dbapi, logs
from openquake.server.db import actions
from openquake.server.utils import get_or_create_django_secret_key

SETTINGS = 'openquake.server.dbserver_settings'


def get_status():
    """
    :returns: 'running' if the DbServer answers, 'not-running' otherwise
    """
    try:
        with logs.dbserver_session() as session:
            resp = session.get(logs.dbserver_url() + '/v0/ping', timeout=10)
    except requests.RequestException:
        return 'not-running'
    return 'running' if resp.ok else 'not-running'


def wait_running(seconds=30):
    """
    Wait until the DbServer answers.

    :param seconds: maximum number of seconds to wait
    :raises RuntimeError: if the DbServer does not answer in time
    """
    for _ in range(seconds):
        if get_status() == 'running':
            return
        time.sleep(1)
    raise RuntimeError(
        'The DbServer is not running on %s: it must be started before the '
        'WebUI with `sudo systemctl start openquake-dbserver`'
        % logs.dbserver_url())


def run_server(foreground=False):
    """
    Upgrade the database and run the DbServer with the Django development
    server. In foreground mode (used by the systemd service) the current
    process is replaced by the server, otherwise the server is started in
    background with a log file in the datadir. In server installations the
    DbServer is the only process upgrading the database and it must be
    started before the WebUI.

    :returns: the path of the log file, in background mode
    """
    # get the Django secret key first, so that a missing key is reported
    # before touching the database
    env = dict(os.environ, DJANGO_SETTINGS_MODULE=SETTINGS,
               DJANGO_SECRET_KEY=get_or_create_django_secret_key())
    dirname = os.path.dirname(os.path.expanduser(config.dbserver.file))
    os.makedirs(dirname, exist_ok=True)
    actions.upgrade_db(dbapi.db)
    dbapi.db.close()
    hostport = '%s:%s' % (config.dbserver.host, config.dbserver.port)
    # the reload functionality of the Django development server
    # interferes with SIGCHLD and causes zombies, thus it is disabled
    args = [sys.executable, '-m', 'openquake.server.manage', 'runserver',
            hostport, '--noreload']
    if foreground:
        os.execve(sys.executable, args, env)
    logfile = os.path.join(logs.get_datadir(), 'dbserver.log')
    with open(logfile, 'a') as log:
        subprocess.Popen(args, env=env, stdout=log,
                         stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wait_running()
    except RuntimeError:
        sys.exit('The DbServer could not start in 30 seconds, see %s'
                 % logfile)
    return logfile


def stop_server():
    """
    Stop the DbServer listening on the port in openquake.cfg.

    :returns: True if it was running, False otherwise
    """
    return general.stop_listening_process(config.dbserver.port)
