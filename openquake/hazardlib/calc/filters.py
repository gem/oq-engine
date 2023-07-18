# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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

import ast
import sys
import operator
from contextlib import contextmanager
import numpy
from scipy.spatial import cKDTree
from scipy.interpolate import interp1d

from openquake.baselib.python3compat import raise_
from openquake.hazardlib import site
from openquake.hazardlib.geo.surface.multi import (
    MultiSurface, _multi_distances, _multi_rx_ry0)
from openquake.hazardlib.geo.utils import (
    KM_TO_DEGREES, angular_distance, get_bounding_box,
    get_longitudinal_extent, BBoxError, spherical_to_cartesian)

U32 = numpy.uint32
MINMAG = 2.5
MAXMAG = 10.2  # to avoid breaking PAC
MAX_DISTANCE = 2000  # km, ultra big distance used if there is no filter
trt_smr = operator.attrgetter('trt_smr')


def magstr(mag):
    """
    :returns: a string representation of the magnitude
    """
    return '%.2f' % numpy.float32(mag)


def _distances_from_dcache(rup, sites, param, dcache):
    """
    Calculates the distances for multi-surfaces using a cache.

    :param rup:
        An instance of :class:`openquake.hazardlib.source.rupture.BaseRupture`
    :param sites:
        A list of sites or a site collection
    :param param:
        The required rupture-distance parameter
    :param dcache:
        A dictionary with the distances. The first key is the
        surface ID and the second one is the type of distance. In a traditional
        calculation dcache is instatianted by in the `get_ctx_iter` method of
        the :class:`openquake.hazardlib.contexts.ContextMaker`
    :returns:
        The computed distances for the rupture in input
    """
    # Update the distance cache
    suids = []  # surface IDs
    for srf in rup.surface.surfaces:
        suids.append(srf.suid)
        if (srf.suid, param) not in dcache:
            # This function returns the distances that will be added to the
            # cache. In case of Rx and Ry0, the information cache will
            # include the ToR of each surface as well as the GC2 t and u
            # coordinates for each section.
            for key, val in _multi_distances(srf, sites, param).items():
                dcache[srf.suid, key] = val
    # Computing distances using the cache
    if param in ['rjb', 'rrup']:
        dcache.hit += 1
        distances = dcache[suids[0], param]
        # This is looping over all the surface IDs composing the rupture
        for suid in suids[1:]:
            distances = numpy.minimum(distances, dcache[suid, param])
    elif param in ['rx', 'ry0']:
        # The computed distances. In this case we are not going to add them to
        # the cache since they cannot be reused
        distances = _multi_rx_ry0(dcache, suids, param)
    else:
        raise ValueError("Unknown distance measure %r" % param)
    return distances


def get_distances(rupture, sites, param, dcache=None):
    """
    :param rupture: a rupture
    :param sites: a mesh of points or a site collection
    :param param: the kind of distance to compute (default rjb)
    :param dcache: None or a dictionary (surfaceID, dist_type) -> distances
    :returns: an array of distances from the given sites
    """
    if (dcache is not None and isinstance(rupture.surface, MultiSurface) and
            hasattr(rupture.surface.surfaces[0], 'suid')):
        return _distances_from_dcache(
            rupture, sites.complete, param, dcache)[sites.sids]
    if not rupture.surface:  # PointRupture
        dist = rupture.hypocenter.distance_to_mesh(sites)
    elif param == 'rrup':
        dist = rupture.surface.get_min_distance(sites)
    elif param == 'rx':
        dist = rupture.surface.get_rx_distance(sites)
    elif param == 'ry0':
        dist = rupture.surface.get_ry0_distance(sites)
    elif param == 'rjb':
        dist = rupture.surface.get_joyner_boore_distance(sites)
    elif param == 'rhypo':
        dist = rupture.hypocenter.distance_to_mesh(sites)
    elif param == 'repi':
        dist = rupture.hypocenter.distance_to_mesh(sites, with_depths=False)
    elif param == 'rcdpp':
        dist = rupture.get_cdppvalue(sites)
    elif param == 'azimuth':
        dist = rupture.surface.get_azimuth(sites)
    elif param == 'azimuth_cp':
        dist = rupture.surface.get_azimuth_of_closest_point(sites)
    elif param == 'closest_point' or param == 'clon' or param == 'clat':
        t = rupture.surface.get_closest_points(sites)  # TODO: measure the
        # perfomance penalty due to the double call to `.get_closest_points`
        # In large calculations; it could very well be insignificant and in
        # that case it is not worth doing anything
        if param == 'closest_point':
            dist = numpy.vstack([t.lons, t.lats, t.depths]).T  # shape (N, 3)
        if param == 'clon':
            dist = numpy.vstack([t.lons])  # shape (N, 3)
        if param == 'clat':
            dist = numpy.vstack([t.lats])  # shape (N, 3)  
    elif param == "rvolc":
        # Volcanic distance not yet supported, defaulting to zero
        dist = numpy.zeros_like(sites.lons)
    else:
        raise ValueError('Unknown distance measure %r' % param)
    dist.flags.writeable = False
    return dist


