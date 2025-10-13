# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
from openquake.hazardlib.geo.point import Point  # noqa
from openquake.hazardlib.geo.line import Line  # noqa
from openquake.hazardlib.geo.multiline import MultiLine  # noqa
from openquake.hazardlib.geo.polygon import Polygon  # noqa
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh  # noqa
from openquake.hazardlib.geo.surface import PlanarSurface  # noqa
from openquake.hazardlib.geo.surface import SimpleFaultSurface  # noqa
from openquake.hazardlib.geo.surface import ComplexFaultSurface  # noqa
from openquake.hazardlib.geo.surface import MultiSurface  # noqa
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface  # noqa
from openquake.hazardlib.geo.surface.gridded import GriddedSurface  # noqa
from openquake.hazardlib.geo.nodalplane import NodalPlane  # noqa
from openquake.hazardlib.geo import surface  # noqa
