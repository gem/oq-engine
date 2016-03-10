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
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.connection import Client, Listener

from openquake.baselib.hdf5 import Hdf5Dataset
from openquake.commonlib.datastore import read
from openquake.engine.utils import config

# recommended setting for development
executor = ThreadPoolExecutor(max_workers=1)

# global commands

exit = sys.exit
info = logging.info


class CmdServer(object):

    @classmethod
    def listen(cls, address, authkey):
        self = cls(address, authkey)
        with self:
            self.loop()

    def __init__(self, address, authkey):
        self.address = address
        self.authkey = authkey

    def stop(self):
        client = Client(self.address, authkey=self.authkey)
        client.send(('exit', 0))
        client.close()

    def loop(self):
        dstore = {}
        listener = Listener(self.address, authkey=self.authkey)
        print('Listening on %s...' % str(self.address))
        try:
            while True:
                conn = listener.accept()
                try:
                    cmd = conn.recv()
                finally:
                    conn.close()
                name = cmd[0]
                if name.startswith('.'):  # method
                    args = cmd[1:-1]
                    calc_id = cmd[-1]
                    try:
                        self.datastore = dstore[calc_id]
                    except KeyError:
                        ds = read(calc_id, 'r+')
                        self.datastore = dstore[calc_id] = ds
                    getattr(self, name[1:])(*args)
                else:  # global function
                    globals()[name](*cmd[1:])
        finally:
            listener.close()
            for ds in dstore.values():
                ds.close()

    def save(self, key, array):
        """
        :param key: datastore key
        :param array: an array to save for the given key
        """
        self.datastore[key] = array
        self.datastore.flush()

    def extend(self, key, array):
        """
        :param key: datastore key
        :param array: an array extending the dataset with the given key
        """
        Hdf5Dataset(self.datastore.hdf5[key]).extend(array)
        self.datastore.flush()


if __name__ == '__main__':
    port = int(config.get('cmdserver', 'port'))
    authkey = config.get('cmdserver', 'authkey')
    logging.basicConfig(level=logging.INFO)
    CmdServer(('', port), authkey).loop()
