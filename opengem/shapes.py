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

LineString = geometry.LineString
Point = geometry.Point


class Region(object):
    """A container of polygons, used for bounds checking"""
    def __init__(self, polygon):
        self.polygon = polygon
        self.cell_size = 0.1
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
    
    @property
    def grid(self):
        """Returns a proxy interface that maps lat/lon 
        to col/row based on a specific cellsize. Proxy is
        also iterable."""
        if not self.cell_size:
            raise Exception("Can't generate grid without cell_size being set")
        return Grid(self, self.cell_size)
    
    def __iter__(self):    
        if not self.cell_size:
            raise Exception("Can't generate grid without cell_size being set")
        for gridpoint in self.grid:
            yield gridpoint.site


class RegionConstraint(Region):
    """Extends a basic region to work as a constraint on parsers"""
    def match(self, point):
        """Point (specified by Point class or tuple) is contained?"""
        if isinstance(point, Site):
            point = point.point
        if not isinstance(point, geometry.Point): 
            point = geometry.Point(point[0], point[1])
        return self.polygon.intersects(point)


class GridPoint(object):
    """Simple (trivial) point class"""
    def __init__(self, grid, column, row):
        self.column = column
        self.row = row
        self.grid = grid
    
    def __eq__(self, other):
        if isinstance(other, Site):
            other = self.grid.point_at(other)
        return (self.column == other.column and 
            self.row == other.row and 
            self.grid.region.bounds == other.grid.region.bounds and
            self.grid.cell_size == other.grid.cell_size)
    
    @property
    def site(self):
        return self.grid.site_at(self)


    def __repr__(self):
        return "%s:%s:%s" % (self.column, self.row, self.grid.cell_size)


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
        print "Grid with %s rows and %s columns" % (self.rows, self.columns)

    def check_site(self, site):
        """Confirm that the site is contained by the region"""
        # if (self.columns < gridpoint.column or gridpoint.column < 1):
        if not (self.region.polygon.intersects(site.point)):
            raise Exception("Point is not on the Grid")
        # TODO(JMC): Confirm that we always want to test this...
    
    def check_point(self, gridpoint):
        """Confirm that the point is contained by the region"""
        point = Point(self._column_to_longitude(gridpoint.column),
                             self._row_to_latitude(gridpoint.row))
        # print "Checking point at %s" % point
        if not (self.region.polygon.intersects(point)):
            raise Exception("Point is not on the Grid")
    
    def _latitude_to_row(self, latitude):
        """Calculate row from latitude value"""
        latitude_offset = math.fabs(latitude - self.lower_left_corner.latitude)
        print "lat offset = %s" % latitude_offset
        return int((latitude_offset / self.cell_size)) + 1

    def _row_to_latitude(self, row):
        return self.lower_left_corner.latitude + ((row-1) * self.cell_size)

    def _longitude_to_column(self, longitude):
        """Calculate column from longitude value"""
        longitude_offset = longitude - self.lower_left_corner.longitude
        print "long offset = %s" % longitude_offset
        return int((longitude_offset / self.cell_size) + 1)
    
    def _column_to_longitude(self, column):
        return self.lower_left_corner.longitude + ((column-1) * self.cell_size)

    def point_at(self, site):
        """Translates a site into a matrix bidimensional point."""
        self.check_site(site)
        row = self._latitude_to_row(site.latitude)
        column = self._longitude_to_column(site.longitude)
        return GridPoint(self, column, row)
    
    def site_at(self, gridpoint):    
        return Site(self._column_to_longitude(gridpoint.column),
                             self._row_to_latitude(gridpoint.row))
    def __iter__(self):
        for row in range(1, self.rows):
            for col in range(1, self.columns):
                try:
                    point = GridPoint(self, col, row)
                    self.check_point(point)
                    yield point
                except Exception, e:
                    pass


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