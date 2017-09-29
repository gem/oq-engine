#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (C) 2016-2017 GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time
import socket
import os.path
import sqlite3
import logging
import threading
import subprocess

from openquake.baselib import config, sap, zeromq as z
from openquake.baselib.parallel import safely_call
from openquake.commonlib import logs
from openquake.server.db import actions
from openquake.server import dbapi
from openquake.server import __file__ as server_path
from openquake.server.settings import DATABASE


db = dbapi.Db(sqlite3.connect, DATABASE['NAME'], isolation_level=None,
              detect_types=sqlite3.PARSE_DECLTYPES, timeout=20)
# NB: I am increasing the timeout from 5 to 20 seconds to see if the random
# OperationalError: "database is locked" disappear in the WebUI tests


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

    def worker(self, sock):
        for cmd_ in sock:
            cmd, args = cmd_[0], cmd_[1:]
            if cmd == 'getpid':
                sock.rep((self.pid, None, None))
                continue
            try:
                func = getattr(actions, cmd)
            except AttributeError:
                sock.rep(('Invalid command ' + cmd, ValueError, None))
            else:
                sock.rep(safely_call(func, (self.db,) + args))

    def start(self):
        # start workers
        workers = []
        for _ in range(self.num_workers):
            sock = z.Socket(self.backend, z.zmq.REP, 'connect')
            threading.Thread(target=self.worker, args=(sock,)).start()
            workers.append(sock)
        logging.warn('DB server started with %s on %s, pid=%d',
                     sys.executable, self.frontend, self.pid)
        # start frontend->backend proxy
        try:
            z.zmq.proxy(z.bind(self.frontend, z.zmq.ROUTER),
                        z.bind(self.backend, z.zmq.DEALER))
        except (KeyboardInterrupt, z.zmq.ZMQError):
            for sock in workers:
                sock.running = False
            logging.warn('DB server stopped')


def different_paths(path1, path2):
    path1 = os.path.realpath(path1)  # expand symlinks
    path2 = os.path.realpath(path2)  # expand symlinks
    # don't care about the extension (it may be .py or .pyc)
    return os.path.splitext(path1)[0] != os.path.splitext(path2)[0]


def get_status(address=None):
    """
    Check if the DbServer is up.

    :param address: pair (hostname, port)
    :returns: 'running' or 'not-running'
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = config.dbserver
    try:
        err = sock.connect_ex(address or (s.host, s.port))
    finally:
        sock.close()
    return 'not-running' if err else 'running'


def check_foreign():
    """
    Check if we the DbServer is the right one
    """
    if not config.dbserver.multi_user:
        remote_server_path = logs.dbcmd('get_path')
        if different_paths(server_path, remote_server_path):
            return('You are trying to contact a DbServer from another'
                   ' instance (got %s, expected %s)\n'
                   'Check the configuration or stop the foreign'
                   ' DbServer instance') % (remote_server_path, server_path)


def ensure_on():
    """
    Start the DbServer if it is off
    """
    if get_status() == 'not-running':
        if config.dbserver.multi_user:
            sys.exit('Please start the DbServer: '
                     'see the documentation for details')
        # otherwise start the DbServer automatically
        subprocess.Popen([sys.executable, '-m', 'openquake.server.dbserver',
                          '-l', 'INFO'])

        # wait for the dbserver to start
        waiting_seconds = 10
        while get_status() == 'not-running':
            if waiting_seconds == 0:
                sys.exit('The DbServer cannot be started after 10 seconds. '
                         'Please check the configuration')
            time.sleep(1)
            waiting_seconds -= 1


@sap.Script
def run_server(dbhostport=None, dbpath=None, logfile=DATABASE['LOG'],
               loglevel='WARN'):
    """
    Run the DbServer on the given database file and port. If not given,
    use the settings in openquake.cfg.
    """
    if dbhostport:  # assume a string of the form "dbhost:port"
        dbhost, port = dbhostport.split(':')
        addr = (dbhost, int(port))
        DATABASE['PORT'] = int(port)
    else:
        addr = (config.dbserver.host, config.dbserver.port)

    if dbpath:
        DATABASE['NAME'] = dbpath

    # create the db directory if needed
    dirname = os.path.dirname(DATABASE['NAME'])
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # create and upgrade the db if needed
    db('PRAGMA foreign_keys = ON')  # honor ON DELETE CASCADE
    actions.upgrade_db(db)
    # the line below is needed to work around a very subtle bug of sqlite;
    # we need new connections, see https://github.com/gem/oq-engine/pull/3002
    db.close()

    # configure logging and start the server
    logging.basicConfig(level=getattr(logging, loglevel), filename=logfile)
    try:
        DbServer(db, addr).start()
    finally:
        db.close()

run_server.arg('dbhostport', 'dbhost:port')
run_server.arg('dbpath', 'dbpath')
run_server.arg('logfile', 'log file')
run_server.opt('loglevel', 'WARN or INFO')

if __name__ == '__main__':
    run_server.callfunc()
