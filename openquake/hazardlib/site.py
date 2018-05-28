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

"""
Module :mod:`openquake.hazardlib.site` defines :class:`Site`.
"""
import numpy
from shapely import geometry
from openquake.baselib.general import split_in_blocks, not_equal
from openquake.hazardlib.geo.utils import fix_lon, cross_idl
from openquake.hazardlib.geo.mesh import Mesh


class Site(object):
    """
    Site object represents a geographical location defined by its position
    as well as its soil characteristics.

    :param location:
        Instance of :class:`~openquake.hazardlib.geo.point.Point` representing
        where the site is located.
    :param vs30:
        Average shear wave velocity in the top 30 m, in m/s.
    :param vs30measured:
        Boolean value, ``True`` if ``vs30`` was measured on that location
        and ``False`` if it was inferred.
    :param z1pt0:
        Vertical distance from earth surface to the layer where seismic waves
        start to propagate with a speed above 1.0 km/sec, in meters.
    :param z2pt5:
        Vertical distance from earth surface to the layer where seismic waves
        start to propagate with a speed above 2.5 km/sec, in km.
    :param backarc":
        Boolean value, ``True`` if the site is in the subduction backarc and
        ``False`` if it is in the subduction forearc or is unknown

    :raises ValueError:
        If any of ``vs30``, ``z1pt0`` or ``z2pt5`` is zero or negative.

    .. note::

        :class:`Sites <Site>` are pickleable
    """
    _slots_ = 'location vs30 vs30measured z1pt0 z2pt5 backarc'.split()

    def __init__(self, location, vs30, vs30measured, z1pt0, z2pt5,
                 backarc=False):
        if not vs30 > 0:
            raise ValueError('vs30 must be positive')
        if not z1pt0 > 0:
            raise ValueError('z1pt0 must be positive')
        if not z2pt5 > 0:
            raise ValueError('z2pt5 must be positive')
        self.location = location
        self.vs30 = vs30
        self.vs30measured = vs30measured
        self.z1pt0 = z1pt0
        self.z2pt5 = z2pt5
        self.backarc = backarc

    def __str__(self):
        """
        >>> import openquake.hazardlib
        >>> loc = openquake.hazardlib.geo.point.Point(1, 2, 3)
        >>> str(Site(loc, 760.0, True, 100.0, 5.0))
        '<Location=<Latitude=2.000000, Longitude=1.000000, Depth=3.0000>, \
Vs30=760.0000, Vs30Measured=True, Depth1.0km=100.0000, Depth2.5km=5.0000, \
Backarc=False>'
        """
        return (
            "<Location=%s, Vs30=%.4f, Vs30Measured=%r, Depth1.0km=%.4f, "
            "Depth2.5km=%.4f, Backarc=%r>") % (
            self.location, self.vs30, self.vs30measured, self.z1pt0,
            self.z2pt5, self.backarc)

    def __hash__(self):
        return hash((self.location.x, self.location.y))

    def __eq__(self, other):
        return (self.location.x, self.location.y) == (
            other.location.x, other.location.y)

    def __repr__(self):
        """
        >>> import openquake.hazardlib
        >>> loc = openquake.hazardlib.geo.point.Point(1, 2, 3)
        >>> site = Site(loc, 760.0, True, 100.0, 5.0)
        >>> str(site) == repr(site)
        True
        """
        return self.__str__()


def _extract(array_or_float, indices):
    try:  # if array
        return array_or_float[indices]
    except TypeError:  # if float
        return array_or_float


