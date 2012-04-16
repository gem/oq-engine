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
Package :mod:`nhlib.geo` contains implementations of different geographical
primitives, such as :class:`~nhlib.geo.point.Point`,
:class:`~nhlib.geo.line.Line` :class:`~nhlib.geo.polygon.Polygon`
and :class:`~nhlib.geo.mesh.Mesh`, as well as different :mod:`surface
<nhlib.geo.surface>` implementations and utility class
:class:`~nhlib.geo.nodalplane.NodalPlane`.
"""
from nhlib.geo.point import Point
from nhlib.geo.line import Line
from nhlib.geo.polygon import Polygon
from nhlib.geo.mesh import Mesh, RectangularMesh
from nhlib.geo.surface import PlanarSurface
from nhlib.geo.surface import SimpleFaultSurface
from nhlib.geo.surface import ComplexFaultSurface
from nhlib.geo.nodalplane import NodalPlane
from nhlib.geo import surface
