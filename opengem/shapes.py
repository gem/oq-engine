# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Collection of base classes for processing 
spatially-related data."""

import math

import geohash
from shapely import geometry
from shapely import wkt

from opengem import flags
FLAGS = flags.FLAGS

flags.DEFINE_integer('distance_precision', 12, 
    "Points within this geohash precision will be considered the same point")

Point = geometry.Point


class Region(object):
    """A container of polygons, used for bounds checking"""
    def __init__(self, polygon):
        self.polygon = polygon
        # TODO(JMC): Make this a multipolygon instead?

    @classmethod
    def from_coordinates(cls, coordinates):
        """Build a region from a set of coordinates"""
        polygon = geometry.Polygon(coordinates)
        return cls(polygon)
    
    @classmethod
    def from_simple(cls, top_left, bottom_right):
        """Build a region from two corners (top left, bottom right)"""
        points = [top_left,
                  (top_left[0], bottom_right[1]),
                  bottom_right,
                  (bottom_right[0], top_left[1])]
        return cls.from_coordinates(points)
    
    @classmethod
    def from_file(cls, path):
        """Load a region from a wkt file with a single polygon"""
        with open(path) as wkt_file:
            polygon = wkt.loads(wkt_file.read())
            return cls(polygon=polygon)
    
    @property
    def bounds(self):
        """Returns a bounding box containing the whole region"""
        return self.polygon.bounds
    
    @property
    def lower_left_corner(self):
        """Lower left corner of the containing bounding box"""
        (minx, miny, _maxx, _maxy) = self.bounds
        return Site(miny, minx)
        
    @property
    def lower_right_corner(self):
        """Lower right corner of the containing bounding box"""
        (_minx, miny, maxx, _maxy) = self.bounds
        return Site(miny, maxx)
            
    @property
    def upper_left_corner(self):
        """Upper left corner of the containing bounding box"""
        (minx, _miny, _maxx, maxy) = self.bounds
        return Site(maxy, minx)
        
    @property
    def upper_right_corner(self):
        """Upper right corner of the containing bounding box"""
        (_minx, _miny, maxx, maxy) = self.bounds
        return Site(maxy, maxx)
    
    def grid(self, cell_size):
        """Returns a proxy interface that maps lat/lon 
        to col/row based on a specific cellsize. Proxy is
        also iterable."""
        return Grid(self, cell_size)


class RegionConstraint(Region):
    """Extends a basic region to work as a constraint on parsers"""
    def match(self, point):
        """Point (specified by Point class or tuple) is contained?"""
        if not isinstance(point, geometry.Point): 
            point = geometry.Point(point[0], point[1])
        return self.polygon.contains(point)


class GridPoint(object):
    """Simple (trivial) point class"""
    def __init__(self, column, row):
        self.column = column
        self.row = row


class Grid(object):
    """Grid is a proxy interface to Region, which translates
    lat/lon to col/row"""
    
    def __init__(self, region, cell_size):
        self.region = region
        self.cell_size = cell_size
        self.lower_left_corner = self.region.lower_left_corner
        self.columns = self._longitude_to_column(
                    self.region.upper_right_corner.longitude)
        self.rows = self._latitude_to_row(
                    self.region.upper_right_corner.latitude)

    def check_site(self, site):
        """Confirm that the site is contained by the region"""
        # if (self.columns < gridpoint.column or gridpoint.column < 1):
        if not (self.region.polygon.contains(site.point)):
            raise Exception("Point is not on the Grid")
        # TODO(JMC): Confirm that we always want to test this...
    
    def _latitude_to_row(self, latitude):
        """Calculate row from latitude value"""
        latitude_offset = math.fabs(latitude - self.lower_left_corner.latitude)
        print "lat offset = %s" % latitude_offset
        return int(self.rows - (latitude_offset / self.cell_size)) + 1

    def _longitude_to_column(self, longitude):
        """Calculate column from longitude value"""
        longitude_offset = longitude - self.lower_left_corner.longitude
        print "long offset = %s" % longitude_offset
        return int((longitude_offset / self.cell_size) + 1)

    def point_at(self, site):
        """Translates a site into a matrix bidimensional point."""
        self.check_site(site)
        row = self._latitude_to_row(site.latitude)
        column = self._longitude_to_column(site.longitude)
        return GridPoint(column, row)
    
    def __iter__(self):
        for row in range(1, self.rows):
            for col in range(1, self.columns):
                yield GridPoint(col, row)


class Site(object):
    """Site is a dictionary-keyable point"""
    
    def __init__(self, longitude, latitude):
        self.point = geometry.Point(longitude, latitude)
    
    @property
    def longitude(self):
        "Point x value is longitude"
        return self.point.x
        
    @property
    def latitude(self):
        "Point y value is latitude"
        return self.point.y

    def __eq__(self, other):
        return self.hash() == other.hash()
    
    def hash(self):
        """A geohash-encoded string for dict keys"""
        return geohash.encode(self.point.y, self.point.x, 
            precision=FLAGS.distance_precision)
    
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
    used in the risk domain."""

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
        to the given x value (domain)."""
        return self.values[x_value]

EMPTY_CURVE = Curve({})