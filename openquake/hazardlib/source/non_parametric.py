# The Hazard Library
# Copyright (C) 2013-2025 GEM Foundation
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
from openquake.baselib.general import block_splitter
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.geo.surface.gridded import GriddedSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.source.rupture import \
    NonParametricProbabilisticRupture
from openquake.hazardlib.geo.utils import (angular_distance, KM_TO_DEGREES,
                                           get_spherical_bounding_box)
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.pmf import PMF

F32 = numpy.float32
U32 = numpy.uint32
BLOCKSIZE = 100


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
    code = b'N'
    MODIFICATIONS = set()

    def __init__(self, source_id, name, tectonic_region_type, data,
                 weights=None):
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.data = data
        if weights is not None:
            assert len(weights) == len(data), (len(weights), len(data))
            for (rup, pmf), weight in zip(data, weights):
                rup.weight = weight

    @property
    def rup_weights(self):
        return [rup.weight for rup, pmf in self.data]

    def iter_ruptures(self, **kwargs):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :returns:
            Generator of instances of :class:`openquake.hazardlib.source.
            rupture.NonParametricProbabilisticRupture`.
        """
        step = kwargs.get('step', 1)
        for rup, pmf in self.data[::step**2]:
            yield NonParametricProbabilisticRupture(
                rup.mag, rup.rake, self.tectonic_region_type,
                rup.hypocenter, rup.surface, pmf,
                weight=getattr(rup, 'weight', 0.))

    def __iter__(self):
        if len(self.data) == 1:  # there is nothing to split
            yield self
            return
        for i, block in enumerate(block_splitter(self.data, BLOCKSIZE)):
            source_id = '%s:%d' % (self.source_id, i)
            src = self.__class__(source_id, self.name,
                                 self.tectonic_region_type, block)
            src.num_ruptures = len(block)
            src.trt_smr = self.trt_smr
            yield src

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

    def get_bounding_box(self, maxdist):
        """
        Bounding box containing the surfaces, enlarged by the maximum distance
        """
        surfaces = []
        for rup, _ in self.data:
            if isinstance(rup.surface, MultiSurface):
                surfaces.extend(rup.surface.surfaces)
            else:
                surfaces.append(rup.surface)
        S = len(surfaces)
        lons = numpy.zeros(2*S)
        lats = numpy.zeros(2*S)
        for i, surf in enumerate(surfaces):
            lo1, lo2, la1, la2 = surf.get_bounding_box()
            lons[2*i] = lo1
            lons[2*i + 1] = lo2
            lats[2*i] = la1
            lats[2*i + 1] = la2
        west, east, north, south = get_spherical_bounding_box(lons, lats)
        a1 = maxdist * KM_TO_DEGREES
        a2 = angular_distance(maxdist, north, south)
        return west - a2, south - a1, east + a2, north + a1

    def is_gridded(self):
        """
        :returns: True if containing only GriddedRuptures, False otherwise
        """
        for rup, _ in self.data:
            if not isinstance(rup.surface, GriddedSurface):
                return False
        return True

    def todict(self):
        """
        Convert a GriddedSource into a dictionary of arrays
        """
        assert self.is_gridded(), '%s is not gridded' % self
        n = len(self.data)
        m = sum(len(rup.surface.mesh) for rup, pmf in self.data)
        p = len(self.data[0][1].data)
        dic = {'probs_occur': numpy.zeros((n, p)),
               'magnitude': numpy.zeros(n),
               'rake': numpy.zeros(n),
               'hypocenter': numpy.zeros((n, 3), F32),
               'mesh3d': numpy.zeros((m, 3), F32),
               'slice': numpy.zeros((n, 2), U32)}
        start = 0
        for i, (rup, pmf) in enumerate(self.data):
            dic['probs_occur'][i] = [prob for (prob, _) in pmf.data]
            dic['magnitude'][i] = rup.mag
            dic['rake'][i] = rup.rake
            dic['hypocenter'][i] = (rup.hypocenter.x, rup.hypocenter.y,
                                    rup.hypocenter.z)
            mesh = rup.surface.mesh.array.T  # shape (npoints, 3)
            dic['mesh3d'][start: start + len(mesh)] = mesh
            dic['slice'][i] = start, start + len(mesh)
            start += len(mesh)
        return dic

    def fromdict(self, dic, weights=None):
        """
        Populate a GriddedSource with ruptures
        """
        assert not self.data, '%s is not empty' % self
        i = 0
        for mag, rake, hp, probs, (start, stop) in zip(
                dic['magnitude'], dic['rake'], dic['hypocenter'],
                dic['probs_occur'], dic['slice']):
            mesh = Mesh(dic['mesh3d'][start:stop, 0],
                        dic['mesh3d'][start:stop, 1],
                        dic['mesh3d'][start:stop, 2])
            surface = GriddedSurface(mesh)
            pmf = PMF([(prob, i) for i, prob in enumerate(probs)])
            hypocenter = Point(hp[0], hp[1], hp[2])
            rup = NonParametricProbabilisticRupture(
                mag, rake, self.tectonic_region_type, hypocenter, surface, pmf,
                weight=None if weights is None else weights[i])
            self.data.append((rup, pmf))
            i += 1

    def __repr__(self):
        return '<%s %s gridded=%s>' % (
            self.__class__.__name__, self.source_id, self.is_gridded())

    def mesh_size(self):
        """
        :returns: the number of points in the underlying meshes
        """
        return sum(mesh.lons.size for mesh in self.iter_meshes())

    @property
    def polygon(self):
        """
        The convex hull of a few subsurfaces
        """
        lons, lats = [], []
        for mesh in self.iter_meshes():
            mesh = mesh.reduce(10)
            lons.extend(mesh.lons.flat)
            lats.extend(mesh.lats.flat)

        condition = numpy.isfinite(lons).astype(int)
        lons = numpy.extract(condition, lons)
        lats = numpy.extract(condition, lats)

        points = numpy.zeros(len(lons), [('lon', float), ('lat', float)])
        points['lon'] = numpy.round(lons, 5)
        points['lat'] = numpy.round(lats, 5)
        points = numpy.unique(points)
        mesh = Mesh(points['lon'], points['lat'])
        return mesh.get_convex_hull()

    def wkt(self):
        """
        :returns: the geometry as a WKT string
        """
        return self.polygon.wkt
