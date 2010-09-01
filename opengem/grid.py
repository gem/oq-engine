# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Collection of base classes for processing 
spatially-related data."""


from shapely import geometry
from shapely import wkt

import flags
import geohash

flags.DEFINE_integer('distance_precision', 6, "Points within this precision will be considered the same point")
FLAGS = flags.FLAGS

Point = geometry.Point

from eventlet import queue

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


class Site(geometry.Point):
    """Site is a dictionary-keyable point"""
    def __init__(self, longitude, latitude):
        self.point = Point(longitude, latitude)
    
    @property
    def longitude(self):
        return self.point.x
        
    @property
    def latitude(self):
        return self.point.y

    def __eq__(self, other):
        return self.hash() == other.hash()
    
    def hash(self):
        return geohash.encode(self.point.y, self.point.x, precision=FLAGS.distance_precision)
    
    def __cmp__(self, other):
        return self.hash() == other.hash()
    
    def __repr__(self):
        return self.hash()
        
    def __str__(self):
        return self.hash()


class Sites(object):
    """A collection of Site objects"""
    def __init__(self):
        pass
    
    
