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
from multiprocessing.connection import Listener

from openquake.commonlib.parallel import safely_call
from openquake.engine.utils import config
from openquake.server.db import actions

DEFAULT_LOG_LEVEL = 'progress'

# global commands

exit = sys.exit
info = logging.info


class DbServer(object):
    """
    A server receiving and executing commands. Errors are trapped and
    we send back to the client pairs (result, exctype) for each command
    received. `exctype` is None if there is no exception, otherwise it
    is an exception class and `result` is an error string containing the
    traceback.
    """
    def __init__(self, address, authkey):
        self.address = address
        self.authkey = authkey

    def loop(self):
        listener = Listener(self.address, authkey=self.authkey)
        logging.info('Listening on %s:%d...' % self.address)
        try:
            while True:
                try:
                    conn = listener.accept()
                except KeyboardInterrupt:
                    break
                except:
                    # unauthenticated connection, for instance by a port
                    # scanner such as the one in manage.py
                    continue
                try:
                    cmd = conn.recv()  # a list [name, arg1, ... argN]
                    name = cmd[0]
                    if name == '@stop':
                        # this is a somewaht special command, so I am using
                        # the convention of prepending an `@` to its name
                        # in the future I may add more special commands
                        conn.send((None, None))
                        break
                    else:  # call the function named `name` in db.actions
                        args = cmd[1:]
                        func = getattr(actions, name)
                    # call the function by trapping any error
                    res, etype, _ = safely_call(func, args)
                    if etype:
                        logging.error(res)
                    # send back the result and the exception class
                    conn.send((res, etype))
                finally:
                    conn.close()
        finally:
            listener.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    DbServer(config.DBS_ADDRESS, config.DBS_AUTHKEY).loop()
