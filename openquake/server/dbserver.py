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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
import sqlite3
import logging
import threading
import subprocess

from openquake.baselib import config, sap, zeromq as z, workerpool as w
from openquake.baselib.general import socket_ready, detach_process
from openquake.baselib.parallel import safely_call
from openquake.commonlib import logs
from openquake.server.db import actions
from openquake.server import dbapi
from openquake.server import __file__ as server_path


db = dbapi.Db(sqlite3.connect, os.path.expanduser(config.dbserver.file),
              isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES,
              timeout=20)
db.cmd = lambda action, *args: getattr(actions, action)(db, *args)
# NB: I am increasing the timeout from 5 to 20 seconds to see if the random
# OperationalError: "database is locked" disappear in the WebUI tests

ZMQ = os.environ.get(
    'OQ_DISTRIBUTE', config.distribution.oq_distribute) == 'zmq'

DBSERVER_PORT = int(os.environ.get('OQ_DBSERVER_PORT') or config.dbserver.port)


class DbServer(object):
    """
    A server collecting the received commands into a queue
    """
    def __init__(self, db, address, num_workers=5):
        self.db = db
        self.master_host = address[0]
        self.frontend = 'tcp://%s:%s' % address
        self.backend = 'inproc://dbworkers'
        self.num_workers = num_workers
        self.pid = os.getpid()
        self.master = w.WorkerMaster(config.dbserver.host,
                                     **config.zworkers)

    def dworker(self, sock):
        # a database worker responding to commands
        with sock:
            for cmd_ in sock:
                cmd, args = cmd_[0], cmd_[1:]
                if cmd == 'getpid':
                    sock.send(self.pid)
                    continue
                try:
                    func = getattr(actions, cmd)
                except AttributeError:  # missing action
                    sock.send(safely_call(self.db, (cmd,) + args))
                else:
                    sock.send(safely_call(func, (self.db,) + args))

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
        if ZMQ:
            # start task_in->task_out streamer thread
            c = config.zworkers
            threading.Thread(
                target=w._streamer,
                args=(self.master_host, c.task_in_port, c.task_out_port)
            ).start()
            logging.warning('Task streamer started from %s -> %s',
                            c.task_in_port, c.task_out_port)

            # start zworkers and wait a bit for them
            msg = self.master.start()
            logging.warning(msg)
            time.sleep(1)

        # start frontend->backend proxy for the database workers
        try:
            z.zmq.proxy(z.bind(self.frontend, z.zmq.ROUTER),
                        z.bind(self.backend, z.zmq.DEALER))
        except (KeyboardInterrupt, z.zmq.ZMQError):
            for sock in dworkers:
                sock.running = False
                sock.zsocket.close()
            logging.warning('DB server stopped')
        finally:
            self.stop()

    def stop(self):
        """Stop the DbServer and the zworkers if any"""
        if ZMQ:
            logging.warning(self.master.stop())
            z.context.term()
        self.db.close()


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
    address = address or (config.dbserver.host, DBSERVER_PORT)
    return 'running' if socket_ready(address) else 'not-running'


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
        # otherwise start the DbServer automatically; NB: I tried to use
        # multiprocessing.Process(target=run_server).start() and apparently
        # it works, but then run-demos.sh hangs after the end of the first
        # calculation, but only if the DbServer is started by oq engine (!?)
        subprocess.Popen([sys.executable, '-m', 'openquake.server.dbserver',
                          '-l', 'INFO'])

        # wait for the dbserver to start
        waiting_seconds = 30
        while get_status() == 'not-running':
            if waiting_seconds == 0:
                sys.exit('The DbServer cannot be started after 30 seconds. '
                         'Please check the configuration')
            time.sleep(1)
            waiting_seconds -= 1


@sap.script
def run_server(dbpath=os.path.expanduser(config.dbserver.file),
               dbhostport=None, loglevel='WARN'):
    """
    Run the DbServer on the given database file and port. If not given,
    use the settings in openquake.cfg.
    """
    if dbhostport:  # assume a string of the form "dbhost:port"
        dbhost, port = dbhostport.split(':')
        addr = (dbhost, int(port))
    else:
        addr = (config.dbserver.listen, DBSERVER_PORT)

    # create the db directory if needed
    dirname = os.path.dirname(dbpath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # create and upgrade the db if needed
    db('PRAGMA foreign_keys = ON')  # honor ON DELETE CASCADE
    actions.upgrade_db(db)
    # the line below is needed to work around a very subtle bug of sqlite;
    # we need new connections, see https://github.com/gem/oq-engine/pull/3002
    db.close()

    # reset any computation left in the 'executing' state
    actions.reset_is_running(db)

    # configure logging and start the server
    logging.basicConfig(level=getattr(logging, loglevel))
    DbServer(db, addr).start()  # expects to be killed with CTRL-C


run_server.arg('dbpath', 'dbpath')
run_server.arg('dbhostport', 'dbhost:port')
run_server.opt('loglevel', 'WARN or INFO')

if __name__ == '__main__':
    if hasattr(os, 'fork') and not config.dbserver.multi_user:
        # needed for https://github.com/gem/oq-engine/issues/3211
        # but only if multi_user = False, otherwise init/supervisor
        # will loose control of the process
        detach_process()
    run_server.callfunc()
