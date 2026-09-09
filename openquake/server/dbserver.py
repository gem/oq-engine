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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
import signal
import logging
import getpass
import threading
import subprocess
import requests

from openquake.baselib import (
    config, zeromq as z, workerpool as w, parallel as p)
from openquake.baselib.general import socket_ready, detach_process
from openquake.hazardlib import valid
from openquake.commonlib import logs
from openquake.commonlib.logs import WORKER_ACTIONS
from openquake.server.db import actions
from openquake.commonlib.dbapi import db
from openquake.server import __file__ as server_path


def start_http_server(loglevel):
    """Start the openquake API served by Uvicorn."""
    host = config.dbserver.host
    port = getattr(config.dbserver, 'http_port', 8800)
    return subprocess.Popen([
        sys.executable, '-m', 'uvicorn',
        'openquake.server.asgi:app',
        '--host', host,
        '--port', str(port),
        '--log-level', loglevel.lower(),
    ])


def stop_http_server(process):
    """Stop the Uvicorn process and wait for it to exit."""
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


class DbServer(object):
    """
    A server collecting the received commands into a queue
    """
    def __init__(self, db, address, num_workers=5):
        self.db = db
        self.frontend = 'tcp://%s:%s' % address
        self.backend = 'inproc://dbworkers'
        self.num_workers = num_workers
        self.pid = os.getpid()

    def dworker(self, sock):
        # a database worker responding to commands
        with sock:
            for cmd_ in sock:
                cmd, args = cmd_[0], cmd_[1:]
                if cmd == 'getpid':
                    sock.send(self.pid)
                    continue
                elif cmd in WORKER_ACTIONS:
                    master = w.WorkerMaster(args[0])  # zworkers
                    msg = getattr(master, cmd[8:])()
                    sock.send(msg)
                    continue
                func = getattr(actions, cmd)
                res = p.safely_call(func, (self.db,) + args)
                sock.send(res)

    def start(self):
        """
        Start database worker threads
        """
        # give a nice name to the process
        w.setproctitle('oq-dbserver')

        dworkers = []
        for _ in range(self.num_workers):
            sock = z.Socket(self.backend, z.zmq.REP, 'connect')
            threading.Thread(target=self.dworker, args=(sock,)).start()
            dworkers.append(sock)
        logging.warning('DB server started with %s on %s, pid %d',
                        sys.executable, self.frontend, self.pid)
        # start frontend->backend proxy for the database workers
        try:
            z.zmq.proxy(z.bind(self.frontend, z.zmq.ROUTER),
                        z.bind(self.backend, z.zmq.DEALER))
        except (KeyboardInterrupt, z.zmq.ContextTerminated):
            for sock in dworkers:
                sock.running = False
                if hasattr(sock, 'zsocket'):  # actually used
                    sock.zsocket.close()
            logging.warning('DB server stopped')
        finally:
            self.stop()

    def stop(self):
        """
        Stop the DbServer
        """
        self.db.close()


def different_paths(path1, path2):
    path1 = os.path.realpath(path1)  # expand symlinks
    path2 = os.path.realpath(path2)  # expand symlinks
    # don't care about the extension (it may be .py or .pyc)
    return os.path.splitext(path1)[0] != os.path.splitext(path2)[0]


def get_status(address=None):
    """
    Check if both the DbServer and its HTTP API are up.

    :param address: pair (hostname, port)
    :returns: 'running', 'degraded', or 'not-running'
    """
    address = address or valid.host_port()
    zmq_running = socket_ready(address)
    http_running = _http_ready()
    if zmq_running and http_running:
        return 'running'
    if zmq_running:
        return 'degraded'
    return 'not-running'


def _http_ready():
    """Return whether the FastAPI service responds on its configured port."""
    host = config.dbserver.host
    port = getattr(config.dbserver, 'http_port', 8800)
    try:
        response = requests.get(
            f'http://{host}:{port}/v1/engine_version', timeout=1)
        return response.ok
    except requests.RequestException:
        return False


def _foreign_server_error():
    """Return the error shown when the configured server is foreign."""
    return ('You are trying to contact a DbServer from another installation. '
            'Check the configuration or stop the foreign DbServer instance')


def check_foreign():
    """
    Check that the DbServer belongs to this installation.

    New servers expose a stable, non-sensitive installation identity. The
    path-based check is retained for compatibility with older DbServers.
    """
    if config.multi_user or os.environ.get('OQ_DATABASE'):
        return

    try:
        identity = logs.dbcmd('get_installation_id')
    except Exception:
        # ``get_installation_id`` was added after ``get_path``. Keep this fallback
        # while old DbServers may still be running.
        remote_server_path = logs.dbcmd('get_path')
        if different_paths(server_path, remote_server_path):
            return _foreign_server_error()
    else:
        if identity.get('installation_id') != actions.installation_id(db):
            return _foreign_server_error()


def ensure_on():
    """
    Start the DbServer if it is off
    """
    if (os.environ.get('OQ_DATABASE', config.dbserver.host) == '127.0.0.1'
        and getpass.getuser() != 'openquake'):
        print('Using local database')
        actions.upgrade_db(db)
        return
    if get_status() == 'not-running':
        if config.multi_user and getpass.getuser() != 'openquake':
            sys.exit('Please start the DbServer: '
                     'see the documentation for details')
        # otherwise start the DbServer automatically; NB: I tried to use
        # multiprocessing.Process(target=run_server).start() and apparently
        # it works, but then run-demos.sh hangs after the end of the first
        # calculation, but only if the DbServer is started by oq engine (!?)
        subprocess.Popen([sys.executable, '-m', 'openquake.commands',
                          'dbserver', 'start'])

        # wait for the dbserver to start
        waiting_seconds = 30
        while get_status() == 'not-running':
            if waiting_seconds == 0:
                sys.exit('The DbServer cannot be started after 30 seconds. '
                         'Please check the configuration')
            time.sleep(1)
            waiting_seconds -= 1


def run_server(dbhostport=None, loglevel='WARN', foreground=False):
    """
    Run the DbServer on the given database file and port. If not given,
    use the settings in openquake.cfg.
    """
    # configure the logging first of all
    logging.basicConfig(level=getattr(logging, loglevel.upper()))

    if dbhostport:  # assume a string of the form "dbhost:port"
        dbhost, port = dbhostport.split(':')
        addr = (dbhost, int(port))
    else:
        addr = (config.dbserver.host, config.dbserver.port)

    # create the db directory if needed
    dirname = os.path.dirname(os.path.expanduser(config.dbserver.file))
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # create and upgrade the db if needed
    db('PRAGMA foreign_keys = ON')  # honor ON DELETE CASCADE
    actions.upgrade_db(db)
    # the line below is needed to work around a very subtle bug of sqlite;
    # we need new connections, see https://github.com/gem/oq-engine/pull/3002
    db.close()

    # start the dbserver
    if hasattr(os, 'fork') and not (config.multi_user or foreground):
        # needed for https://github.com/gem/oq-engine/issues/3211
        # but only if multi_user = False, otherwise init/supervisor
        # will loose control of the process
        detach_process()
    http_process = start_http_server(loglevel)
    try:
        DbServer(db, addr).start()  # expects to be killed with CTRL-C
    finally:
        stop_http_server(http_process)
