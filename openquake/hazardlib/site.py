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

"""
Module :mod:`openquake.hazardlib.site` defines :class:`Site`.
"""
import numpy
from scipy.spatial import distance
from shapely import geometry
from openquake.baselib.general import not_equal, get_duplicates
from openquake.hazardlib.geo.utils import (
    fix_lon, cross_idl, _GeographicObjects, geohash, spherical_to_cartesian)
from openquake.hazardlib.geo.mesh import Mesh

U32LIMIT = 2 ** 32
ampcode_dt = (numpy.string_, 4)
param = dict(
    vs30measured='reference_vs30_type',
    vs30='reference_vs30_value',
    z1pt0='reference_depth_to_1pt0km_per_sec',
    z2pt5='reference_depth_to_2pt5km_per_sec',
    backarc='reference_backarc')


# TODO: equivalents of calculate_z1pt0 and calculate_z2pt5
# are inside some GSIM implementations, we should avoid duplication
def calculate_z1pt0(vs30):
    '''
    Reads an array of vs30 values (in m/s) and
    returns the depth to the 1.0 km/s velocity horizon (in m)
    Ref: Chiou & Youngs (2014) California model
    :param vs30: the shear wave velocity (in m/s) at a depth of 30m
    '''
    c1 = 571 ** 4.
    c2 = 1360.0 ** 4.
    return numpy.exp((-7.15 / 4.0) * numpy.log((vs30 ** 4. + c1) / (c2 + c1)))


def calculate_z2pt5(vs30):
    '''
    Reads an array of vs30 values (in m/s) and
    returns the depth to the 2.5 km/s velocity horizon (in km)
    Ref: Campbell, K.W. & Bozorgnia, Y., 2014.
    'NGA-West2 ground motion model for the average horizontal components of
    PGA, PGV, and 5pct damped linear acceleration response spectra.'
    Earthquake Spectra, 30(3), pp.1087–1114.

    :param vs30: the shear wave velocity (in m/s) at a depth of 30 m
    '''
    c1 = 7.089
    c2 = -1.144
    return numpy.exp(c1 + numpy.log(vs30) * c2)


class Site(object):
    """
    Site object represents a geographical location defined by its position
    as well as its soil characteristics.

    :param location:
        Instance of :class:`~openquake.hazardlib.geo.point.Point` representing
        where the site is located.
    :param vs30:
        Average shear wave velocity in the top 30 m, in m/s.
    :param z1pt0:
        Vertical distance from earth surface to the layer where seismic waves
        start to propagate with a speed above 1.0 km/sec, in meters.
    :param z2pt5:
        Vertical distance from earth surface to the layer where seismic waves
        start to propagate with a speed above 2.5 km/sec, in km.

    :raises ValueError:
        If any of ``vs30``, ``z1pt0`` or ``z2pt5`` is zero or negative.

    .. note::

        :class:`Sites <Site>` are pickleable
    """

    def __init__(self, location, vs30=numpy.nan,
                 z1pt0=numpy.nan, z2pt5=numpy.nan, **extras):
        if not numpy.isnan(vs30) and vs30 <= 0:
            raise ValueError('vs30 must be positive')
        if not numpy.isnan(z1pt0) and z1pt0 <= 0:
            raise ValueError('z1pt0 must be positive')
        if not numpy.isnan(z2pt5) and z2pt5 <= 0:
            raise ValueError('z2pt5 must be positive')
        self.location = location
        self.vs30 = vs30
        self.z1pt0 = z1pt0
        self.z2pt5 = z2pt5
        for param, val in extras.items():
            assert param in site_param_dt, param
            setattr(self, param, val)

    def __str__(self):
        """
        >>> import openquake.hazardlib
        >>> loc = openquake.hazardlib.geo.point.Point(1, 2, 3)
        >>> str(Site(loc, 760.0, 100.0, 5.0))
        '<Location=<Latitude=2.000000, Longitude=1.000000, Depth=3.0000>, \
Vs30=760.0000, Depth1.0km=100.0000, Depth2.5km=5.0000>'
        """
        return (
            "<Location=%s, Vs30=%.4f, Depth1.0km=%.4f, "
            "Depth2.5km=%.4f>") % (
            self.location, self.vs30, self.z1pt0, self.z2pt5)

    def __hash__(self):
        return hash((self.location.x, self.location.y))

    def __eq__(self, other):
        return (self.location.x, self.location.y) == (
            other.location.x, other.location.y)

    def __repr__(self):
        """
        >>> import openquake.hazardlib
        >>> loc = openquake.hazardlib.geo.point.Point(1, 2, 3)
        >>> site = Site(loc, 760.0, 100.0, 5.0)
        >>> str(site) == repr(site)
        True
        """
        return self.__str__()


