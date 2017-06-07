# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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

from openquake.baselib.python3compat import range
from openquake.baselib.slots import with_slots
from openquake.baselib.general import split_in_blocks
from openquake.hazardlib.geo.mesh import Mesh


@with_slots
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


@with_slots
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
        ('_vs30', numpy.float64),
        ('_vs30measured', numpy.bool),
        ('_z1pt0', numpy.float64),
        ('_z2pt5', numpy.float64),
        ('_backarc', numpy.bool),
    ])
    _slots_ = dtype.names

    @classmethod
    def from_points(cls, lons, lats, depths, sitemodel):
        """
        Build the site collection from

        :param lons:
            a sequence of longitudes
        :param lats:
            a sequence of latitudes
        :param depths:
            a sequence of depths
        :param sitemodel:
            an object containing the attributes
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
        self = cls.__new__(cls)
        self.complete = self
        self.total_sites = len(lons)
        self.sids = numpy.arange(len(lons), dtype=numpy.uint32)
        self.lons = numpy.array(lons)
        self.lats = numpy.array(lats)
        self.depths = numpy.array(depths)
        self._vs30 = sitemodel.reference_vs30_value
        self._vs30measured = sitemodel.reference_vs30_type == 'measured'
        self._z1pt0 = sitemodel.reference_depth_to_1pt0km_per_sec
        self._z2pt5 = sitemodel.reference_depth_to_2pt5km_per_sec
        self._backarc = sitemodel.reference_backarc
        return self

    def __init__(self, sites):
        self.complete = self
        self.total_sites = n = len(sites)
        self.sids = numpy.zeros(n, dtype=int)
        self.lons = numpy.zeros(n, dtype=float)
        self.lats = numpy.zeros(n, dtype=float)
        self.depths = numpy.zeros(n, dtype=float)
        self._vs30 = numpy.zeros(n, dtype=float)
        self._vs30measured = numpy.zeros(n, dtype=bool)
        self._z1pt0 = numpy.zeros(n, dtype=float)
        self._z2pt5 = numpy.zeros(n, dtype=float)
        self._backarc = numpy.zeros(n, dtype=bool)

        for i in range(n):
            self.sids[i] = i
            self.lons[i] = sites[i].location.longitude
            self.lats[i] = sites[i].location.latitude
            self.depths[i] = sites[i].location.depth
            self._vs30[i] = sites[i].vs30
            self._vs30measured[i] = sites[i].vs30measured
            self._z1pt0[i] = sites[i].z1pt0
            self._z2pt5[i] = sites[i].z2pt5
            self._backarc[i] = sites[i].backarc

        # protect arrays from being accidentally changed. it is useful
        # because we pass these arrays directly to a GMPE through
        # a SiteContext object and if a GMPE is implemented poorly it could
        # modify the site values, thereby corrupting site and all the
        # subsequent calculation. note that this doesn't protect arrays from
        # being changed by calling itemset()
        for arr in (self._vs30, self._vs30measured, self._z1pt0, self._z2pt5,
                    self.lons, self.lats, self.depths, self._backarc,
                    self.sids):
            arr.flags.writeable = False

    def __toh5__(self):
        array = numpy.zeros(self.total_sites, self.dtype)
        for slot in self._slots_:
            array[slot] = getattr(self, slot)
        attrs = dict(total_sites=self.total_sites)
        return array, attrs

    def __fromh5__(self, array, attrs):
        for slot in self._slots_:
            setattr(self, slot, array[slot])
        vars(self).update(attrs)
        self.complete = self

    @property
    def mesh(self):
        """Return a mesh with the given lons, lats, and depths"""
        return Mesh(self.lons, self.lats, self.depths)

    @property
    def indices(self):
        """The full set of indices from 0 to total_sites - 1"""
        return numpy.arange(0, self.total_sites)

    def at_sea_level(self):
        """True if all depths are zero"""
        return (self.depths == 0).all()

    def split_in_tiles(self, hint):
        """
        Split a SiteCollection into a set of tiles (SiteCollection instances).

        :param hint: hint for how many tiles to generate
        """
        tiles = []
        for seq in split_in_blocks(range(len(self)), hint or 1):
            indices = numpy.array(seq, int)
            sc = SiteCollection.__new__(SiteCollection)
            sc.complete = sc
            sc.total_sites = len(indices)
            sc.sids = self.sids[indices]
            sc.lons = self.lons[indices]
            sc.lats = self.lats[indices]
            sc.depths = self.depths[indices]
            sc._vs30 = _extract(self._vs30, indices)
            sc._vs30measured = _extract(self._vs30measured, indices)
            sc._z1pt0 = _extract(self._z1pt0, indices)
            sc._z2pt5 = _extract(self._z2pt5, indices)
            sc._backarc = _extract(self._backarc, indices)
            tiles.append(sc)
        return tiles

    def __iter__(self):
        """
        Iterate through all :class:`sites <Site>` in the collection, yielding
        one at a time.
        """
        if isinstance(self.vs30, float):  # from points
            for i, location in enumerate(self.mesh):
                yield Site(location, self._vs30, self._vs30measured,
                           self._z1pt0, self._z2pt5, self._backarc)
        else:  # from sites
            for i, location in enumerate(self.mesh):
                yield Site(location, self.vs30[i], self.vs30measured[i],
                           self.z1pt0[i], self.z2pt5[i], self.backarc[i])

    def filter(self, mask):
        """
        Create a FilteredSiteCollection with only a subset of sites
        from this one.

        :param mask:
            Numpy array of boolean values of the same length as this sites
            collection. ``True`` values should indicate that site with that
            index should be included into the filtered collection.
        :returns:
            A new :class:`FilteredSiteCollection` instance, unless all the
            values in ``mask`` are ``True``, in which case this site collection
            is returned, or if all the values in ``mask`` are ``False``,
            in which case method returns ``None``. New collection has data
            of only those sites that were marked for inclusion in mask.
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
        [indices] = mask.nonzero()
        return FilteredSiteCollection(indices, self)

    def __len__(self):
        """
        Return the number of sites in the collection.
        """
        return self.total_sites

    def __repr__(self):
        return '<SiteCollection with %d sites>' % self.total_sites

