# vim: tabstop=4 shiftwidth=4 softtabstop=4

from eventlet import queue

class Grid(object):
    def __init__(self, *args, **kwargs):
        self.cellsize = 0.1
        self.__dict__.update(kwargs)
    
    @property
    def xulcorner(self):
        return self.xllcorner
        
    @property
    def yulcorner(self):
        return self.yllcorner - (self.cellsize * self.ncols)

def ComputeGrid(object):
    def __init__(self, cell_factory, pool):
        self.queue = queue.Queue()
        self.cell_factory = cell_factory
        self.pool = pool
        self._cells = {}

    def cell(self, key):
        """Get or create a cell by key"""
        if key not in self._cells:
            new_cell = self._create_new_cell(key)
            self._cells[key] = new_cell
        return self._cells[key]

    def compute(self, waiting, callback):
        compute_done = event.Event()
        self.pool.spawn(self._compute, waiting, callback, finish=compute_done)
        return compute_done

    def _compute(self, waiting, callback, finish):
        while [x for x in waiting if not x.ready()] or not self.queue.empty():
            computation = self.queue.get()
            cell, result = computation.compute()
            callback(cell, result)

        finish.send()

    
    def _create_new_cell(self, key):
        """Create a new cell and queue it for computation.""" 
        new_cell = self.cell_factory(key)

        def _queue_computation():
            self.queue.put(new_cell)
        
        self.pool.spawn(_queue_computation)
        return new_cell
