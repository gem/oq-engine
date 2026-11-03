# The Hazard Library
# Copyright (C) 2013-2026 GEM Foundation
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
from openquake.baselib.general import block_splitter, WeightedSequence
from openquake.hazardlib.codes import NON_PARAMETRIC
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.geo.surface.gridded import GriddedSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.source.rupture import (
    BaseRupture, NonParametricProbabilisticRupture)
from openquake.hazardlib.geo.utils import (angular_distance, KM_TO_DEGREES,
                                           get_spherical_bounding_box)
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.pmf import PMF

F32 = numpy.float32
U32 = numpy.uint32
BLOCKSIZE = 100
RUP_ATTRS = {'tectonic_region_type', 'rake', 'mag', 'hypocenter', 'surface',
             'rupture_slip_direction', 'ruid', 'probs_occur', 'weight'}
RUP_TYPES = (BaseRupture, NonParametricProbabilisticRupture)
POINT_ATTRS = {'longitude', 'latitude', 'depth'}


# True if the rupture can be stored in arrays and rebuilt exactly,
# i.e. it is a plain BaseRupture or NonParametricProbabilisticRupture
# with a GriddedSurface and the probabilities of 0, 1, ... occurrences
def _is_simple(rup, pmf, first_rup, first_pmf):
    surf = rup.surface
    if (type(rup) not in RUP_TYPES or type(rup) is not type(first_rup) or
            type(surf) is not GriddedSurface or type(pmf) is not PMF or
            type(surf.mesh) is not Mesh or type(rup.hypocenter) is not Point):
        return False
    if (not set(vars(rup)) <= RUP_ATTRS or
            (surf.idx, surf.strike, surf.dip) != (None, None, None) or
            rup.rupture_slip_direction is not None or rup.ruid is not None or
            rup.tectonic_region_type != first_rup.tectonic_region_type or
            hasattr(rup, 'weight') != hasattr(first_rup, 'weight')):
        return False
    arr = surf.mesh.array
    if (not set(vars(surf.mesh)) <= {'array', 'xyz'} or
            set(vars(rup.hypocenter)) != POINT_ATTRS or
            arr.ndim != 2 or len(arr) != 3 or
            arr.dtype != first_rup.surface.mesh.array.dtype):
        return False
    probs = [prob for prob, _ in pmf.data]
    if ([occ for _, occ in pmf.data] != list(range(len(probs))) or
            len(probs) != len(first_pmf.data)):
        return False
    if type(rup) is BaseRupture:
        return not hasattr(rup, 'probs_occur')
    return (rup.probs_occur.dtype == numpy.float64 and
            numpy.array_equal(rup.probs_occur, probs))


# Store the (rup, pmf) pairs in a few arrays, or return None if the
# ruptures are not simple; the cached cartesian coordinates of the meshes
# are not stored, since they can be recomputed exactly
def _to_arrays(data):
    if not data:
        return None
    rup0, pmf0 = data[0]
    if not all(_is_simple(rup, pmf, rup0, pmf0) for rup, pmf in data):
        return None
    meshes = [rup.surface.mesh.array for rup, _ in data]
    sizes = [mesh.shape[1] for mesh in meshes]
    arrays = {
        'mag': numpy.array([rup.mag for rup, _ in data]),
        'rake': numpy.array([rup.rake for rup, _ in data]),
        'hypo': numpy.array([(rup.hypocenter.longitude,
                              rup.hypocenter.latitude,
                              rup.hypocenter.depth) for rup, _ in data]),
        'probs': numpy.array([[prob for prob, _ in pmf.data]
                              for _, pmf in data]),
        'mesh': numpy.concatenate(meshes, axis=1),
        'offset': numpy.cumsum([0] + sizes),
        'trt': rup0.tectonic_region_type, 'rup_type': type(rup0),
        'mag_type': type(rup0.mag), 'rake_type': type(rup0.rake)}
    if hasattr(rup0, 'weight'):
        arrays['weight'] = [rup.weight for rup, _ in data]
    if isinstance(data, WeightedSequence):
        arrays['seq_weight'] = data.weight
    elif type(data) is not list:
        return None
    return arrays


# Rebuild the (rup, pmf) pairs from the arrays returned by _to_arrays
def _from_arrays(arrays):
    out = []
    mag_type, rake_type = arrays['mag_type'], arrays['rake_type']
    offset = arrays['offset']
    weights = arrays.get('weight')
    for i, (mag, rake, hypo, probs) in enumerate(zip(
            arrays['mag'], arrays['rake'], arrays['hypo'], arrays['probs'])):
        mesh = Mesh.__new__(Mesh)
        mesh.array = arrays['mesh'][:, offset[i]:offset[i + 1]].copy()
        pmf = PMF([(prob, occ) for occ, prob in enumerate(probs.tolist())])
        args = (mag_type(mag), rake_type(rake), arrays['trt'], Point(*hypo),
                GriddedSurface(mesh))
        if arrays['rup_type'] is BaseRupture:
            rup = BaseRupture(*args)
        else:
            rup = NonParametricProbabilisticRupture(*args, pmf)
        if weights is not None:
            rup.weight = weights[i]
        out.append((rup, pmf))
    if 'seq_weight' in arrays:
        seq = WeightedSequence()
        seq._seq = out
        seq.weight = arrays['seq_weight']
        return seq
    return out


