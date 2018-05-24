# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2018 GEM Foundation
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

import sys
import operator
import collections
from contextlib import contextmanager
import numpy
try:
    import rtree
except ImportError:
    rtree = None
from scipy.interpolate import interp1d
from openquake.baselib import hdf5, config
from openquake.baselib.parallel import Starmap
from openquake.baselib.general import gettemp, groupby
from openquake.baselib.python3compat import raise_
from openquake.hazardlib.geo.utils import (
    KM_TO_DEGREES, angular_distance, within, fix_lon, get_bounding_box)

MAX_DISTANCE = 2000  # km, ultra big distance used if there is no filter
src_group_id = operator.attrgetter('src_group_id')


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


class Piecewise(object):
    """
    Given two arrays x and y of non-decreasing values, build a piecewise
    function associating to each x the corresponding y. If x is smaller
    then the minimum x, the minimum y is returned; if x is larger than the
    maximum x, the maximum y is returned.
    """
    def __init__(self, x, y):
        self.y = numpy.array(y)
        # interpolating from x values to indices in the range [0: len(x)]
        self.piecewise = interp1d(x, range(len(x)), bounds_error=False,
                                  fill_value=(0, len(x) - 1))

    def __call__(self, x):
        idx = numpy.int64(numpy.ceil(self.piecewise(x)))
        return self.y[idx]


class IntegrationDistance(collections.Mapping):
    """
    Pickleable object wrapping a dictionary of integration distances per
    tectonic region type. The integration distances can be scalars or
    list of pairs (magnitude, distance). Here is an example using 'default'
    as tectonic region type, so that the same values will be used for all
    tectonic region types:

    >>> maxdist = IntegrationDistance({'default': [
    ...          (3, 30), (4, 40), (5, 100), (6, 200), (7, 300), (8, 400)]})
    >>> maxdist('Some TRT', mag=2.5)
    30
    >>> maxdist('Some TRT', mag=3)
    30
    >>> maxdist('Some TRT', mag=3.1)
    40
    >>> maxdist('Some TRT', mag=8)
    400
    >>> maxdist('Some TRT', mag=8.5)  # 2000 km are used above the maximum
    2000

    It has also a method `.get_closest(sites, rupture)` returning the closest
    sites to the rupture and their distances. The integration distance can be
    missing if the sites have been already filtered (empty dictionary): in
    that case the method returns all the sites and all the distances.
    """
    def __init__(self, dic):
        self.dic = dic or {}  # TRT -> float or list of pairs
        self.magdist = {}  # TRT -> (magnitudes, distances)
        for trt, value in self.dic.items():
            if isinstance(value, list):  # assume a list of pairs (mag, dist)
                self.magdist[trt] = value
            else:
                self.dic[trt] = float(value)

    def __call__(self, trt, mag=None):
        value = getdefault(self.dic, trt)
        if isinstance(value, float):  # scalar maximum distance
            return value
        elif mag is None:  # get the maximum distance
            return MAX_DISTANCE
        elif not hasattr(self, 'piecewise'):
            self.piecewise = {}  # function cache
        try:
            md = self.piecewise[trt]  # retrieve from the cache
        except KeyError:  # fill the cache
            mags, dists = zip(*getdefault(self.magdist, trt))
            if mags[-1] < 11:  # use 2000 km for mag > mags[-1]
                mags = numpy.concatenate([mags, [11]])
                dists = numpy.concatenate([dists, [MAX_DISTANCE]])
            md = self.piecewise[trt] = Piecewise(mags, dists)
        return md(mag)

    def get_bounding_box(self, lon, lat, trt=None, mag=None):
        """
        Build a bounding box around the given lon, lat by computing the
        maximum_distance at the given tectonic region type and magnitude.

        :param lon: longitude
        :param lat: latitude
        :param trt: tectonic region type, possibly None
        :param mag: magnitude, possibly None
        :returns: min_lon, min_lat, max_lon, max_lat
        """
        if trt is None:  # take the greatest integration distance
            maxdist = max(self(trt, mag) for trt in self.dic)
        else:  # get the integration distance for the given TRT
            maxdist = self(trt, mag)
        a1 = min(maxdist * KM_TO_DEGREES, 90)
        a2 = min(angular_distance(maxdist, lat), 180)
        return lon - a2, lat - a1, lon + a2, lat + a1

    def get_affected_box(self, src):
        """
        Get the enlarged bounding box of a source.

        :param src: a source object
        :returns: a bounding box (min_lon, min_lat, max_lon, max_lat)
        """
        mag = src.get_min_max_mag()[1]
        maxdist = self(src.tectonic_region_type, mag)
        bbox = get_bounding_box(src, maxdist)
        return (fix_lon(bbox[0]), bbox[1], fix_lon(bbox[2]), bbox[3])

    def __getstate__(self):
        # otherwise is not pickleable due to .piecewise
        return dict(dic=self.dic, magdist=self.magdist)

    def __getitem__(self, trt):
        return self(trt)

    def __iter__(self):
        return iter(self.dic)

    def __len__(self):
        return len(self.dic)

    def __repr__(self):
        return repr(self.dic)


def prefilter(srcs, srcfilter, monitor):
    """
    :returns: a dict src_group_id -> sources
    """
    return groupby(srcfilter.filter(srcs), src_group_id)


