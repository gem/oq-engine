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
Module :mod:`openquake.hazardlib.site` defines :class:`Site`.
"""

import numpy
import pandas
from scipy.spatial import distance
from shapely import geometry
from openquake.baselib import hdf5, general
from openquake.baselib.general import not_equal, get_duplicates, cached_property
from openquake.hazardlib.geo.utils import (
    fix_lon, cross_idl, _GeographicObjects, geohash, geohash3, CODE32,
    spherical_to_cartesian, get_middle_point, geolocate)
from openquake.hazardlib.geo.geodetic import npoints_towards
from openquake.hazardlib.geo.mesh import Mesh

U32LIMIT = 2 ** 32
F64 = numpy.float64
ampcode_dt = (numpy.bytes_, 4)
param = dict(
    vs30measured='reference_vs30_type',
    vs30='reference_vs30_value',
    z1pt0='reference_depth_to_1pt0km_per_sec',
    z2pt5='reference_depth_to_2pt5km_per_sec',
    region='region',
    xvf='xvf')


# TODO: equivalents of calculate_z1pt0 and calculate_z2pt5
# are inside some GSIM implementations, we should avoid duplication
def calculate_z1pt0(vs30, country):
    '''
    Reads an array of vs30 values (in m/s) and returns the depth to
    the 1.0 km/s velocity horizon (in m)
    Ref: Chiou, B. S.-J. and Youngs, R. R., 2014. 'Update of the
    Chiou and Youngs NGA model for the average horizontal component
    of peak ground motion and response spectra.' Earthquake Spectra,
    30(3), pp.1117–1153.
    :param vs30: the shear wave velocity (in m/s) at a depth of 30m
    :param country: country as defined by geoBoundariesCGAZ_ADM0.gpkg

    '''
    z1pt0 = numpy.zeros(len(vs30))
    df = pandas.DataFrame({'codes': country})
    idx_glo = df.loc[df.codes != 'JPN'].index.values
    idx_jpn = df.loc[df.codes == 'JPN'].index.values

    c1_glo = 571 ** 4.
    c2_glo = 1360.0 ** 4.
    z1pt0[idx_glo] = numpy.exp((-7.15 / 4.0) * numpy.log(
        (vs30[idx_glo] ** 4 + c1_glo) / (c2_glo + c1_glo)))

    c1_jpn = 412 ** 2.
    c2_jpn = 1360.0 ** 2.
    z1pt0[idx_jpn] = numpy.exp((-5.23 / 2.0) * numpy.log(
        (vs30[idx_jpn] ** 2 + c1_jpn) / (c2_jpn + c1_jpn)))

    return z1pt0


def calculate_z2pt5(vs30, country):
    '''
    Reads an array of vs30 values (in m/s) and returns the depth
    to the 2.5 km/s velocity horizon (in km)
    Ref: Campbell, K.W. & Bozorgnia, Y., 2014.
    'NGA-West2 ground motion model for the average horizontal components of
    PGA, PGV, and 5pct damped linear acceleration response spectra.'
    Earthquake Spectra, 30(3), pp.1087–1114.

    :param vs30: the shear wave velocity (in m/s) at a depth of 30 m
    :param country: country as defined by geoBoundariesCGAZ_ADM0.gpkg

    '''
    z2pt5 = numpy.zeros(len(vs30))
    df = pandas.DataFrame({'codes': country})
    idx_glo = df.loc[df.codes != 'JPN'].index.values
    idx_jpn = df.loc[df.codes == 'JPN'].index.values

    c1_glo = 7.089
    c2_glo = -1.144
    z2pt5[idx_glo] = numpy.exp(c1_glo + numpy.log(vs30[idx_glo]) * c2_glo)

    c1_jpn = 5.359
    c2_jpn = -1.102
    z2pt5[idx_jpn] = numpy.exp(c1_jpn + c2_jpn * numpy.log(vs30[idx_jpn]))

    return z2pt5


def rnd5(lons):
    return numpy.round(lons, 5)


class TileGetter:
    """
    An extractor complete->tile
    """
    def __init__(self, tileno, ntiles):
        self.tileno = tileno
        self.ntiles = ntiles

    def __call__(self, complete, ilabel=None):
        if self.ntiles == 1 and ilabel is None:
            return complete
        sc = SiteCollection.__new__(SiteCollection)
        array = complete.array[complete.sids % self.ntiles == self.tileno]
        if ilabel is not None:
            sc.array = array[array['ilabel'] == ilabel]
        else:
            sc.array = array
        sc.complete = complete
        return sc


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
        If ``vs30`` is zero or negative
        OR
        ``z1pt0`` or ``z2pt5`` is zero or negative AND not -999 (a value of
        -999 informs basin param using GMMs to estimate values for such sites
        with median value from GMM's own vs30 to z1pt0 or z2pt5 relationship).

    .. note::

        :class:`Sites <Site>` are pickleable
    """

    def __init__(self, location, vs30=numpy.nan,
                 z1pt0=numpy.nan, z2pt5=numpy.nan, **extras):
        if not numpy.isnan(vs30) and vs30 <= 0:
            raise ValueError('vs30 must be positive')
        if not numpy.isnan(z1pt0) and z1pt0 <= 0 and z1pt0 != -999:
            raise ValueError('z1pt0 must be positive or set to -999')
        if not numpy.isnan(z2pt5) and z2pt5 <= 0 and z2pt5 != -999:
            raise ValueError('z2pt5 must be positive or set to -999')

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
    'z_sed': numpy.float64,
    'siteclass': (numpy.bytes_, 1),
    'ilabel': numpy.uint8,
    'geohash': (numpy.bytes_, 6),
    'z1pt4': numpy.float64,
    'backarc': numpy.uint8,  # 0=forearc,1=backarc,2=alongarc
    'xvf': numpy.float64,
    'soiltype': numpy.uint32,
    'bas': bool,

    # Parameters for site amplification
    'ampcode': ampcode_dt,
    'ec8': (numpy.bytes_, 1),
    'ec8_p18': (numpy.bytes_, 2),
    'h800': numpy.float64,
    'geology': (numpy.bytes_, 20),
    'amplfactor': numpy.float64,
    'ch_ampl03': numpy.float64,
    'ch_ampl06': numpy.float64,
    'ch_phis2s03': numpy.float64,
    'ch_phis2s06': numpy.float64,
    'ch_phiss03': numpy.float64,
    'ch_phiss06': numpy.float64,
    'f0': numpy.float64,
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
    'unit': (numpy.bytes_, 5),
    'liq_susc_cat': (numpy.bytes_, 2),
    'dw': numpy.float64,
    'yield_acceleration': numpy.float64,
    'slope': numpy.float64,
    'relief': numpy.float64,
    'gwd': numpy.float64,
    'cti': numpy.float64,
    'dc': numpy.float64,
    'dr': numpy.float64,
    'dwb': numpy.float64,
    'zwb': numpy.float64,
    'tri': numpy.float64,
    'hwater': numpy.float64,
    'precip': numpy.float64,
    'lithology': (numpy.bytes_, 2),
    'landcover': (numpy.float64),
    'hratio': (numpy.float64),
    'tslope': (numpy.float64),
    'slab_thickness': (numpy.float64),

    # parameters for YoudEtAl2002
    'freeface_ratio': numpy.float64,
    'T_15': numpy.float64,
    'D50_15': numpy.float64,
    'F_15': numpy.float64,
    'T_eq': numpy.float64,

    # other parameters
    'custom_site_id': (numpy.bytes_, 8),
    'region': numpy.uint32,
    'in_cshm': bool  # used in mcverry
}