# Arrays for the ruptures from start to stop, in a WeightedSequence of
# weight stop - start, as the blocks returned by block_splitter
def _slice_arrays(arrays, start, stop):
    offset = arrays['offset']
    out = {k: v for k, v in arrays.items() if k != 'seq_weight'}
    for key in ('mag', 'rake', 'hypo', 'probs'):
        out[key] = arrays[key][start:stop]
    out['mesh'] = arrays['mesh'][:, offset[start]:offset[stop]]
    out['offset'] = offset[start:stop + 1] - offset[start]
    if 'weight' in arrays:
        out['weight'] = arrays['weight'][start:stop]
    out['seq_weight'] = stop - start
    return out


# Longitudes and latitudes of the bounding boxes of the surfaces,
# in the same order as NonParametricSeismicSource.get_bounding_box
def _bounds(arrays):
    offset, mesh = arrays['offset'], arrays['mesh']
    n = len(offset) - 1
    lons, lats = numpy.zeros(2 * n), numpy.zeros(2 * n)
    for i in range(n):
        start, stop = offset[i], offset[i + 1]
        (lons[2 * i], lons[2 * i + 1], lats[2 * i], lats[2 * i + 1]) = \
            get_spherical_bounding_box(mesh[0, start:stop],
                                       mesh[1, start:stop])
    return lons, lats


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
    code = NON_PARAMETRIC
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
    def data(self):
        """
        The list of pairs (rup, pmf); after unpickling it is rebuilt from
        compact arrays at each access, so that the ruptures are kept in
        memory only while they are used
        """
        if '_arrays' in self.__dict__:
            return _from_arrays(self._arrays)
        return self._data

    @data.setter
    def data(self, data):
        self.__dict__.pop('_arrays', None)
        self._data = data

    def __getstate__(self):
        # pickle the ruptures as a few arrays, which are much smaller
        # in memory and faster to unpickle than the rupture objects
        state = self.__dict__.copy()
        if '_data' in state:
            arrays = _to_arrays(state['_data'])
            if arrays is not None:
                del state['_data']
                state['_arrays'] = arrays
        return state

    def __setstate__(self, state):
        if 'data' in state:  # pickled before data became a property
            state['_data'] = state.pop('data')
        self.__dict__.update(state)

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
        if self.count_ruptures() == 1:  # there is nothing to split
            yield self
            return
        if '_arrays' in self.__dict__:  # split without rebuilding
            n = self.count_ruptures()
            for i, start in enumerate(range(0, n, BLOCKSIZE)):
                src = self.__class__.__new__(self.__class__)
                src.source_id = '%s:%d' % (self.source_id, i)
                src.name = self.name
                src.tectonic_region_type = self.tectonic_region_type
                src._arrays = _slice_arrays(
                    self._arrays, start, min(start + BLOCKSIZE, n))
                src._num_ruptures = src.count_ruptures()
                yield src
            return
        for i, block in enumerate(block_splitter(self.data, BLOCKSIZE)):
            source_id = '%s:%d' % (self.source_id, i)
            src = self.__class__(source_id, self.name,
                                 self.tectonic_region_type, block)
            src._num_ruptures = len(block)
            yield src

    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`.
        """
        if '_arrays' in self.__dict__:
            return len(self._arrays['mag'])
        return len(self.data)

    def get_min_max_mag(self):
        """
        Return the minimum and maximum magnitudes of the ruptures generated
        by the source
        """
        if '_arrays' in self.__dict__:
            mags = self._arrays['mag']
            return self._arrays['mag_type'](mags.min()), \
                self._arrays['mag_type'](mags.max())
        min_mag = min(rup.mag for rup, pmf in self.data)
        max_mag = max(rup.mag for rup, pmf in self.data)
        return min_mag, max_mag

    def get_bounding_box(self, maxdist):
        """
        Bounding box containing the surfaces, enlarged by the maximum distance
        """
        if '_arrays' in self.__dict__:
            lons, lats = _bounds(self._arrays)
            west, east, north, south = get_spherical_bounding_box(lons, lats)
            a1 = maxdist * KM_TO_DEGREES
            a2 = angular_distance(maxdist, north, south)
            return west - a2, south - a1, east + a2, north + a1
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

    def get_mags(self):
        """
        :returns: the magnitudes of the ruptures contained in the source
        """
        if '_arrays' in self.__dict__:
            mag_type = self._arrays['mag_type']
            return sorted(set(map(mag_type, self._arrays['mag'])))
        return super().get_mags()

    def is_gridded(self):
        """
        :returns: True if containing only GriddedRuptures, False otherwise
        """
        if '_arrays' in self.__dict__:  # only gridded ruptures are stored
            return True
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
