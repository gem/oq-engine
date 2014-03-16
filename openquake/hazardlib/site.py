# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module :mod:`openquake.hazardlib.site` defines :class:`Site`.
"""
import numpy

from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.slots import with_slots


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
    :param id:
        Optional parameter with default 0. If given, it should be an
        integer identifying the site univocally.

    :raises ValueError:
        If any of ``vs30``, ``z1pt0`` or ``z2pt5`` is zero or negative.

    .. note::

        :class:`Sites <Site>` are pickleable
    """
    __slots__ = 'location vs30 vs30measured z1pt0 z2pt5 id'.split()

    def __init__(self, location, vs30, vs30measured, z1pt0, z2pt5, id=0):
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
        self.id = id

    def __str__(self):
        """
        >>> import openquake.hazardlib
        >>> loc = openquake.hazardlib.geo.point.Point(1, 2, 3)
        >>> str(Site(loc, 760.0, True, 100.0, 5.0))
        '<Location=<Latitude=2.000000, Longitude=1.000000, Depth=3.0000>, \
Vs30=760.0000, Vs30Measured=True, Depth1.0km=100.0000, Depth2.5km=5.0000>'
        """
        return (
            "<Location=%s, Vs30=%.4f, Vs30Measured=%r, Depth1.0km=%.4f, "
            "Depth2.5km=%.4f>") % (
            self.location, self.vs30, self.vs30measured, self.z1pt0,
            self.z2pt5)

    def __repr__(self):
        """
        >>> import openquake.hazardlib
        >>> loc = openquake.hazardlib.geo.point.Point(1, 2, 3)
        >>> site = Site(loc, 760.0, True, 100.0, 5.0)
        >>> str(site) == repr(site)
        True
        """
        return self.__str__()


