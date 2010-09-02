# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Collection of base classes for processing 
spatially-related data."""


from shapely import geometry
from shapely import wkt

import flags
import geohash

flags.DEFINE_integer('distance_precision', 12, "Points within this geohash precision will be considered the same point")
FLAGS = flags.FLAGS

Point = geometry.Point

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
        return "<Site(%s, %s)>" % (self.longitude, self.latitude)


class Sites(object):
    """A collection of Site objects"""
    def __init__(self):
        pass
    

class Curve(object):
    """This class defines a curve (discrete function)

    used in the risk domain.
    """

    def __init__(self, values):
        self.values = values

    def __eq__(self, other):
        return self.values == other.values

    @property
    def domain(self):
        """Returns the domain values of this curve."""

        return self.values.keys()

    def get_for(self, x_value):
        """Returns the y value (codomain) corresponding

        to the given x value (domain).
        """

        return self.values[x_value]

EMPTY_CURVE = Curve({})