class SourceFilter(object):
    """
    Filter objects have a .filter method yielding filtered sources,
    i.e. sources with an attribute .indices, containg the IDs of the sites
    within the given maximum distance. There is also a .pfilter method
    that filters the sources in parallel and returns a dictionary
    src_group_id -> filtered sources.
    Filter the sources by using `self.sitecol.within_bbox` which is
    based on numpy.
    """
    def __init__(self, sitecol, integration_distance, hdf5path=None):
        if sitecol is not None and len(sitecol) < len(sitecol.complete):
            raise ValueError('%s is not complete!' % sitecol)
        self.hdf5path = hdf5path
        if hdf5path and (
                config.distribution.oq_distribute in ('no', 'processpool') or
                config.directory.shared_dir):  # store the sitecol
            with hdf5.File(hdf5path, 'w') as h5:
                h5['sitecol'] = sitecol
        else:  # keep the sitecol in memory
            self.__dict__['sitecol'] = sitecol
        self.integration_distance = (
            IntegrationDistance(integration_distance)
            if isinstance(integration_distance, dict)
            else integration_distance)
        self.distribute = None

    @property
    def sitecol(self):
        """
        Read the site collection from .hdf5path and cache it
        """
        if 'sitecol' in vars(self):
            return self.__dict__['sitecol']
        with hdf5.File(self.hdf5path, 'r') as h5:
            self.__dict__['sitecol'] = sc = h5['sitecol']
        return sc

    def get_rectangle(self, src):
        """
        :param src: a source object
        :returns: ((min_lon, min_lat), width, height), useful for plotting
        """
        min_lon, min_lat, max_lon, max_lat = (
            self.integration_distance.get_affected_box(src))
        return (min_lon, min_lat), (max_lon - min_lon) % 360, max_lat - min_lat

    def get_close_sites(self, source):
        """
        Returns the sites within the integration distance from the source,
        or None.
        """
        source_sites = list(self([source]))
        if source_sites:
            return source_sites[0][1]

    def __call__(self, sources):
        """
        :yields: pairs (src, sites)
        """
        if not self.integration_distance:  # do not filter
            for src in sources:
                yield src, self.sitecol
            return
        for src in self.filter(sources):
            yield src, self.sitecol.filtered(src.indices)

    # used in the disaggregation calculator
    def get_bounding_boxes(self, trt=None, mag=None):
        """
        :param trt: a tectonic region type (used for the integration distance)
        :param mag: a magnitude (used for the integration distance)
        :returns: a list of bounding boxes, one per site
        """
        bbs = []
        for site in self.sitecol:
            bb = self.integration_distance.get_bounding_box(
                site.location.longitude, site.location.latitude, trt, mag)
            bbs.append(bb)
        return bbs

    def filter(self, sources):
        """
        :param sources: a sequence of sources
        :yields: sources with .indices
        """
        for src in sources:
            if hasattr(src, 'indices'):   # already filtered
                yield src
                continue
            box = self.integration_distance.get_affected_box(src)
            indices = self.sitecol.within_bbox(box)
            if len(indices):
                src.indices = indices
                yield src

    def pfilter(self, sources, monitor):
        """
        Filter the sources in parallel by using Starmap.apply

        :param sources: a sequence of sources
        :param monitor: a Monitor instance
        :returns: a dictionary src_group_id -> sources
        """
        sources_by_grp = Starmap.apply(
            prefilter, (sources, self, monitor), distribute=self.distribute,
            name=self.__class__.__name__).reduce()
        Starmap.shutdown()  # close the processpool
        Starmap.init()  # reopen it when necessary
        # avoid task ordering issues
        for sources in sources_by_grp.values():
            sources.sort(key=operator.attrgetter('source_id'))
        return sources_by_grp


class RtreeFilter(SourceFilter):
    """
    The RtreeFilter uses the rtree library. The index is generated at
    instantiation time and stored in a temporary file. The filter should be
    instantiated only once per calculation, after the site collection is
    known. It should be used as follows::

      rfilter = RtreeFilter(sitecol, integration_distance)
      for src, sites in rfilter(sources):
         do_something(...)

    As a side effect, sets the `.indices` attribute of the source, i.e. the
    number of sites within the integration distance. Notice that
    libspatialindex indices cannot be properly pickled
    (https://github.com/Toblerity/rtree/issues/65) this is why they must
    be saved on the file system where they can be read from the workers.

    NB: an RtreeFilter has an .indexpath attribute, but not a .sitecol
    attribute nor an .index attribute, so it can be pickled and transferred
    easily.

    :param sitecol:
        :class:`openquake.hazardlib.site.SiteCollection` instance
    :param integration_distance:
        Integration distance dictionary (TRT -> distance in km)
    """
    def __init__(self, sitecol, integration_distance, hdf5path=None):
        if rtree is None:
            raise ImportError('rtree')
        super().__init__(sitecol, integration_distance, hdf5path)
        self.distribute = 'processpool'
        self.indexpath = gettemp()
        lonlats = zip(sitecol.lons, sitecol.lats)
        index = rtree.index.Index(self.indexpath)
        for i, (lon, lat) in enumerate(lonlats):
            index.insert(i, (lon, lat, lon, lat))
        index.close()

    def filter(self, sources):
        """
        :param sources: a sequence of sources
        :yields: rtree-filtered sources
        """
        index = rtree.index.Index(self.indexpath)
        try:
            for src in sources:
                box = self.integration_distance.get_affected_box(src)
                indices = within(box, index)
                if len(indices):
                    src.indices = indices
                    yield src
        finally:
            index.close()


source_site_noop_filter = SourceFilter(None, {})
