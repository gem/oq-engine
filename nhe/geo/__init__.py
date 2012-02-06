# encoding: utf-8
"""
Module providing geographical classes and functions.
"""
import pyproj

#: Geod object to be used whenever we need to deal with
#: spherical coordinates.
GEOD = pyproj.Geod(ellps='sphere')


from nhe.geo.point import Point
from nhe.geo.line import Line
from nhe.geo.polygon import Polygon
