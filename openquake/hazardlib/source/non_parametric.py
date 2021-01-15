# The Hazard Library
# Copyright (C) 2013-2021 GEM Foundation
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

from openquake.hazardlib.geo.surface.base import _get_finite_mesh

from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.geo.surface.gridded import GriddedSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.source.rupture import \
    NonParametricProbabilisticRupture
from openquake.hazardlib.geo.utils import angular_distance, KM_TO_DEGREES
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.pmf import PMF

F32 = numpy.float32
U32 = numpy.uint32


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
        super().__init__(source_id, name, tectonic_region_type)
        self.data = data
        if weights is not None:
            assert len(weights) == len(data)
            for (rup, pmf), weight in zip(data, weights):
                rup.weight = weight

    def iter_ruptures(self, **kwargs):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :returns:
            Generator of instances of :class:`openquake.hazardlib.source.
            rupture.NonParametricProbabilisticRupture`.
        """
        for rup, pmf in self.data:
            if rup.mag >= self.min_mag:
                yield NonParametricProbabilisticRupture(
                    rup.mag, rup.rake, self.tectonic_region_type,
                    rup.hypocenter, rup.surface, pmf, weight=rup.weight)

    def __iter__(self):
        if len(self.data) == 1:  # there is nothing to split
            yield self
            return
        for i, rup_pmf in enumerate(self.data):
            source_id = '%s:%d' % (self.source_id, i)
            src = self.__class__(source_id, self.name,
                                 self.tectonic_region_type, [rup_pmf])
            src.num_ruptures = 1
            src.et_id = self.et_id
            src.id = self.id
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
        Bounding box containing all surfaces, enlarged by the maximum distance
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
        return '<%s gridded=%s>' % (self.__class__.__name__, self.is_gridded())

    @property
    def polygon(self):
        """
        The convex hull of the underlying mesh of points
        """
        lons, lats = [], []
        for rup, pmf in self.data:

            if isinstance(rup.surface, MultiSurface):
                for sfc in rup.surface.surfaces:
                    lons.extend(sfc.mesh.lons.flat)
                    lats.extend(sfc.mesh.lats.flat)
            else:
                lons.extend(rup.surface.mesh.lons.flat)
                lats.extend(rup.surface.mesh.lats.flat)

        condition = numpy.isfinite(lons).astype(int)
        lons = numpy.extract(condition, lons)
        lats = numpy.extract(condition, lats)

        points = numpy.zeros(len(lons), [('lon', F32), ('lat', F32)])
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

    def get_one_rupture(self, ses_seed, rupture_mutex=False):
        """
        Yields one random rupture from a source
        """
        num_ruptures = self.count_ruptures()
        if rupture_mutex:
            weights = numpy.array([rup.weight for rup in self.iter_ruptures()])
        else:
            weights = numpy.ones((num_ruptures)) / num_ruptures
        idx = numpy.random.choice(range(num_ruptures), p=weights)
        serial = self.serial(ses_seed)
        for i, rup in enumerate(self.iter_ruptures()):
            if i == idx:
                rup.rup_id = serial + i
                rup.idx = idx
                return rup
