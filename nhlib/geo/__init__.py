# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
from nhe.geo.mesh import Mesh, RectangularMesh
from nhe.geo.surface import PlanarSurface
from nhe.geo.nodalplane import NodalPlane