def _extract(array_or_float, indices):
    try:  # if array
        return array_or_float[indices]
    except TypeError:  # if float
        return array_or_float


# dtype of each valid site parameter
site_param_dt = {
    'sids': numpy.uint32,
    'site_id': numpy.uint32,
    'lon': numpy.float64,
    'lat': numpy.float64,
    'depth': numpy.float64,
    'vs30': numpy.float64,
    'kappa0': numpy.float64,
    'vs30measured': bool,
    'z1pt0': numpy.float64,
    'z2pt5': numpy.float64,
    'siteclass': (numpy.string_, 1),
    'geohash': (numpy.string_, 6),
    'z1pt4': numpy.float64,
    'backarc': numpy.uint8,  # 0=forearc,1=backarc,2=alongarc
    'xvf': numpy.float64,
    'soiltype': numpy.uint32,
    'bas': bool,

    # Parameters for site amplification
    'ampcode': ampcode_dt,
    'ec8': (numpy.string_, 1),
    'ec8_p18': (numpy.string_, 2),
    'h800': numpy.float64,
    'geology': (numpy.string_, 20),
    'amplfactor': numpy.float64,
    'fpeak': numpy.float64,
    # Fundamental period and and amplitude of HVRSR spectra
    'THV': numpy.float64,
    'PHV': numpy.float64,

    # parameters for secondary perils
    'friction_mid': numpy.float64,
    'cohesion_mid': numpy.float64,
    'saturation': numpy.float64,
    'dry_density': numpy.float64,
    'Fs': numpy.float64,
    'crit_accel': numpy.float64,
    'unit': (numpy.string_, 5),
    'liq_susc_cat': (numpy.string_, 2),
    'dw': numpy.float64,
    'yield_acceleration': numpy.float64,
    'slope': numpy.float64,
    'gwd': numpy.float64,
    'cti': numpy.float64,
    'dc': numpy.float64,
    'dr': numpy.float64,
    'dwb': numpy.float64,
    'hwater': numpy.float64,
    'precip': numpy.float64,

    # parameters for YoudEtAl2002
    'freeface_ratio': numpy.float64,
    'T_15': numpy.float64,
    'D50_15': numpy.float64,
    'F_15': numpy.float64,
    'T_eq': numpy.float64,

    # other parameters
    'custom_site_id': (numpy.string_, 8),
    'region': numpy.uint32,
    'in_cshm': bool  # used in mcverry
}