class SiteCollection(object):
    """
    A collection of :class:`sites <Site>`.

    Instances of this class are intended to represent a large collection
    of sites in a most efficient way in terms of memory usage.

    .. note::

        If a :class:`SiteCollection` is created from sites containing only
        lon and lat, iterating over the collection will yield
        :class:`Sites <Site>` with a reference depth of 0.0 (the sea level).
        Otherwise, it is possible to model the sites on a realistic
        topographic surface by specifying the `depth` of each site.

    :param sites:
        A list of instances of :class:`Site` class.
    """
    dtype = numpy.dtype([
        ('sids', numpy.uint32),
        ('lons', numpy.float64),
        ('lats', numpy.float64),
        ('depths', numpy.float64),
        ('vs30', numpy.float64),
        ('vs30measured', numpy.bool),
        ('z1pt0', numpy.float64),
        ('z2pt5', numpy.float64),
        ('backarc', numpy.bool),
    ])

    @classmethod
    def from_shakemap(cls, shakemap_array):
        """
        Build a site collection from a shakemap array
        """
        self = object.__new__(cls)
        self.complete = self
        n = len(shakemap_array)
        self.array = arr = numpy.zeros(n, self.dtype)
        arr['sids'] = numpy.arange(n, dtype=numpy.uint32)
        arr['lons'] = shakemap_array['lon']
        arr['lats'] = shakemap_array['lat']
        arr['depths'] = numpy.zeros(n)
        arr['vs30'] = shakemap_array['vs30']
        arr.flags.writeable = False
        return self

    @classmethod
    def from_points(cls, lons, lats, depths=None, sitemodel=None):
        """
        Build the site collection from

        :param lons:
            a sequence of longitudes
        :param lats:
            a sequence of latitudes
        :param depths:
            a sequence of depths (or None)
        :param sitemodel:
            None or an object containing the attributes
            reference_vs30_value,
            reference_vs30_type,
            reference_depth_to_1pt0km_per_sec,
            reference_depth_to_2pt5km_per_sec,
            reference_backarc
        """
        if depths is None:
            depths = numpy.zeros(len(lons))
        assert len(lons) == len(lats) == len(depths), (len(lons), len(lats),
                                                       len(depths))
        self = object.__new__(cls)
        self.complete = self
        self.array = arr = numpy.zeros(len(lons), self.dtype)
        arr['sids'] = numpy.arange(len(lons), dtype=numpy.uint32)
        arr['lons'] = fix_lon(numpy.array(lons))
        arr['lats'] = numpy.array(lats)
        arr['depths'] = numpy.array(depths)
        if sitemodel is None:
            pass
        elif hasattr(sitemodel, 'reference_vs30_value'):  # oqparam
            arr['vs30'] = sitemodel.reference_vs30_value
            arr['vs30measured'] = sitemodel.reference_vs30_type == 'measured'
            arr['z1pt0'] = sitemodel.reference_depth_to_1pt0km_per_sec
            arr['z2pt5'] = sitemodel.reference_depth_to_2pt5km_per_sec
            arr['backarc'] = sitemodel.reference_backarc
        elif 'vs30' in sitemodel.dtype.names:  # site params
            for name in sitemodel.dtype.names[2:]:  # except lon, lat
                arr[name] = sitemodel[name]
        return self

    xyz = Mesh.xyz

    def filtered(self, indices):
        """
        :param indices:
           a subset of indices in the range [0 .. tot_sites - 1]
        :returns:
           a filtered SiteCollection instance if `indices` is a proper subset
           of the available indices, otherwise returns the full SiteCollection
        """
        if len(indices) == len(self):
            return self
        new = object.__new__(self.__class__)
        indices = numpy.uint32(sorted(indices))
        new.array = self.array[indices]
        new.complete = self.complete
        return new

    def make_complete(self):
        """
        Turns the site collection into a complete one, if needed
        """
        # reset the site indices from 0 to N-1 and set self.complete to self
        self.array['sids'] = numpy.arange(len(self), dtype=numpy.uint32)
        self.complete = self

    def __init__(self, sites):
        """
        Build a complete SiteCollection from a list of Site objects
        """
        if hasattr(sites, 'sids'):
            numpy.testing.assert_equal(sites.sids, numpy.arange(len(sites)))
        self.array = arr = numpy.zeros(len(sites), self.dtype)
        self.complete = self
        for i in range(len(arr)):
            arr['sids'][i] = i
            arr['lons'][i] = sites[i].location.longitude
            arr['lats'][i] = sites[i].location.latitude
            arr['depths'][i] = sites[i].location.depth
            arr['vs30'][i] = sites[i].vs30
            arr['vs30measured'][i] = sites[i].vs30measured
            arr['z1pt0'][i] = sites[i].z1pt0
            arr['z2pt5'][i] = sites[i].z2pt5
            arr['backarc'][i] = sites[i].backarc

        # protect arrays from being accidentally changed. it is useful
        # because we pass these arrays directly to a GMPE through
        # a SiteContext object and if a GMPE is implemented poorly it could
        # modify the site values, thereby corrupting site and all the
        # subsequent calculation. note that this doesn't protect arrays from
        # being changed by calling itemset()
        arr.flags.writeable = False

    def __eq__(self, other):
        return not self.__ne__(other)

    def __ne__(self, other):
        return not_equal(self.array, other.array)

    def __toh5__(self):
        return self.array, {}

    def __fromh5__(self, array, attrs):
        self.array = array
        self.complete = self

    @property
    def mesh(self):
        """Return a mesh with the given lons, lats, and depths"""
        return Mesh(self.lons, self.lats, self.depths)

    def at_sea_level(self):
        """True if all depths are zero"""
        return (self.depths == 0).all()

    # used in the engine when computing the hazard statistics
    def split_in_tiles(self, hint):
        """
        Split a SiteCollection into a set of tiles (SiteCollection instances).

        :param hint: hint for how many tiles to generate
        """
        tiles = []
        for seq in split_in_blocks(range(len(self)), hint or 1):
            sc = SiteCollection.__new__(SiteCollection)
            sc.array = self.array[numpy.array(seq, int)]
            tiles.append(sc)
        return tiles

    def __iter__(self):
        """
        Iterate through all :class:`sites <Site>` in the collection, yielding
        one at a time.
        """
        for i, location in enumerate(self.mesh):
            yield Site(location, self.vs30[i], self.vs30measured[i],
                       self.z1pt0[i], self.z2pt5[i], self.backarc[i])

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

    def within(self, region):
        """
        :param region: a shapely polygon
        :returns: a filtered SiteCollection of sites within the region
        """
        mask = numpy.array([
            geometry.Point(rec['lons'], rec['lats']).within(region)
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
        lons, lats = self.array['lons'], self.array['lats']
        if cross_idl(lons.min(), lons.max()) or cross_idl(min_lon, max_lon):
            lons = lons % 360
            min_lon, max_lon = min_lon % 360, max_lon % 360
        mask = (min_lon < lons) * (lons < max_lon) * \
               (min_lat < lats) * (lats < max_lat)
        return mask.nonzero()[0]

    def __getstate__(self):
        return dict(array=self.array, complete=self.complete)

    def __getitem__(self, sid):
        """
        Return a site record
        """
        return self.array[sid]

    def __getattr__(self, name):
        if name not in ('vs30 vs30measured z1pt0 z2pt5 backarc lons lats '
                        'depths sids'):
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