def add(string, suffix, maxlen):
    """
    Add a suffix to a string staying within the maxlen limit

    >>> add('pippo', ':xxx', 8)
    'pipp:xxx'
    >>> add('pippo', ':x', 8)
    'pippo:x'
    """
    L = len(string)
    assert L < maxlen, string
    assert len(suffix) < maxlen, suffix
    n = len(suffix)
    return string[:maxlen-n] + suffix


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
    def from_(cls, array):
        """
        Build a site collection from a site model array
        """
        self = object.__new__(cls)
        self.array = array
        self.complete = self
        return self

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
            if hasattr(sitemodel, 'dtype'):
                names = set(sitemodel.dtype.names)
                sm = sitemodel
            else:
                sm = vars(sitemodel)
                names = set(sm) & set(req_site_params)
            for name in names:
                if name not in ('lon', 'lat'):
                    self._set(name, sm[name])
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

    @classmethod
    def from_planar(cls, rup, point='TC', toward_azimuth=90,
                    direction='positive', hdist=100, step=5.,
                    req_site_params=()):
        """
        :param rup: a rupture built with `rupture.get_planar`
        :return: a :class:`openquake.hazardlib.site.SiteCollection` instance
        """
        sfc = rup.surface
        if point == 'TC':
            pnt = sfc.get_top_edge_centroid()
            lon, lat = pnt.x, pnt.y
        elif point == 'BC':
            lon, lat = get_middle_point(
                sfc.corner_lons[2], sfc.corner_lats[2],
                sfc.corner_lons[3], sfc.corner_lats[3])
        else:
            idx = {'TL': 0, 'TR': 1, 'BR': 2, 'BL': 3}[point]
            lon = sfc.corner_lons[idx]
            lat = sfc.corner_lats[idx]
        depth = 0
        vdist = 0
        npoints = hdist / step
        strike = rup.surface.strike

        pointsp = []
        pointsn = []
        if direction in ['positive', 'both']:
            azi = (strike + toward_azimuth) % 360
            pointsp = npoints_towards(
                lon, lat, depth, azi, hdist, vdist, npoints)

        if direction in ['negative', 'both']:
            idx = 0 if direction == 'negative' else 1
            azi = (strike + toward_azimuth + 180) % 360
            pointsn = npoints_towards(
                lon, lat, depth, azi, hdist, vdist, npoints)

        if len(pointsn):
            lons = reversed(pointsn[0][idx:])
            lats = reversed(pointsn[1][idx:])
        else:
            lons = pointsp[0]
            lats = pointsp[1]
        return cls.from_points(lons, lats, None, rup, req_site_params)

    def _set(self, param, value):
        self.add_col(param, site_param_dt[param])
        self.array[param] = value

    xyz = Mesh.xyz

    def set_global_params(self, oq, req_site_params=('z1pt0', 'z2pt5')):
        """
        Set the global site parameters
        (vs30, vs30measured, z1pt0, z2pt5)
        """
        self._set('vs30', oq.reference_vs30_value)
        self._set('vs30measured',
                  oq.reference_vs30_type == 'measured')
        if 'z1pt0' in req_site_params:
            self._set('z1pt0', oq.reference_depth_to_1pt0km_per_sec)
        if 'z2pt5' in req_site_params:
            self._set('z2pt5', oq.reference_depth_to_2pt5km_per_sec)

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

    # tested in classical/case_38
    def multiply(self, vs30s,
                 soil_classes=numpy.array(
                     [b'E', b'DE', b'D', b'CD', b'C', b'BC', b'B', b'A']),
                 soil_values=F64([152, 213, 305, 442, 640, 914, 1500])):
        """
        Multiply a site collection with the given vs30 values.
        NB: if there are multiple values the sites with vs30 = -999. are multiplied,
        otherwise the given value is applied to all sites.
        """
        classes = general.find_among(soil_classes, soil_values, vs30s)
        n = len(vs30s)
        N = len(self)
        dt = self.array.dtype
        names = list(dt.names)
        try:
            dt['custom_site_id']
        except KeyError:
            new_csi = True
            dt = [('custom_site_id', site_param_dt['custom_site_id'])] + [
                (n, dt[n]) for n in names]
            names.insert(0, 'custom_site_id')
        else:
            new_csi = False
        ok = self['vs30'] == -999.
        sites_to_multiply = ok.sum()
        tot = sites_to_multiply * n + (N - sites_to_multiply)
        array = numpy.empty(tot, dt)
        j = 0
        multi_vs30 = len(vs30s) > 1
        for i, orig_rec in enumerate(self.array):
            if multi_vs30 and not ok[i]:  # do not multiply
                rec = array[j]
                for name in names:
                    if name == 'custom_site_id':
                        rec[name] = (f'{j}'.encode('ascii') if new_csi
                                     else orig_rec[name])
                    else:
                        rec[name] = orig_rec[name]
                j += 1
                continue
            # else override the vs30
            for cl, vs30 in zip(classes, vs30s):
                rec = array[j]
                for name in names:
                    if name == 'custom_site_id' and new_csi:
                        # tested in classical/case_08
                        rec[name] = add(f'{i}'.encode('ascii'), b':' + cl, 8)
                    elif name == 'custom_site_id':
                        # tested in classical/case_38
                        rec[name] = add(orig_rec[name], b':' + cl, 8)
                    elif name == 'vs30':
                        rec[name] = vs30
                    elif name == 'sids':
                        rec[name] = j
                    else:
                        rec[name] = orig_rec[name]
                j += 1
        new = object.__new__(self.__class__)
        new.array = array
        new.complete = new
        return new

    def get_around(self, lon, lat, digits=5):
        """
        :returns: the submesh around lon, lat with the given precision
        """
        out = []
        lons = numpy.round(self.lons, digits)
        lats = numpy.round(self.lats, digits)
        for i, (lo, la) in enumerate(zip(lons, lats)):
            if lo == lon and la == lat:
                out.append(i)
        return self[out]

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
        Add a column to the underlying array (if not already there)
        """
        names = self.array.dtype.names
        if colname not in names:
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
                 if p in site_param_dt and p != 'depth']
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

    def split(self, ntiles, minsize=1):
        """
        :param ntiles: number of tiles to generate (ceiled if float)
        :returns: self if there are <=1 tiles, otherwise the tiles
        """
        maxtiles = numpy.ceil(len(self) / minsize)
        ntiles = min(numpy.ceil(ntiles), maxtiles)
        return [TileGetter(i, ntiles) for i in range(int(ntiles))]

    def split_in_tiles(self, hint):
        """
        Split a SiteCollection into a set of tiles with contiguous site IDs
        """
        if hint <= 1:
            return [self]
        elif hint > len(self):
            hint = len(self)
        tiles = []
        for tileno in range(hint):
            ok = self.sids % hint == tileno
            if ok.any():
                sc = SiteCollection.__new__(SiteCollection)
                sc.array = self.complete.array[self.sids[ok]]
                sc.complete = self.complete
                tiles.append(sc)
        return tiles

    def split_by_gh3(self):
        """
        Split a SiteCollection into a set of tiles with the same geohash3
        """
        gh3s = geohash3(self.lons, self.lats)
        gb = pandas.DataFrame(dict(sid=self.sids, gh3=gh3s)).groupby('gh3')
        tiles = []
        for gh3, df in gb:
            sc = SiteCollection.__new__(SiteCollection)
            sc.array = self.complete.array[df.sid]
            sc.complete = self.complete
            sc.gh3 = gh3
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
        # NB: self != self.complete in the impact tests with stations
        m1, m2 = site_model[['lon', 'lat']], self.complete[['lon', 'lat']]
        if len(m1) != len(m2) or (m1 != m2).any():  # associate
            _sitecol, site_model, _discarded = _GeographicObjects(
                site_model).assoc(self.complete, assoc_dist, 'warn')
        ok = set(self.array.dtype.names) & set(site_model.dtype.names) - set(
            ignore) - {'lon', 'lat', 'depth'}
        for name in ok:
            vals = site_model[name]
            self._set(name, vals[self.sids])
            self.complete._set(name, vals)

        # sanity check
        for param in self.req_site_params:
            if param in ignore:
                continue
            dt = site_param_dt[param]
            if dt is numpy.float64 and (self.array[param] == 0.).all():
                raise ValueError('The site parameter %s is always zero: please'
                                 ' check the site model' % param)
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

    def extend(self, lons, lats):
        """
        Extend the site collection to additional (and different) points.
        Used for station_data in conditioned GMFs.
        """
        assert len(lons) == len(lats), (len(lons), len(lats))
        complete = self.complete
        orig = set(zip(rnd5(complete.lons), rnd5(complete.lats)))
        new = set(zip(rnd5(lons), rnd5(lats))) - orig
        if not new:
            return self
        lons, lats = zip(*sorted(new))
        N1 = len(complete)
        N2 = len(new)
        array = numpy.zeros(N1 + N2, self.array.dtype)
        array[:N1] = complete.array
        array[N1:]['sids'] = numpy.arange(N1, N1+N2)
        array[N1:]['lon'] = lons
        array[N1:]['lat'] = lats
        complete.array = array

    @cached_property
    def countries(self):
        """
        Return the countries for each site in the SiteCollection.
        The boundaries of the countries are defined as in the file
        geoBoundariesCGAZ_ADM0.gpkg
        """
        from openquake.commonlib import readinput
        geom_df = readinput.read_countries_df()
        lonlats = numpy.zeros((len(self), 2), numpy.float32)
        lonlats[:, 0] = self.lons
        lonlats[:, 1] = self.lats
        return geolocate(lonlats, geom_df)

    def by_country(self):
        """
        Returns a table with the number of sites per country.
        """
        uni, cnt = numpy.unique(self.countries, return_counts=True)
        out = numpy.zeros(len(uni), [('country', (numpy.bytes_, 3)),
                                     ('num_sites', int)])
        out['country'] = uni
        out['num_sites'] = cnt
        out.sort(order='num_sites')
        return out

    def geohash(self, length):
        """
        :param length: length of the geohash in the range 1..8
        :returns: an array of N geohashes, one per site
        """
        ln = numpy.uint8(length)
        arr = CODE32[geohash(self['lon'], self['lat'], ln)]
        return [row.tobytes() for row in arr]

    def num_geohashes(self, length):
        """
        :param length: length of the geohash in the range 1..8
        :returns: number of distinct geohashes in the site collection
        """
        return len(numpy.unique(self.geohash(length)))

    def calculate_z1pt0(self):
        """
        Compute the column z1pt0 from the vs30 using a region-dependent
        formula for NGA-West2
        """
        self.array['z1pt0'] = calculate_z1pt0(self.vs30, self.countries)

    def calculate_z2pt5(self):
        """
        Compute the column z2pt5 from the vs30 using a region-dependent
        formula for NGA-West2
        """
        self.array['z2pt5'] = calculate_z2pt5(self.vs30, self.countries)

    def __getstate__(self):
        return dict(array=self.array, complete=self.complete)

    def __getitem__(self, sid):
        """
        Return a site record
        """
        return self.array[sid]

    def __getattr__(self, name):
        if name in ('lons', 'lats'):  # legacy names
            return self.array[name[:-1]]
        if name == 'depths':
            try:
                return self.array['depth']
            except ValueError:  # missing depth
                return numpy.zeros_like(self.array['lon'])
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


def check_all_equal(mosaic_model, dicts, *keys):
    """
    Check all the dictionaries have the same value for the same key
    """
    if not dicts:
        return
    dic0 = dicts[0]
    for key in keys:
        for dic in dicts[1:]:
            if dic[key] != dic0[key]:
                raise RuntimeError('Inconsistent key %s!=%s while processing %s',
                                   dic[key], dic0[key], mosaic_model)


def merge_without_dupl(array1, array2, uniquefield):
    """
    >>> dt = [('code', 'S1'), ('value', numpy.int32)]
    >>> a1 = numpy.array([('a', 1), ('b', 2)], dt)
    >>> a2 = numpy.array([('b', 2), ('c', 3)], dt)
    >>> merged, dupl = merge_without_dupl(a1, a2, 'code')
    >>> merged
    array([(b'a', 1), (b'b', 2), (b'c', 3)],
          dtype=[('code', 'S1'), ('value', '<i4')])
    >>> a2[dupl]
    array([(b'b', 2)], dtype=[('code', 'S1'), ('value', '<i4')])
    """
    dtype = {}
    for array in (array1, array2):
        for name in array.dtype.names:
            dtype[name] = array.dtype[name]
    dupl = numpy.isin(array2[uniquefield], array1[uniquefield])
    new = array2[~dupl]
    N = len(array1) + len(new)
    array = numpy.zeros(N, [(n, dtype[n]) for n in dtype])
    for n in dtype:
        if n in array1.dtype.names:
            array[n][:len(array1)] = array1[n]
        if n in array2.dtype.names:
            array[n][len(array1):] = new[n]
    return array, dupl


def merge_sitecols(hdf5fnames, mosaic_model='', check_gmfs=False):
    """
    Read a number of site collections from the given filenames
    and returns a single SiteCollection instance, plus a list
    of site ID arrays, one for each site collection, excluding the duplicates.

    If `check_gmfs` is set, assume there are `gmf_data` groups and
    make sure the attributes are consistent (i.e. the same over all files).
    """
    sitecols = []
    attrs = []
    for fname in hdf5fnames:
        with hdf5.File(fname, 'r') as f:
            sitecol = f['sitecol']
            sitecols.append(sitecol)
            if check_gmfs:
                attrs.append(dict(f['gmf_data'].attrs))
    sitecol = sitecols[0]
    converters = [{sid: i for i, sid in enumerate(sitecol.sids)}]
    if len(sitecols) == 1:
        return sitecol, converters

    if attrs:
        check_all_equal(mosaic_model, attrs, '__pdcolumns__', 'effective_time',
                        'investigation_time')

    assert 'custom_site_id' in sitecol.array.dtype.names
    new = object.__new__(sitecol.__class__)
    new.array = sitecol.array
    offset = len(sitecol)
    for sc in sitecols[1:]:
        new.array, dupl = merge_without_dupl(
            new.array, sc.array, 'custom_site_id')
        conv = {sid: offset + i for i, sid in enumerate(sc.sids[~dupl])}
        converters.append(conv)
        offset += dupl.sum()
    new.array['sids'] = numpy.arange(len(new.array))
    new.complete = new
    return new, converters
