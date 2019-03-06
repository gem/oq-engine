# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Package :mod:`openquake.hazardlib.geo` contains implementations of different
geographical primitives, such as :class:`~openquake.hazardlib.geo.point.Point`,
:class:`~openquake.hazardlib.geo.line.Line`
:class:`~openquake.hazardlib.geo.polygon.Polygon` and
:class:`~openquake.hazardlib.geo.mesh.Mesh`, as well as different
:mod:`surface <openquake.hazardlib.geo.surface>` implementations and utility
class :class:`~openquake.hazardlib.geo.nodalplane.NodalPlane`.
"""
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo.surface import PlanarSurface
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo.surface import ComplexFaultSurface
from openquake.hazardlib.geo.surface import MultiSurface
from openquake.hazardlib.geo.surface.gridded import GriddedSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo import surface