@contextmanager
def context(src):
    """
    Used to add the source_id to the error message. To be used as

    with context(src):
        operation_with(src)

    Typically the operation is filtering a source, that can fail for
    tricky geometries.
    """
    try:
        yield
    except Exception:
        etype, err, tb = sys.exc_info()
        msg = 'An error occurred with source id=%s. Error: %s'
        msg %= (src.source_id, err)
        raise_(etype, msg, tb)


def getdefault(dic_with_default, key):
    """
    :param dic_with_default: a dictionary with a 'default' key
    :param key: a key that may be present in the dictionary or not
    :returns: the value associated to the key, or to 'default'
    """
    try:
        return dic_with_default[key]
    except KeyError:
        return dic_with_default['default']


def unique_sorted(items):
    """
    Check that the items are unique and sorted
    """
    if len(set(items)) < len(items):
        raise ValueError('Found duplicates in %s' % items)
    elif items != sorted(items):
        raise ValueError('%s is not ordered' % items)
    return items


# used for the maximum distance parameter in the job.ini file
def floatdict(value):
    """
    :param value:
        input string corresponding to a literal Python number or dictionary
    :returns:
        a Python dictionary key -> number

    >>> floatdict("200")
    {'default': 200}

    >>> floatdict("{'active shallow crust': 250., 'default': 200}")
    {'active shallow crust': 250.0, 'default': 200}
    """
    value = ast.literal_eval(value)
    if isinstance(value, (int, float, list)):
        return {'default': value}
    return value


def magdepdist(pairs):
    """
    :param pairs: a list of pairs [(mag, dist), ...]
    :returns: a scipy.interpolate.interp1d function
    """
    mags, dists = zip(*pairs)
    return interp1d(mags, dists, bounds_error=False, fill_value=0.)


def upper_maxdist(idist):
    """
    :returns: the maximum distance in a dictionary trt->dists
    """
    return max(idist[trt][-1][1] for trt in idist)


