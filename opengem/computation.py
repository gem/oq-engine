# vim: tabstop=4 shiftwidth=4 softtabstop=4

from eventlet import event
from eventlet import queue

class Computation(object):
    def __init__(self, pool, cell, data_keys=None):
        self.pool = pool
        self.cell = cell
        self.result = event.Event()

        if data_keys is None:
            data_keys = []

        self._data = {}
        for k in data_keys:
            self._data[k] = event.Event()
    
    def receive(self, key, _data):
        self._data[key].send(_data)

    def compute(self):
        # wait on all input
        data = [(k, v.wait()) for k, v in self._data.iteritems()]
        
        # do the computation
        result = self._compute(**data)

        # send to finished
        self.result.send((self.cell, result))
        return (self.cell, result)


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
        self.pool.spawn(cell.compute)
        self._queue.put(cell.result)
        return cell
    
    def results(self):
        while not self._queue.empty():
            yield self._queue.get().wait()

