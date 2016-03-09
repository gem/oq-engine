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
from multiprocessing.connection import Client, Listener
from openquake.baselib.hdf5 import Hdf5Dataset
from openquake.commonlib.datastore import read


class DataManager(object):

    @classmethod
    def listen(cls, address, authkey):
        print 'PPPPPPPPPPPPPPPP'
        self = cls(address, authkey)
        with self:
            self.loop()

    def __init__(self, address, authkey):
        self.address = address
        self.authkey = authkey

    def __enter__(self):
        print('Listening on %s...' % str(self.address))
        self.listener = Listener(self.address, authkey=self.authkey)
        return self

    def __exit__(self, etype, exc, tb):
        client = Client(self.address, authkey=self.authkey)
        client.send((sys.exit, 0))
        client.close()
        self.listener.close()
        for ds in self.dstore.values():
            ds.close()

    def loop(self):
        self.dstore = {}
        while True:
            try:
                conn = self.listener.accept()
                cmd = conn.recv()
            except BaseException:
                conn.close()
                raise
            call = cmd[0]
            if callable(call):
                call(*cmd[1:])
                continue
            args = cmd[1:-1]
            calc_id = cmd[-1]
            try:
                self.datastore = self.dstore[calc_id]
            except KeyError:
                self.datastore = self.dstore[calc_id] = read(calc_id, 'r+')
            else:  # assume `call` is a method name, like `save` or `extend`
                getattr(self, call)(*args)

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