# adding a number of properties for the site model data
for name in 'vs30 vs30measured z1pt0 z2pt5 backarc'.split():
    def getarray(sc, name=name):  # sc is a SiteCollection
        value = getattr(sc, '_' + name)
        if isinstance(value, (float, bool)):
            arr = numpy.array([value] * len(sc), dtype=type(value))
            arr.flags.writeable = False
            return arr
        else:
            return value
    setattr(SiteCollection, name, property(getarray, doc='%s array' % name))


@with_slots
class FilteredSiteCollection(object):
    """
    A class meant to store proper subsets of a complete collection of sites
    in a memory-efficient way.

    :param indices:
        an array of indices referring to the complete site collection
    :param complete:
        the complete site collection the filtered collection was
        derived from

    Notice that if you filter a FilteredSiteCollection `fsc`, you will
    get a different FilteredSiteCollection referring to the complete
    SiteCollection `fsc.complete`, not to the filtered collection `fsc`.
    """
    _slots_ = 'indices complete'.split()

    def __init__(self, indices, complete):
        if complete is not complete.complete:
            raise ValueError(
                'You should pass a full site collection, not %s' % complete)
        self.indices = indices
        self.complete = complete

    @property
    def total_sites(self):
        """The total number of the original sites, without filtering"""
        return self.complete.total_sites

    @property
    def mesh(self):
        """Return a mesh with the given lons, lats, and depths"""
        return Mesh(self.lons, self.lats, self.depths)

    def at_sea_level(self):
        """True if all depths are zero"""
        return (self.depths == 0).all()

    def filter(self, mask):
        """
        Create a FilteredSiteCollection with only a subset of sites
        from this one.

        :param mask:
            Numpy array of boolean values of the same length as this
            filtered sites collection. ``True`` values should indicate
            that site with that index should be included into the
            filtered collection.
        :returns:
            A new :class:`FilteredSiteCollection` instance, unless all the
            values in ``mask`` are ``True``, in which case this site collection
            is returned, or if all the values in ``mask`` are ``False``,
            in which case method returns ``None``. New collection has data
            of only those sites that were marked for inclusion in mask.
        """
        assert len(mask) == len(self), (len(mask), len(self))
        if mask.all():
            return self
        elif not mask.any():
            return None
        indices = self.indices.take(mask.nonzero()[0])
        return FilteredSiteCollection(indices, self.complete)

    def __iter__(self):
        """
        Iterate through all :class:`sites <Site>` in the collection, yielding
        one at a time.
        """
        for i, location in enumerate(self.mesh):
            yield Site(location, self.vs30[i], self.vs30measured[i],
                       self.z1pt0[i], self.z2pt5[i], self.backarc[i])

    def __len__(self):
        """Return the number of filtered sites"""
        return len(self.indices)

    def __toh5__(self):
        n = len(self.complete)
        array = numpy.zeros(n, self.complete.dtype)
        for slot in self.complete._slots_:
            array[slot] = getattr(self.complete, slot)
        attrs = dict(total_sites=n, indices=self.indices)
        return array, attrs

    def __fromh5__(self, array, attrs):
        complete = object.__new__(SiteCollection)
        complete.complete = complete
        complete.total_sites = attrs['total_sites']
        for slot in complete._slots_:
            setattr(complete, slot, array[slot])
        self.indices = attrs['indices']
        self.complete = complete

    def __repr__(self):
        return '<FilteredSiteCollection with %d of %d sites>' % (
            len(self.indices), self.total_sites)


def _extract_site_param(fsc, name):
    # extract the site parameter 'name' from the filtered site collection
    return getattr(fsc.complete, name)[fsc.indices]


# attach a number of properties filtering the arrays
for name in 'vs30 vs30measured z1pt0 z2pt5 backarc lons lats depths \
sids'.split():
    prop = property(
        lambda fsc, name=name: _extract_site_param(fsc, name),
        doc='Extract %s array from FilteredSiteCollection' % name)
    setattr(FilteredSiteCollection, name, prop)
