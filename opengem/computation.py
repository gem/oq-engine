# vim: tabstop=4 shiftwidth=4 softtabstop=4

from eventlet import event
from eventlet import queue

class Computation(object):
    def __init__(self, pool, keys=None):
        self.pool = pool
        self.result = event.Event()
        if keys is None:
            keys = []

        self.data = {}
        for k in keys:
            self._data[k] = event.Event()
    
    def receive(self, key, _data):
        self._data[key].send(_data)

    def compute(self):
        # wait on all input
        data = [(k, v.wait()) for k, v in self._data.iteritems()]
        
        # do the computation
        result = self._compute(**data)

        # send to finished
        self.result.send(result)


class Grid(object):
    def __init__(self, pool, cell_factory):
        self.pool = pool
        self.cell_factory = cell_factory
        self._cells = {}
        self._queue = queue.Queue()

    def cell(self, key):
        if key not in self._cells:
            self._cells = self._new_cell(key)

    def _new_cell(self, key):
        cell = self.cell_factory(self.pool, key)
        return cell