class IntegrationDistance(dict):
    """
    A dictionary trt -> [(mag, dist), ...]
    """
    @classmethod
    def new(cls, value):
        """
        :param value: string to be converted
        :returns: IntegrationDistance dictionary

        >>> md = IntegrationDistance.new('50')
        >>> md
        {'default': [(2.5, 50), (10.2, 50)]}
        """
        items_by_trt = floatdict(value)
        self = cls()
        for trt, items in items_by_trt.items():
            if isinstance(items, list):
                pairs = unique_sorted([tuple(it) for it in items])
                for mag, dist in pairs:
                    if mag < MINMAG or mag > MAXMAG:
                        raise ValueError('Invalid magnitude %s' % mag)
                self[trt] = pairs
            else:  # assume scalar distance
                assert items >= 0, items
                self[trt] = [(MINMAG, items), (MAXMAG, items)]
        return self

    # tested in case_miriam, case_75 and ebdamage/case_15
    def cut(self, min_mag_by_trt):
        """
        Cut the lower magnitudes. For instance

        >>> maxdist = IntegrationDistance.new('[(4., 50), (8., 200.)]')
        >>> maxdist.cut({'default': 5.})
        >>> maxdist
        {'default': [(5.0, 87.5), (8.0, 200.0)]}
        """
        all_trts = set(self) | set(min_mag_by_trt)
        if 'default' not in self:
            maxval = max(self.values(),
                         key=lambda val: max(dist for mag, dist in val))
            self['default'] = maxval
        if 'default' not in min_mag_by_trt:
            min_mag_by_trt['default'] = min(min_mag_by_trt.values())
        for trt in all_trts:
            min_mag = getdefault(min_mag_by_trt, trt)
            if not min_mag:
                continue
            first = (min_mag, float(self(trt)(min_mag)))
            magdists = [(mag, dist) for (mag, dist) in self[trt]
                        if mag >= min_mag]
            if min_mag < magdists[0][0]:
                self[trt] = [first] + magdists
            else:
                self[trt] = magdists

    def __call__(self, trt):
        return magdepdist(self[trt])

    def __missing__(self, trt):
        assert 'default' in self, 'missing "default" key in maximum_distance'
        return self['default']

    def get_bounding_box(self, lon, lat, trt=None):
        """
        Build a bounding box around the given lon, lat by computing the
        maximum_distance at the given tectonic region type and magnitude.

        :param lon: longitude
        :param lat: latitude
        :param trt: tectonic region type, possibly None
        :returns: min_lon, min_lat, max_lon, max_lat
        """
        if trt is None:  # take the greatest integration distance
            maxdist = max(self.max().values())
        else:  # get the integration distance for the given TRT
            maxdist = self[trt][-1][1]
        a1 = min(maxdist * KM_TO_DEGREES, 90)
        a2 = min(angular_distance(maxdist, lat), 180)
        return lon - a2, lat - a1, lon + a2, lat + a1

    def get_dist_bins(self, trt, nbins=51):
        """
        :returns: an array of distance bins, from 10m to maxdist
        """
        return .01 + numpy.arange(nbins) * self(trt) / (nbins - 1)


def split_source(src):
    """
    :param src: a splittable (or not splittable) source
    :returns: the underlying sources (or the source itself)
    """
    from openquake.hazardlib.source import splittable  # avoid circular import
    if not splittable(src):
        return [src]
    splits = list(src)
    if len(splits) == 1:
        return [src]
    has_samples = hasattr(src, 'samples')
    has_smweight = hasattr(src, 'smweight')
    has_scaling_rate = hasattr(src, 'scaling_rate')
    has_grp_id = hasattr(src, 'grp_id')
    grp_id = getattr(src, 'grp_id', 0)  # 0 in hazardlib
    offset = src.offset
    for i, split in enumerate(splits):
        split.offset = offset
        split.source_id = '%s.%s' % (src.source_id, i)
        split.trt_smr = src.trt_smr
        split.grp_id = grp_id
        split.id = src.id
        if has_samples:
            split.samples = src.samples
        if has_smweight:
            split.smweight = src.smweight
        if has_scaling_rate:
            split.scaling_rate = src.scaling_rate
        if has_grp_id:
            split.grp_id = src.grp_id
        offset += split.num_ruptures
        #split.nsites = src.nsites
    return splits


default = IntegrationDistance({'default': [(MINMAG, 1000), (MAXMAG, 1000)]})


