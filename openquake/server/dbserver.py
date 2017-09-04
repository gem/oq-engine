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
import sqlite3
import os.path
import logging
import subprocess
from openquake.baselib import sap, zeromq
from openquake.baselib.parallel import safely_call
from openquake.hazardlib import valid
from openquake.commonlib import config, logs
from openquake.server.db import actions
from openquake.server import dbapi
from openquake.server import __file__ as server_path
from openquake.server.settings import DATABASE

zmq = os.environ.get(
    'OQ_DISTRIBUTE', config.get('distribution', 'oq_distribute')) == 'zmq'
if zmq:
    from openquake.baselib import zeromq as z


class DbServer(object):
    """
    A server collecting the received commands into a queue
    """
    def __init__(self, db, address, authkey):
        self.db = db
        self.address = 'tcp://%s:%s' % address
        host, self.port = address
        self.authkey = authkey  # this is not used for the moment
        if host == 'localhost':
            host = '127.0.0.1'
        self.frontend_url = 'tcp://%s:%s' % (host, self.port + 1)
        self.backend_url = 'tcp://%s:%s' % (host, self.port + 2)

    def __enter__(self):
        if zmq:
            # create the workers
            self.workers = 0
            rpython = (config.get('dbserver', 'remote_python') or
                       sys.executable)
            for host, sshport, cores in config.get_host_cores():
                if host == '127.0.0.1':  # localhost
                    args = [sys.executable]
                else:
                    args = ['ssh', host, '-p', sshport, rpython]
                args += ['-m', 'openquake.baselib.zeromq',
                         self.backend_url, cores]
                logging.warn('starting ' + ' '.join(args))
                subprocess.Popen(args)
                self.workers += 1
            z.Process(z.proxy, self.frontend_url, self.backend_url).start()
            logging.warn('zmq proxy started on ports %d, %d',
                         self.port + 1, self.port + 2)
        return self

    def __exit__(self, etype, exc, tb):
        if zmq:
            with z.context as c, c.connect(self.frontend_url, z.DEALER) as s:
                for i in range(self.workers):
                    logging.warning('stopping zmq worker %d', i)
                    s.send_pyobj(('stop', i))
                time.sleep(1)  # wait a bit for the stop to be sent

    def loop(self):
        logging.warn('DB server started with %s, listening on %s...',
                     sys.executable, self.address)
        sock = zeromq.ReplySocket(self.address)
        for cmd_ in sock:
            cmd, args = cmd_[0], cmd_[1:]
            logging.debug('Got ' + str(cmd_))
            try:
                func = getattr(actions, cmd)
            except AttributeError:
                sock.reply(('Invalid command ' + cmd, ValueError, None))
            else:
                sock.reply(safely_call(func, (self.db,) + args))
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
    try:
        err = sock.connect_ex(address or config.DBS_ADDRESS)
    finally:
        sock.close()
    return 'not-running' if err else 'running'


def check_foreign():
    """
    Check if we the DbServer is the right one
    """
    if not config.flag_set('dbserver', 'multi_user'):
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
        if valid.boolean(config.get('dbserver', 'multi_user')):
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
        addr = config.DBS_ADDRESS

    if dbpath:
        DATABASE['NAME'] = dbpath

    # create the db directory if needed
    dirname = os.path.dirname(DATABASE['NAME'])
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # create and upgrade the db if needed
    db = dbapi.Db(sqlite3.connect, DATABASE['NAME'], isolation_level=None,
                  detect_types=sqlite3.PARSE_DECLTYPES)
    db('PRAGMA foreign_keys = ON')  # honor ON DELETE CASCADE
    actions.upgrade_db(db)

    # configure logging and start the server
    logging.basicConfig(level=getattr(logging, loglevel), filename=logfile)
    try:
        with DbServer(db, addr, config.DBS_AUTHKEY) as dbs:
            dbs.loop()
    finally:
        db.conn.close()

run_server.arg('dbhostport', 'dbhost:port')
run_server.arg('dbpath', 'dbpath')
run_server.arg('logfile', 'log file')
run_server.opt('loglevel', 'WARN or INFO')

if __name__ == '__main__':
    run_server.callfunc()
