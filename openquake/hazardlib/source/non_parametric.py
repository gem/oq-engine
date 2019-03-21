# The Hazard Library
# Copyright (C) 2013-2019 GEM Foundation
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
from openquake.hazardlib.geo.surface.gridded import GriddedSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.source.rupture import \
    NonParametricProbabilisticRupture
from openquake.hazardlib.geo.utils import angular_distance, KM_TO_DEGREES
from openquake.hazardlib.geo.mesh import Mesh, point3d
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.pmf import PMF
from openquake.baselib.slots import with_slots

F32 = numpy.float32


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
    code = b'N'
    _slots_ = BaseSeismicSource._slots_ + ['data']

    MODIFICATIONS = set()

    def __init__(self, source_id, name, tectonic_region_type, data):
        super().__init__(source_id, name, tectonic_region_type)
        self.data = data

    def iter_ruptures(self):
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
            src.src_group_id = self.src_group_id
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

    def __toh5__(self):
        assert self.is_gridded(), '%s is not gridded' % self
        attrs = {'source_id': self.source_id, 'name': self.name,
                 'tectonic_region_type': self.tectonic_region_type}
        dic = {'probs_occur': [], 'magnitude': [], 'rake': [],
               'hypocenter': [], 'points': []}
        for rup, pmf in self.data:
            dic['probs_occur'].append([prob for (prob, _) in pmf.data])
            dic['magnitude'].append(rup.mag)
            dic['rake'].append(rup.rake)
            dic['hypocenter'].append((rup.hypocenter.x, rup.hypocenter.y,
                                      rup.hypocenter.z))
            dic['points'].append(rup.surface.mesh.array)
        dic['hypocenter'] = numpy.array(dic['hypocenter'], point3d)
        return dic, attrs

    def __fromh5__(self, dic, attrs):
        vars(self).update(attrs)
        self.data = []
        for mag, rake, hp, probs, points in zip(
                dic['magnitude'], dic['rake'], dic['hypocenter'],
                dic['probs_occur'], dic['points']):
            mesh = Mesh(points[0], points[1], points[2])
            surface = GriddedSurface(mesh)
            pmf = PMF([(prob, i) for i, prob in enumerate(probs)])
            hypocenter = Point(hp['lon'], hp['lat'], hp['depth'])
            rup = NonParametricProbabilisticRupture(
                mag, rake, self.tectonic_region_type, hypocenter, surface, pmf)
            self.data.append((rup, pmf))

    def __repr__(self):
        return '<%s gridded=%s>' % (self.__class__.__name__, self.is_gridded())

    def geom(self):
        """
        :returns: the geometry as an array of shape (N, 3)
        """
        # the rupture can have a faultSurface which is a 3D array
        # or can be a griddedSurface which is a 2D array or others
        arr = numpy.concatenate([rup.surface.mesh.array.reshape(3, -1)
                                 for rup, pmf in self.data],
                                axis=1)  # shape (3, N)
        return arr.T

    def get_one_rupture(self, rupture_mutex=False):
        """
        Yields one random rupture from a source
        """
        num_ruptures = self.count_ruptures()
        if rupture_mutex:
            weights = numpy.array([rup.weight for rup in self.iter_ruptures()])
        else:
            weights = numpy.ones((num_ruptures))*1./num_ruptures
        idx = numpy.random.choice(range(num_ruptures), p=weights)
        for i, rup in enumerate(self.iter_ruptures()):
            if i == idx:
                rup.serial = self.serial + i
                rup.idx = idx
                return rup