class SourceFilter(object):
    """
    Filter objects have a .filter method yielding filtered sources
    and the IDs of the sites within the given maximum distance.
    Filter the sources by using `self.sitecol.within_bbox` which is
    based on numpy.
    """
    def __init__(self, sitecol, integration_distance=default):
        self.sitecol = sitecol
        self.integration_distance = integration_distance
        self.slc = slice(None)  # TODO: check if we can remove this

    def reduce(self, multiplier=5):
        """
        Reduce the SourceFilter to a subset of sites
        """
        idxs = numpy.arange(0, len(self.sitecol), multiplier)
        sc = object.__new__(site.SiteCollection)
        sc.array = self.sitecol[idxs]
        sc.complete = self.sitecol.complete
        return self.__class__(sc, self.integration_distance)

    def get_enlarged_box(self, src, maxdist=None):
        """
        Get the enlarged bounding box of a source.

        :param src: a source object
        :param maxdist: a scalar maximum distance (or None)
        :returns: a bounding box (min_lon, min_lat, max_lon, max_lat)
        """
        if maxdist is None:
            if hasattr(self.integration_distance, 'y'):  # interp1d
                maxdist = self.integration_distance.y[-1]
            else:
                maxdist = getdefault(self.integration_distance,
                                     src.tectonic_region_type)[-1][1]
        try:
            bbox = get_bounding_box(src, maxdist)
        except Exception as exc:
            raise
            raise exc.__class__('source %s: %s' % (src.source_id, exc))
        return bbox

    def get_rectangle(self, src):
        """
        :param src: a source object
        :returns: ((min_lon, min_lat), width, height), useful for plotting
        """
        min_lon, min_lat, max_lon, max_lat = self.get_enlarged_box(src)
        return (min_lon, min_lat), (max_lon - min_lon) % 360, max_lat - min_lat

    def get_close_sites(self, source):
        """
        Returns the sites within the integration distance from the source,
        or None.
        """
        sids = self.close_sids(source)
        if len(sids):
            return self.sitecol.filtered(sids)

    def split(self, sources):
        """
        :yields: pairs (split, sites)
        """
        for src, _sites in self.filter(sources):
            for s in split_source(src):
                sites = self.get_close_sites(s)
                if sites is not None:
                    yield s, sites

    # used in source and rupture prefiltering: it should not discard too much
    def close_sids(self, src_or_rec, trt=None, maxdist=None):
        """
        :param src_or_rec: a source or a rupture record
        :param trt: passed only if src_or_rec is a rupture record
        :returns:
           the site indices within the maximum_distance of the hypocenter,
           plus the maximum size of the bounding box
        """
        assert self.sitecol is not None
        if not self.integration_distance:  # do not filter
            return self.sitecol.sids
        if trt:  # rupture proxy
            assert hasattr(self.integration_distance, 'x')
            dlon = get_longitudinal_extent(
                src_or_rec['minlon'], src_or_rec['maxlon']) / 2.
            dlat = (src_or_rec['maxlat'] - src_or_rec['minlat']) / 2.
            lon, lat, dep = src_or_rec['hypo']
            dist = self.integration_distance(src_or_rec['mag']) + numpy.sqrt(
                dlon**2 + dlat**2) / KM_TO_DEGREES
            dist += 10  # added 10 km of buffer to guard against numeric errors
            # the test most sensitive to the buffer effect is in oq-risk-tests,
            # case_ucerf/job_eb.ini; without buffer, sites can be discarded
            # even if within the maximum_distance
            return self._close_sids(lon, lat, dep, dist)
        else:  # source
            trt = src_or_rec.tectonic_region_type
            try:
                bbox = self.get_enlarged_box(src_or_rec, maxdist)
            except BBoxError:  # do not filter
                return self.sitecol.sids
            return self.sitecol.within_bbox(bbox)

    def _close_sids(self, lon, lat, dep, dist):
        if not hasattr(self, 'kdt'):
            self.kdt = cKDTree(self.sitecol.xyz)
        xyz = spherical_to_cartesian(lon, lat, dep)
        sids = U32(self.kdt.query_ball_point(xyz, dist, eps=.001))
        sids.sort()
        return sids

    def filter(self, sources):
        """
        :param sources: a sequence of sources
        :yields: pairs (sources, sites)
        """
        if self.sitecol is None:  # nofilter
            for src in sources:
                yield src, None
            return
        for src in sources:
            sids = self.close_sids(src)
            if len(sids):
                yield src, self.sitecol.filtered(sids)

    def __getitem__(self, slc):
        if slc.start is None and slc.stop is None:
            return self
        sitecol = object.__new__(self.sitecol.__class__)
        sitecol.array = self.sitecol[slc]
        sitecol.complete = self.sitecol.complete
        return self.__class__(sitecol, self.integration_distance)


nofilter = SourceFilter(None, {})