class SiteCollection(object):
    """
    A collection of :class:`sites <Site>`.

    Instances of this class are intended to represent a large collection
    of sites in a most efficient way in terms of memory usage.

    .. note::

        Because calculations assume that :class:`Sites <Site>` are on the
        Earth's surface, all `depth` information in a :class:`SiteCollection`
        is discarded. The collection `mesh` will only contain lon and lat. So
        even if a :class:`SiteCollection` is created from sites containing
        `depth` in their geometry, iterating over the collection will yield
        :class:`Sites <Site>` with a reference depth of 0.0.

    :param sites:
        A list of instances of :class:`Site` class.
    """
    def __init__(self, sites):
        self.indices = None
        self.total_sites = len(sites)
        self.vs30 = zeros = numpy.zeros(len(sites))
        self.vs30measured = numpy.zeros(len(sites), dtype=bool)
        self.z1pt0 = zeros.copy()
        self.z2pt5 = zeros.copy()
        self.sid = numpy.zeros(len(sites), dtype=int)
        lons = zeros.copy()
        lats = zeros.copy()

        for i in xrange(len(sites)):
            self.vs30[i] = sites[i].vs30
            self.vs30measured[i] = sites[i].vs30measured
            self.z1pt0[i] = sites[i].z1pt0
            self.z2pt5[i] = sites[i].z2pt5
            self.sid[i] = sites[i].id
            lons[i] = sites[i].location.longitude
            lats[i] = sites[i].location.latitude

        self.mesh = Mesh(lons, lats, depths=None)

        # protect arrays from being accidentally changed. it is useful
        # because we pass these arrays directly to a GMPE through
        # a SiteContext object and if a GMPE is implemented poorly it could
        # modify the site values, thereby corrupting site and all the
        # subsequent calculation. note that this doesn't protect arrays from
        # being changed by calling itemset()
        for arr in (self.vs30, self.vs30measured, self.z1pt0, self.z2pt5,
                    self.sid, self.mesh.lons, self.mesh.lats):
            arr.flags.writeable = False

    def __iter__(self):
        """
        Iterate through all :class:`sites <Site>` in the collection, yielding
        one at a time.
        """
        for i, location in enumerate(self.mesh):
            yield Site(location, self.vs30[i], self.vs30measured[i],
                       self.z1pt0[i], self.z2pt5[i], self.sid[i])

    def expand(self, data, placeholder):
        """
        Expand a short array `data` over a filtered site collection of the
        same length and return a long array of size `total_sites` filled
        with the placeholder.

        The typical workflow is the following: there is a whole site
        collection, the one that has an information about all the sites.
        Then it gets filtered for performing some calculation on a limited
        set of sites (like for instance filtering sites by their proximity
        to a rupture). That filtering process can be repeated arbitrary
        number of times, i.e. a collection that is already filtered can
        be filtered for further limiting the set of sites to compute on.
        Then the (supposedly expensive) computation is done on a limited
        set of sites which still appears as just a :class:`SiteCollection`
        instance, so that computation code doesn't need to worry about
        filtering, it just needs to handle site collection objects. The
        calculation result comes in a form of 1d or 2d numpy array (that
        is, either one value per site or one 1d array per site) with length
        equal to number of sites in a filtered collection. That result
        needs to be expanded to an array of similar structure but the one
        that holds values for all the sites in the original (unfiltered)
        collection. This is what :meth:`expand` is for. It creates a result
        array of ``total_sites`` length and puts values from ``data`` into
        appropriate places in it remembering indices of sites that were
        chosen for actual calculation and leaving ``placeholder`` value
        everywhere else.

        :param data:
            1d or 2d numpy array with first dimension representing values
            computed for site from this collection.
        :param placeholder:
            A scalar value to be put in result array for those sites that
            were filtered out and no real calculation was performed for them.
        :returns:
            Array of length ``total_sites`` with values from ``data``
            distributed in the appropriate places.
        """
        len_data = data.shape[0]
        assert len_data == len(self), (len_data, len(self))

        if self.indices is None:
            # nothing to expand: this sites collection was not filtered
            return data

        assert len_data <= self.total_sites
        assert self.indices[-1] < self.total_sites, (
            self.indices[-1], self.total_sites)

        if data.ndim == 1:
            # single-dimensional array
            result = numpy.empty(self.total_sites)
            result.fill(placeholder)
            result.put(self.indices, data)
            return result

        assert data.ndim == 2
        # two-dimensional array
        num_values = data.shape[1]
        result = numpy.empty((self.total_sites, num_values))
        result.fill(placeholder)
        for i in xrange(num_values):
            result[:, i].put(self.indices, data[:, i])
        return result

    def filter(self, mask):
        """
        Create a new collection with only a subset of sites from this one.

        :param mask:
            Numpy array of boolean values of the same length as this sites
            collection. ``True`` values should indicate that site with that
            index should be included into the filtered collection.
        :returns:
            A new :class:`SiteCollection` instance, unless all the values
            in ``mask`` are ``True``, in which case this site collection
            is returned, or if all the values in ``mask`` are ``False``,
            in which case method returns ``None``. New collection has data
            of only those sites that were marked for inclusion in mask.

        See also :meth:`expand`.
        """
        assert len(mask) == len(self)
        if mask.all():
            # all sites satisfy the filter, return
            # this collection unchanged
            return self
        if not mask.any():
            # no sites pass the filter, return None
            return None
        col = object.__new__(self.__class__)
        col.total_sites = self.total_sites  # preserve the number of sites
        # extract indices of Trues from the mask
        [indices] = mask.nonzero()
        # take only needed values from this collection
        # to a new one
        col.vs30 = self.vs30.take(indices)
        col.vs30measured = self.vs30measured.take(indices)
        col.z1pt0 = self.z1pt0.take(indices)
        col.z2pt5 = self.z2pt5.take(indices)
        col.sid = self.sid.take(indices)
        col.mesh = Mesh(self.mesh.lons.take(indices),
                        self.mesh.lats.take(indices),
                        depths=None)
        if self.indices is not None:
            # if this collection was already a subset of some other
            # collection (a result of :meth:`filter` itself) than mask's
            # indices represent values in a filtered collection, but
            # we need to keep track of original indices in the whole
            # (unfiltered) collection. here we save original indices
            # of sites in this double- (or more times) filtered
            # collection
            col.indices = self.indices.take(indices)
        else:
            col.indices = indices
        # do the same as in the constructor
        for arr in (col.vs30, col.vs30measured, col.z1pt0, col.z2pt5,
                    col.sid, col.mesh.lons, col.mesh.lats):
            arr.flags.writeable = False
        return col

    def __len__(self):
        """
        Return a number of sites in a collection.
        """
        return len(self.mesh)
