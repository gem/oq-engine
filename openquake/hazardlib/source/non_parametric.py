# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.source.non_parametric` defines
:class:`NonParametricSeismicSource`
"""
import numpy
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.mesh import RectangularMesh
from openquake.hazardlib.source.rupture import \
    NonParametricProbabilisticRupture
from openquake.baselib.slots import with_slots


@with_slots
class NonParametricSeismicSource(BaseSeismicSource):
    """
    Non Parametric Seismic Source explicitly defines earthquake ruptures in the
    constructor. That is earthquake ruptures are not generated algorithmically
    from a set of source parameters.

    Ruptures' rectonic region types are overwritten by source tectonic region
    type.

    :param data:
        List of tuples. Each tuple must contain two items. The first item must
        be an instance of :class:`openquake.hazardlib.source.rupture.Rupture`.
        The second item must be an instance of
        :class:`openquake.hazardlib.pmf.PMF` describing the probability of the
        rupture to occur N times (the PMF must be defined from a minimum number
        of occurrences equal to 0)
    """
    _slots_ = BaseSeismicSource._slots_ + ['data']

    MODIFICATIONS = set()

    def __init__(self, source_id, name, tectonic_region_type, data):
        super(NonParametricSeismicSource, self). \
            __init__(source_id, name, tectonic_region_type)
        self.data = data

    def iter_ruptures(self):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :returns:
            Generator of instances of :class:
            `~openquake.hazardlib.source.rupture.NonParametricProbabilisticRupture`.
        """
        for rup, pmf in self.data:
            yield NonParametricProbabilisticRupture(
                rup.mag, rup.rake, self.tectonic_region_type, rup.hypocenter,
                rup.surface, rup.source_typology, pmf)

    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`.
        """
        return len(self.data)

    def get_min_max_mag(self):
        """
        Return the minimum and maximum magnitudes of the ruptures generated
        by the source
        """
        min_mag = min(rup.mag for rup, pmf in self.data)
        max_mag = max(rup.mag for rup, pmf in self.data)
        return min_mag, max_mag

    def get_rupture_enclosing_polygon(self, dilation=0):
        """
        Create instance of
        :class:`openquake.hazardlib.geo.surface.multi.MultiSurface` from all
        ruptures' surfaces and compute its bounding box. Calculate convex hull
        of bounding box, and return it dilated by ``dilation``.

        :param dilation:
            A buffer distance in km to extend the polygon borders to.
        :returns:
            Instance of :class:`openquake.hazardlib.geo.polygon.Polygon`.
        """
        surfaces = []
        for rup, _ in self.data:
            if isinstance(rup.surface, MultiSurface):
                for s in rup.surface.surfaces:
                    surfaces.append(s)
            else:
                surfaces.append(rup.surface)
        multi_surf = MultiSurface(surfaces)

        west, east, north, south = multi_surf.get_bounding_box()
        mesh = RectangularMesh(numpy.array([[west, east], [west, east]]),
                               numpy.array([[north, north], [south, south]]),
                               None)
        poly = mesh.get_convex_hull()

        return poly if dilation == 0 else poly.dilate(dilation)