class SiteCollection(object):
    """\
    A collection of :class:`sites <Site>`.

    Instances of this class are intended to represent a large collection
    of sites in a most efficient way in terms of memory usage. The most
    common usage is to instantiate it as `SiteCollection.from_points`, by
    passing the set of required parameters, which must be a subset of the
    following parameters:

%s

    .. note::

        If a :class:`SiteCollection` is created from sites containing only
        lon and lat, iterating over the collection will yield
        :class:`Sites <Site>` with a reference depth of 0.0 (the sea level).
        Otherwise, it is possible to model the sites on a realistic
        topographic surface by specifying the `depth` of each site.

    :param sites:
        A list of instances of :class:`Site` class.
    """ % '\n'.join('    - %s: %s' % item
                    for item in sorted(site_param_dt.items())
                    if item[0] not in ('lon', 'lat'))
    req_site_params = ()

    @classmethod
    def from_usgs_shakemap(cls, shakemap_array):
        """
        Build a site collection from a shakemap array
        """
        self = object.__new__(cls)
        self.complete = self
        n = len(shakemap_array)
        dtype = numpy.dtype([(p, site_param_dt[p])
                             for p in 'sids lon lat depth vs30'.split()])
        self.array = arr = numpy.zeros(n, dtype)
        arr['sids'] = numpy.arange(n, dtype=numpy.uint32)
        arr['lon'] = shakemap_array['lon']
        arr['lat'] = shakemap_array['lat']
        arr['depth'] = numpy.zeros(n)
        arr['vs30'] = shakemap_array['vs30']
        return self

    @classmethod  # this is the method used by the engine
    def from_points(cls, lons, lats, depths=None, sitemodel=None,
                    req_site_params=()):
        """
        Build the site collection from

        :param lons:
            a sequence of longitudes
        :param lats:
            a sequence of latitudes
        :param depths:
            a sequence of depths (or None)
        :param sitemodel:
            None or an object containing site parameters as attributes
        :param req_site_params:
            a sequence of required site parameters, possibly empty
        """
        assert len(lons) < U32LIMIT, len(lons)
        if depths is None:
            depths = numpy.zeros(len(lons))
        assert len(lons) == len(lats) == len(depths), (len(lons), len(lats),
                                                       len(depths))
        self = object.__new__(cls)
        self.complete = self
        self.req_site_params = req_site_params
        req = ['sids', 'lon', 'lat', 'depth'] + sorted(
            par for par in req_site_params if par not in ('lon', 'lat'))
        if 'vs30' in req and 'vs30measured' not in req:
            req.append('vs30measured')
        dtype = numpy.dtype([(p, site_param_dt[p]) for p in req])
        self.array = arr = numpy.zeros(len(lons), dtype)
        arr['sids'] = numpy.arange(len(lons), dtype=numpy.uint32)
        arr['lon'] = fix_lon(numpy.array(lons))
        arr['lat'] = numpy.array(lats)
        arr['depth'] = numpy.array(depths)
        if sitemodel is None:
            pass
        elif hasattr(sitemodel, 'reference_vs30_value'):
            self.set_global_params(sitemodel, req_site_params)
        else:
            for name in sitemodel.dtype.names:
                if name not in ('lon', 'lat'):
                    self._set(name, sitemodel[name])
        dupl = get_duplicates(self.array, 'lon', 'lat')
        if dupl:
            # raise a decent error message displaying only the first 9
            # duplicates (there could be millions)
            n = len(dupl)
            dots = ' ...' if n > 9 else ''
            items = list(dupl.items())[:9]
            raise ValueError('There are %d duplicate sites %s%s' %
                             (n, items, dots))
        return self

    def _set(self, param, value):
        if param not in self.array.dtype.names:
            self.add_col(param, site_param_dt[param])
        self.array[param] = value

    xyz = Mesh.xyz

    def set_global_params(
            self, oq, req_site_params=('z1pt0', 'z2pt5', 'backarc')):
        """
        Set the global site parameters
        (vs30, vs30measured, z1pt0, z2pt5, backarc)
        """
        self._set('vs30', oq.reference_vs30_value)
        self._set('vs30measured',
                  oq.reference_vs30_type == 'measured')
        if 'z1pt0' in req_site_params:
            self._set('z1pt0', oq.reference_depth_to_1pt0km_per_sec)
        if 'z2pt5' in req_site_params:
            self._set('z2pt5', oq.reference_depth_to_2pt5km_per_sec)
        if 'backarc' in req_site_params:
            self._set('backarc', oq.reference_backarc)
        
    def filtered(self, indices):
        """
        :param indices:
           a subset of indices in the range [0 .. tot_sites - 1]
        :returns:
           a filtered SiteCollection instance if `indices` is a proper subset
           of the available indices, otherwise returns the full SiteCollection
        """
        if indices is None or len(indices) == len(self):
            return self
        new = object.__new__(self.__class__)
        indices = numpy.uint32(indices)
        new.array = self.array[indices]
        new.complete = self.complete
        return new

    def reduce(self, nsites):
        """
        :returns: a filtered SiteCollection with around nsites (if nsites<=N)
        """
        N = len(self.complete)
        n = N // nsites
        if n <= 1:
            return self
        sids, = numpy.where(self.complete.sids % n == 0)
        return self.filtered(sids)

    def add_col(self, colname, dtype, values=None):
        """
        Add a column to the underlying array
        """
        names = self.array.dtype.names
        dtlist = [(name, self.array.dtype[name]) for name in names]
        dtlist.append((colname, dtype))
        arr = numpy.zeros(len(self), dtlist)
        for name in names:
            arr[name] = self.array[name]
        if values is not None:
            arr[colname] = values
        self.array = arr

    def make_complete(self):
        """
        Turns the site collection into a complete one, if needed
        """
        # reset the site indices from 0 to N-1 and set self.complete to self
        self.array['sids'] = numpy.arange(len(self), dtype=numpy.uint32)
        self.complete = self

    def one(self):
        """
        :returns: a SiteCollection with a site of the minimal vs30
        """
        if 'vs30' in self.array.dtype.names:
            idx = self.array['vs30'].argmin()
        else:
            idx = 0
        return self.filtered([self.sids[idx]])

    # used in preclassical
    def get_cdist(self, rec_or_loc):
        """
        :param rec_or_loc: a record with field 'hypo' or a Point instance
        :returns: array of N euclidean distances from rec['hypo']
        """
        try:
            lon, lat, dep = rec_or_loc['hypo']
        except TypeError:
            lon, lat, dep = rec_or_loc.x, rec_or_loc.y, rec_or_loc.z
        xyz = spherical_to_cartesian(lon, lat, dep).reshape(1, 3)
        return distance.cdist(self.xyz, xyz)[:, 0]

    def __init__(self, sites):
        """
        Build a complete SiteCollection from a list of Site objects
        """
        extra = [(p, site_param_dt[p]) for p in sorted(vars(sites[0]))
                 if p in site_param_dt]
        dtlist = [(p, site_param_dt[p])
                  for p in ('sids', 'lon', 'lat', 'depth')] + extra
        self.array = arr = numpy.zeros(len(sites), dtlist)
        self.complete = self
        for i, site in enumerate(sites):
            arr['sids'][i] = getattr(site, 'id', i)
            arr['lon'][i] = site.location.longitude
            arr['lat'][i] = site.location.latitude
            arr['depth'][i] = site.location.depth
            for p, dt in extra:
                arr[p][i] = getattr(site, p)

        # NB: in test_correlation.py we define a SiteCollection with
        # non-unique sites, so we cannot do an
        # assert len(numpy.unique(self[['lon', 'lat']])) == len(self)

    def __eq__(self, other):
        return not self.__ne__(other)

    def __ne__(self, other):
        return not_equal(self.array, other.array)

    def __toh5__(self):
        names = self.array.dtype.names
        cols = ' '.join(names)
        return {n: self.array[n] for n in names}, {'__pdcolumns__': cols}

    def __fromh5__(self, dic, attrs):
        if isinstance(dic, dict):  # engine >= 3.11
            params = attrs['__pdcolumns__'].split()
            dtype = numpy.dtype([(p, site_param_dt[p]) for p in params])
            self.array = numpy.zeros(len(dic['sids']), dtype)
            for p in dic:
                self.array[p] = dic[p][()]
        else:  # old engine, dic is actually a structured array
            self.array = dic
        self.complete = self

    @property
    def mesh(self):
        """Return a mesh with the given lons, lats, and depths"""
        return Mesh(self['lon'], self['lat'], self['depth'])

    def at_sea_level(self):
        """True if all depths are zero"""
        return (self.depths == 0).all()

    # used in the engine
    def split_max(self, max_sites):
        """
        Split a SiteCollection into SiteCollection instances
        """
        return self.split(numpy.ceil(len(self) / max_sites))

    def split(self, ntiles):
        """
        :param ntiles: number of tiles to generate (rounded if float)
        :returns: self if there are <=1 tiles, otherwise the tiles
        """
        # if ntiles > nsites produce N tiles with a single site each
        ntiles = min(int(numpy.ceil(ntiles)), len(self))
        if ntiles <= 1:
            return [self]
        tiles = []
        for i in range(ntiles):
            sc = SiteCollection.__new__(SiteCollection)
            # smart trick to split in "homogenous" tiles
            sc.array = self.array[self.sids % ntiles == i]
            sc.complete = self
            tiles.append(sc)
        return tiles

    def split_in_tiles(self, hint):
        """
        Split a SiteCollection into a set of tiles with contiguous site IDs
        """
        if hint > len(self):
            hint = len(self)
        tiles = []
        for sids in numpy.array_split(self.sids, hint):
            assert len(sids), 'Cannot split %s in %d tiles' % (self, hint)
            sc = SiteCollection.__new__(SiteCollection)
            sc.array = self.complete.array[sids]
            sc.complete = self.complete
            tiles.append(sc)
        return tiles

    def count_close(self, location, distance):
        """
        :returns: the number of sites within the distance from the location
        """
        return (self.get_cdist(location) < distance).sum()

    def __iter__(self):
        """
        Iterate through all :class:`sites <Site>` in the collection, yielding
        one at a time.
        """
        params = self.array.dtype.names[4:]  # except sids, lons, lats, depths
        sids = self.sids
        for i, location in enumerate(self.mesh):
            kw = {p: self.array[i][p] for p in params}
            s = Site(location, **kw)
            s.id = sids[i]
            yield s

    def filter(self, mask):
        """
        Create a SiteCollection with only a subset of sites.

        :param mask:
            Numpy array of boolean values of the same length as the site
            collection. ``True`` values should indicate that site with that
            index should be included into the filtered collection.
        :returns:
            A new :class:`SiteCollection` instance, unless all the
            values in ``mask`` are ``True``, in which case this site collection
            is returned, or if all the values in ``mask`` are ``False``,
            in which case method returns ``None``. New collection has data
            of only those sites that were marked for inclusion in the mask.
        """
        assert len(mask) == len(self), (len(mask), len(self))
        if mask.all():
            # all sites satisfy the filter, return
            # this collection unchanged
            return self
        if not mask.any():
            # no sites pass the filter, return None
            return None
        # extract indices of Trues from the mask
        indices, = mask.nonzero()
        return self.filtered(indices)

    def assoc(self, site_model, assoc_dist, ignore=()):
        """
        Associate the `site_model` parameters to the sites.
        Log a warning if the site parameters are more distant than
        `assoc_dist`.

        :returns: the site model array reduced to the hazard sites
        """
        m1, m2 = site_model[['lon', 'lat']], self[['lon', 'lat']]
        if len(m1) != len(m2) or (m1 != m2).any():  # associate
            _sitecol, site_model, _discarded = _GeographicObjects(
                site_model).assoc(self, assoc_dist, 'warn')
        ok = set(self.array.dtype.names) & set(site_model.dtype.names) - set(
            ignore) - {'lon', 'lat', 'depth'}
        for name in ok:
            self._set(name, site_model[name])
        for name in set(self.array.dtype.names) - set(site_model.dtype.names):
            if name == 'vs30measured':
                self._set(name, 0)  # default
                # NB: by default reference_vs30_type == 'measured' is 1
                # but vs30measured is 0 (the opposite!!)

        # sanity check
        for param in self.req_site_params:
            if param in ignore:
                continue
            dt = site_param_dt[param]
            if dt is numpy.float64 and (self.array[param] == 0.).all():
                raise ValueError('The site parameter %s is always zero: please '
                                 'check the site model' % param)
        return site_model

    def within(self, region):
        """
        :param region: a shapely polygon
        :returns: a filtered SiteCollection of sites within the region
        """
        mask = numpy.array([
            geometry.Point(rec['lon'], rec['lat']).within(region)
            for rec in self.array])
        return self.filter(mask)

    def within_bbox(self, bbox):
        """
        :param bbox:
            a quartet (min_lon, min_lat, max_lon, max_lat)
        :returns:
            site IDs within the bounding box
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        lons, lats = self['lon'], self['lat']
        if cross_idl(lons.min(), lons.max(), min_lon, max_lon):
            lons = lons % 360
            min_lon, max_lon = min_lon % 360, max_lon % 360
        mask = (min_lon < lons) * (lons < max_lon) * \
               (min_lat < lats) * (lats < max_lat)
        return mask.nonzero()[0]

    def geohash(self, length):
        """
        :param length: length of the geohash in the range 1..8
        :returns: an array of N geohashes, one per site
        """
        l = numpy.uint8(length)
        arr = geohash(self['lon'], self['lat'], l)
        return [row.tobytes() for row in arr]

    def num_geohashes(self, length):
        """
        :param length: length of the geohash in the range 1..8
        :returns: number of distinct geohashes in the site collection
        """
        return len(numpy.unique(self.geohash(length)))

    def calculate_z1pt0(self):
        """
        Compute the column z1pt0 from the vs30
        """
        self.array['z1pt0'] = calculate_z1pt0(self.vs30)

    def calculate_z2pt5(self):
        """
        Compute the column z2pt5 from the vs30 using a formula for NGA-West2
        """
        self.array['z2pt5'] = calculate_z2pt5(self.vs30)

    def __getstate__(self):
        return dict(array=self.array, complete=self.complete)

    def __getitem__(self, sid):
        """
        Return a site record
        """
        return self.array[sid]

    def __getattr__(self, name):
        if name in ('lons', 'lats', 'depths'):  # legacy names
            return self.array[name[:-1]]
        if name not in site_param_dt:
            raise AttributeError(name)
        return self.array[name]

    def __len__(self):
        """
        Return the number of sites in the collection.
        """
        return len(self.array)

    def __repr__(self):
        total_sites = len(self.complete.array)
        return '<SiteCollection with %d/%d sites>' % (
            len(self), total_sites)
