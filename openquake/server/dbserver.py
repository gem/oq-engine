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
import requests

from openquake.baselib import config, general
from openquake.commonlib import dbapi, logs
from openquake.server.db import actions

SETTINGS = 'openquake.server.dbserver_settings'


def get_status():
    """
    :returns: 'running' if the DbServer answers, 'not-running' otherwise
    """
    try:
        resp = requests.get(logs.dbserver_url() + '/v0/ping', timeout=10)
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


def run_server():
    """
    Upgrade the database and replace the current process with the DbServer,
    run by the Django development server. In server installations the
    DbServer is the only process upgrading the database and it must be
    started before the WebUI.
    """
    dirname = os.path.dirname(os.path.expanduser(config.dbserver.file))
    os.makedirs(dirname, exist_ok=True)
    actions.upgrade_db(dbapi.db)
    dbapi.db.close()
    hostport = '%s:%s' % (config.dbserver.host, config.dbserver.port)
    # the reload functionality of the Django development server
    # interferes with SIGCHLD and causes zombies, thus it is disabled
    args = [sys.executable, '-m', 'openquake.server.manage', 'runserver',
            hostport, '--noreload']
    env = dict(os.environ, DJANGO_SETTINGS_MODULE=SETTINGS)
    os.execve(sys.executable, args, env)


def stop_server():
    """
    Stop the DbServer listening on the port in openquake.cfg.

    :returns: True if it was running, False otherwise
    """
    return general.stop_listening_process(config.dbserver.port)
