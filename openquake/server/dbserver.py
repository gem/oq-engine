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
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
import logging
from Queue import Queue
from threading import Thread
from multiprocessing.connection import Listener

from openquake.commonlib.parallel import safely_call
from openquake.engine import config
from openquake.server.db import actions
from django.db import connection

DEFAULT_LOG_LEVEL = 'progress'

# global commands

exit = sys.exit
info = logging.info
queue = Queue()


def manage_commands():
    """
    Execute the received commands in a separated thread. Errors are trapped
    and we send back to the client pairs (result, exctype) for each command
    received. `exctype` is None if there is no exception, otherwise it
    is an exception class and `result` is an error string containing the
    traceback.
    """
    connection.cursor()  # bind the db
    while True:
        conn, cmd = queue.get()
        if cmd == ('@stop',):
            # this is a somewhat special command, so I am using
            # the convention of prepending an `@` to its name
            # in the future I may add more special commands
            conn.send((None, None))
            conn.close()
            return

        # execute the command by trapping any possible exception
        func = getattr(actions, cmd[0])
        res, etype, _ = safely_call(func, cmd[1:])

        # logging
        logging.info('Got %s', str(cmd))
        if etype:
            logging.error(res)

        # send back the result and the exception class
        conn.send((res, etype))
        conn.close()


class DbServer(object):
    """
    A server collecting the received commands into a queue
    """
    def __init__(self, address, authkey):
        self.address = address
        self.authkey = authkey
        self.thread = Thread(target=manage_commands)

    def loop(self):
        listener = Listener(self.address, backlog=5, authkey=self.authkey)
        logging.info('DB server listening on %s:%d...' % self.address)
        self.thread.start()
        cmd = [None]
        try:
            while cmd[0] != '@stop':
                try:
                    conn = listener.accept()
                except KeyboardInterrupt:
                    break
                except:
                    # unauthenticated connection, for instance by a port
                    # scanner such as the one in manage.py
                    continue
                cmd = conn.recv()  # a tuple (name, arg1, ... argN)
                queue.put((conn, cmd))
        finally:
            listener.close()
            self.thread.join()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if sys.argv[1:]:  # assume sys.argv[1] has the form fname:port
        from openquake.server.settings import DATABASE
        fname, port = sys.argv[1].split(':')
        addr = (DATABASE['HOST'], int(port))
        DATABASE['NAME'] = fname
        DATABASE['PORT'] = int(port)
    else:
        addr = config.DBS_ADDRESS
    DbServer(addr, config.DBS_AUTHKEY).loop()
