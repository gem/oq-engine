"""
Package :mod:`nhe.geo` contains implementations of different geographical
primitives, such as :class:`~nhe.geo.point.Point`, :class:`~nhe.geo.line.Line`
:class:`~nhe.geo.polygon.Polygon` and :class:`~nhe.geo.mesh.Mesh`, as well
as different :mod:`surface <nhe.geo.surface>` implementations and utility
class :class:`~nhe.geo.nodalplane.NodalPlane`.
"""
from nhe.geo.point import Point
from nhe.geo.line import Line
from nhe.geo.polygon import Polygon
from nhe.geo.mesh import Mesh
from nhe.geo.surface import PlanarSurface
from nhe.geo.nodalplane import NodalPlane
