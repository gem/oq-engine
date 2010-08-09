# vim: tabstop=4 shiftwidth=4 softtabstop=4

from shapely import geometry
from shapely import wkt


LineString = geometry.LineString

class RegionConstraint(object):
    def __init__(self, polygon):
        self.polygon = polygon

    @classmethod
    def from_coordinates(cls, coordinates):
        polygon = geometry.Polygon(coordinates)
        return cls(polygon)
    
    @classmethod
    def from_simple(cls, top_left, bottom_right):
        points = [top_left,
                  (top_left[0], bottom_right[1]),
                  bottom_right,
                  (bottom_right[0], top_left[1])]
        return cls.from_coordinates(points)
    
    @classmethod
    def from_file(cls, path):
        f = open(path)
        polygon = wkt.loads(f.read())
        return cls(polygon=polygon)

    def match(self, point):
        if type(point) is type(tuple()):
            point = geometry.Point(*point)
        return self.polygon.contains(point)
