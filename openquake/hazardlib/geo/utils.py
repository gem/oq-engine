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
Module :mod:`openquake.hazardlib.geo.utils` contains functions that are common
to several geographical primitives and some other low-level spatial operations.
"""

import math
import logging
import collections

import numpy
import numba
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist, euclidean
from shapely import geometry, contains_xy
from shapely.strtree import STRtree

from openquake.baselib.hdf5 import vstr
from openquake.baselib.performance import compile, split_array
from openquake.hazardlib import geo

U8 = numpy.uint8
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
KM_TO_DEGREES = 0.0089932  # 1 degree == 111 km
DEGREES_TO_RAD = 0.01745329252  # 1 radians = 57.295779513 degrees
EARTH_RADIUS = 6371.0
spherical_to_cartesian = geo.geodetic.spherical_to_cartesian
MAX_EXTENT = 5000  # km, decided by M. Simionato
BASE32 = [ch.encode('ascii') for ch in '0123456789bcdefghjkmnpqrstuvwxyz']
CODE32 = U8([ord(c) for c in '0123456789bcdefghjkmnpqrstuvwxyz'])
SQRT = math.sqrt(2) / 2


def get_dist(array, point):
    """
    :param array: an array of shape (3,) or (N, 3)
    :param point: an array of shape (3)
    :returns: distances(s) from the reference point
    """
    assert len(point.shape) == 1, 'Expected a vector'
    if len(array.shape) == 1:
        return euclidean(array, point)
    return cdist(array, numpy.array([point]))[:, 0]  # shape N


class BBoxError(ValueError):
    """Bounding box too large"""


class PolygonPlotter(object):
    """
    Add polygons to a given axis object
    """
    def __init__(self, ax):
        self.ax = ax
        self.minxs = []
        self.maxxs = []
        self.minys = []
        self.maxys = []

    def add(self, poly, **kw):
        from openquake.hmtk.plotting.patch import PolygonPatch
        minx, miny, maxx, maxy = poly.bounds
        self.minxs.append(minx)
        self.maxxs.append(maxx)
        self.minys.append(miny)
        self.maxys.append(maxy)
        try:
            self.ax.add_patch(PolygonPatch(poly, **kw))
        except ValueError:  # LINESTRING, not POLYGON
            pass

    def set_lim(self, xs=(), ys=()):
        if len(xs):
            self.minxs.append(min(xs))
            self.maxxs.append(max(xs))
        if len(ys):
            self.minys.append(min(ys))
            self.maxys.append(max(ys))
        if self.minxs and self.maxxs:
            self.ax.set_xlim(min(self.minxs), max(self.maxxs))
        if self.minys and self.maxys:
            self.ax.set_ylim(min(self.minys), max(self.maxys))


def angular_distance(km, lat=0, lat2=None):
    """
    Return the angular distance of two points at the given latitude.

    >>> '%.3f' % angular_distance(100, lat=40)
    '1.174'
    >>> '%.3f' % angular_distance(100, lat=80)
    '5.179'
    """
    if lat2 is not None:
        # use the largest latitude to compute the angular distance
        lat = max(abs(lat), abs(lat2))
    return km * KM_TO_DEGREES / math.cos(lat * DEGREES_TO_RAD)


@compile(['(f8[:],f8[:])' ,'(f4[:],f4[:])'])
def angular_mean_weighted(degrees, weights):
    # not using @ to avoid a NumbaPerformanceWarning:
    # '@' is faster on contiguous arrays
    mean_sin, mean_cos = 0., 0.
    for d, w in zip(degrees, weights):
        r = math.radians(d)
        mean_sin += math.sin(r) * w
        mean_cos += math.cos(r) * w
    mean = numpy.arctan2(mean_sin, mean_cos)
    return numpy.degrees(mean)


def angular_mean(degrees, weights=None):
    """
    Given an array of angles in degrees, returns its angular mean.
    If weights are passed, assume sum(weights) == 1.

    >>> angular_mean([179, -179])
    180.0
    >>> angular_mean([-179, 179])
    180.0
    >>> angular_mean([-179, 179], [.75, .25])
    -179.4999619199226
    """
    if len(degrees) == 1:
        return degrees
    elif weights is None:
        rads = numpy.radians(degrees)
        sin = numpy.sin(rads)
        cos = numpy.cos(rads)
        return numpy.degrees(numpy.arctan2(sin.mean(), cos.mean()))
    else:
        ds, ws = numpy.float64(degrees), numpy.float64(weights)
        assert len(ws) == len(ds), (len(ws), len(ds))
        return angular_mean_weighted(ds, ws)


class SiteAssociationError(Exception):
    """Raised when there are no sites close enough"""


class _GeographicObjects(object):
    """
    Store a collection of geographic objects, i.e. objects with lons, lats.
    It is possible to extract the closest object to a given location by
    calling the method .get_closest(lon, lat).
    """
    def __init__(self, objects):
        self.objects = objects
        if hasattr(objects, 'lons'):
            lons = objects.lons
            lats = objects.lats
            depths = objects.depths
        elif isinstance(objects, numpy.ndarray):
            lons = objects['lon']
            lats = objects['lat']
            try:
                depths = objects['depth']
            except ValueError:  # no field of name depth
                depths = numpy.zeros_like(lons)
        else:
            raise TypeError('{} not supported'.format(objects))
        self.kdtree = cKDTree(spherical_to_cartesian(lons, lats, depths))

    def get_closest(self, lon, lat, depth=0):
        """
        Get the closest object to the given longitude and latitude
        and its distance.

        :param lon: longitude in degrees
        :param lat: latitude in degrees
        :param depth: depth in km (default 0)
        :returns: (object, distance)
        """
        xyz = spherical_to_cartesian(lon, lat, depth)
        min_dist, idx = self.kdtree.query(xyz)
        return self.objects[idx], min_dist

    def assoc(self, sitecol, assoc_dist, mode):
        """
        :param sitecol: a (filtered) site collection
        :param assoc_dist: the maximum distance for association
        :param mode: 'strict', 'warn' or 'filter'
        :returns: filtered site collection, filtered objects, discarded
        """
        assert mode in 'strict warn filter', mode
        dic = {}
        discarded = []
        for sid, lon, lat in zip(sitecol.sids, sitecol.lons, sitecol.lats):
            obj, distance = self.get_closest(lon, lat)
            if assoc_dist is None:
                dic[sid] = obj  # associate all
            elif distance <= assoc_dist:
                dic[sid] = obj  # associate within
            elif mode == 'warn':
                dic[sid] = obj  # associate outside
                logging.warning(
                    'The closest vs30 site (%.1f %.1f) is distant more than %d'
                    ' km from site #%d (%.1f %.1f)', obj['lon'], obj['lat'],
                    int(distance), sid, lon, lat)
            elif mode == 'filter':
                discarded.append(obj)
            elif mode == 'strict':
                raise SiteAssociationError(
                    'There is nothing closer than %s km '
                    'to site (%s %s)' % (assoc_dist, lon, lat))
        if not dic:
            raise SiteAssociationError(
                'No sites could be associated within %s km' % assoc_dist)
        sids = sorted(dic)
        return (sitecol.filtered(sids), numpy.array([dic[s] for s in sids]),
                discarded)

    def assoc2(self, exp, assoc_dist, region, mode):
        """
        Associated an exposure to the site collection used
        to instantiate GeographicObjects.

        :param exp: Exposure instance
        :param assoc_dist: the maximum distance for association
        :param mode: 'strict', 'warn' or 'filter'
        :returns: filtered site collection, discarded assets
        """
        assert mode in 'strict filter', mode
        self.objects.filtered  # self.objects must be a SiteCollection
        mesh = exp.mesh
        assets_by_site = split_array(exp.assets, exp.assets['site_id'])
        if region:
            # TODO: use SRTree
            out = []
            for i, (lon, lat) in enumerate(zip(mesh.lons, mesh.lats)):
                if not geometry.Point(lon, lat).within(region):
                    out.append(i)
            if out:
                ok = ~numpy.isin(numpy.arange(len(mesh)), out)
                if ok.sum() == 0:
                    raise RuntimeError(
                        'Could not find any asset within the region!')
                mesh = geo.Mesh(mesh.lons[ok], mesh.lats[ok], mesh.depths[ok])
                assets_by_site = [
                    assets for yes, assets in zip(ok, assets_by_site) if yes]
                logging.info('Discarded %d assets outside the region',
                             len(out))
        asset_dt = numpy.dtype(
            [('asset_ref', vstr), ('lon', F32), ('lat', F32)])
        assets_by_sid = collections.defaultdict(list)
        discarded = []
        objs, distances = self.get_closest(mesh.lons, mesh.lats)
        for obj, distance, assets in zip(objs, distances, assets_by_site):
            if distance <= assoc_dist:
                # keep the assets, otherwise discard them
                assets_by_sid[obj['sids']].extend(assets)
            elif mode == 'strict':
                raise SiteAssociationError(
                    'There is nothing closer than %s km '
                    'to site (%s %s)' % (assoc_dist, obj['lon'], obj['lat']))
            else:
                discarded.extend(assets)
        sids = sorted(assets_by_sid)
        if not sids:
            raise SiteAssociationError(
                'Could not associate any site to any assets within the '
                'asset_hazard_distance of %s km' % assoc_dist)
        data = [(asset['id'], asset['lon'], asset['lat'])
                for asset in discarded]
        discarded = numpy.array(data, asset_dt)
        assets = []
        for sid in sids:
            for ass in assets_by_sid[sid]:
                ass['site_id'] = sid
                assets.append(ass)
        exp.mesh = mesh
        exp.assets = numpy.array(assets, ass.dtype)
        exp.assets['ordinal'] = numpy.arange(len(exp.assets))
        return self.objects.filtered(sids), discarded


def assoc(objects, sitecol, assoc_dist, mode):
    """
    Associate geographic objects to a site collection.

    :param objects:
        something with .lons, .lats or ['lon'] ['lat'], or a list of lists
        of objects with a .location attribute (i.e. assets_by_site)
    :param assoc_dist:
        the maximum distance for association
    :param mode:
        if 'strict' fail if at least one site is not associated
        if 'error' fail if all sites are not associated
    :returns: (filtered site collection, filtered objects, discarded objects)
    """
    return _GeographicObjects(objects).assoc(sitecol, assoc_dist, mode)


ERROR_OUTSIDE = 'The site (%.1f %.1f) is outside of any vs30 area.'


def assoc_to_polygons(polygons, data, sitecol, mode):
    """
    Associate data from a shapefile with polygons to a site collection
    :param polygons: polygon shape data
    :param data: rest of the data belonging to the shapes
    :param sitecol: a (filtered) site collection
    :param mode: 'strict', 'warn' or 'filter'
    :returns: filtered site collection, filtered objects, discarded
    """
    assert mode in 'strict warn filter', mode
    sites = {}
    discarded = []
    tree = STRtree(polygons)
    index_by_id = dict((id(pl), i) for i, pl in enumerate(polygons))

    for sid, lon, lat in zip(sitecol.sids, sitecol.lons, sitecol.lats):
        point = geometry.Point(lon, lat)
        result = next((index_by_id[id(o)]
                       for o in tree.geometries[tree.query(point)]
                       if o.contains(point)), None)
        if result is not None:
            # associate inside
            sites[sid] = data[result].copy()
            # use site coords for further calculation
            sites[sid]['lon'] = lon
            sites[sid]['lat'] = lat
        elif mode == 'strict':
            raise SiteAssociationError(ERROR_OUTSIDE, lon, lat)
        elif mode == 'warn':
            discarded.append((lon, lat))
            logging.warning(ERROR_OUTSIDE, lon, lat)
        elif mode == 'filter':
            discarded.append((lon, lat))

    if not sites:
        raise SiteAssociationError(
            'No sites could be associated within a shape.')

    sorted_sids = sorted(sites)
    discarded = numpy.array(discarded, dtype=[('lon', F32), ('lat', F32)])

    return (sitecol.filtered(sorted_sids),
            numpy.array([sites[s] for s in sorted_sids]), discarded)


def clean_points(points):
    """
    Given a list of points, return a new list with adjacent duplicate points
    removed.

    :param points: a list of Point instances or a list of 3D arrays
    """
    msg = 'At least two distinct points are needed for a line!'
    if not points:
        raise ValueError(msg)

    result = [points[0]]
    isarray = isinstance(points[0], numpy.ndarray)
    for point in points[1:]:
        ok = isarray and (point != result[-1]).any() or point != result[-1]
        if ok:  # different from the previous point
            result.append(point)

    if len(result) < 2:
        raise ValueError(msg)
    return result


def line_intersects_itself(lons, lats, closed_shape=False):
    """
    Return ``True`` if line of points intersects itself.
    Line with the last point repeating the first one considered
    intersecting itself.

    The line is defined by lists (or numpy arrays) of points'
    longitudes and latitudes (depth is not taken into account).

    :param closed_shape:
        If ``True`` the line will be checked twice: first time with
        its original shape and second time with the points sequence
        being shifted by one point (the last point becomes first,
        the first turns second and so on). This is useful for
        checking that the sequence of points defines a valid
        :class:`~openquake.hazardlib.geo.polygon.Polygon`.
    """
    assert len(lons) == len(lats)

    if len(lons) <= 3:
        # line can not intersect itself unless there are
        # at least four points
        return False

    west, east, north, south = get_spherical_bounding_box(lons, lats)
    proj = OrthographicProjection(west, east, north, south)

    xx, yy = proj(lons, lats)
    if not geometry.LineString(list(zip(xx, yy))).is_simple:
        return True

    if closed_shape:
        xx, yy = proj(numpy.roll(lons, 1), numpy.roll(lats, 1))
        if not geometry.LineString(list(zip(xx, yy))).is_simple:
            return True

    return False


@numba.vectorize("(f8,f8)")
def get_longitudinal_extent(lon1, lon2):
    """
    Return the distance between two longitude values as an angular measure.
    Parameters represent two longitude values in degrees.

    :return:
        Float, the angle between ``lon1`` and ``lon2`` in degrees. Value
        is positive if ``lon2`` is on the east from ``lon1`` and negative
        otherwise. Absolute value of the result doesn't exceed 180 for
        valid parameters values.
    """
    return (lon2 - lon1 + 180) % 360 - 180


def check_extent(lons, lats, msg=''):
    """
    :param lons: an array of longitudes (more than one)
    :param lats: an array of latitudes (more than one)
    :params msg: message to display in case of too large extent
    :returns: (dx, dy, dz) in km (rounded)
    """
    l1 = len(lons)
    l2 = len(lats)
    if l1 < 2:
        raise ValueError('%s: not enough lons: %s' % (msg, lons))
    elif l2 < 2:
        raise ValueError('%s: not enough lats: %s' % (msg, lats))
    elif l1 != l2:
        raise ValueError('%s: wrong number of lons, lats: (%d, %d)' %
                         (msg, l1, l2))

    xs, ys, zs = spherical_to_cartesian(lons, lats).T  # (N, 3) -> (3, N)
    dx = xs.max() - xs.min()
    dy = ys.max() - ys.min()
    dz = zs.max() - zs.min()
    # the goal is to forbid sources absurdely large due to wrong coordinates
    if dx > MAX_EXTENT or dy > MAX_EXTENT or dz > MAX_EXTENT:
        raise ValueError('%s: too large: %d km' % (msg, max(dx, dy, dz)))
    return int(dx), int(dy), int(dz)


def get_bbox(lons, lats, xlons=(), xlats=()):
    """
    :returns: (minlon, minlat, maxlon, maxlat)
    """
    assert len(lons) == len(lats)
    assert len(xlons) == len(xlats)
    arr = numpy.empty(len(lons) + len(xlons), [('lon', float), ('lat', float)])
    if len(xlons):
        arr['lon'] = numpy.concatenate([lons, xlons])
    else:
        arr['lon'] = lons
    if len(xlats):
        arr['lat'] = numpy.concatenate([lats, xlats])
    else:
        arr['lat'] = lats
    return get_bounding_box(arr, 0)


def get_bounding_box(obj, maxdist):
    """
    Return the dilated bounding box of a geometric object.

    :param obj:
        an object with method .get_bounding_box, or with an attribute .polygon
        or a list of locations
    :param maxdist: maximum distance in km
    :returns: (minlon, minlat, maxlon, maxlat)
    """
    if hasattr(obj, 'get_bounding_box'):
        return obj.get_bounding_box(maxdist)
    elif hasattr(obj, 'polygon'):
        bbox = obj.polygon.get_bbox()
    else:
        if isinstance(obj, list):  # a list of locations
            lons = numpy.array([loc.longitude for loc in obj])
            lats = numpy.array([loc.latitude for loc in obj])
        else:  # assume an array with fields lon, lat
            lons, lats = obj['lon'], obj['lat']
        min_lon, max_lon = lons.min(), lons.max()
        if cross_idl(min_lon, max_lon):
            lons %= 360
        bbox = lons.min(), lats.min(), lons.max(), lats.max()
    a1 = min(maxdist * KM_TO_DEGREES, 90)
    a2 = angular_distance(maxdist, bbox[1], bbox[3])
    delta = bbox[2] - bbox[0] + 2 * a2
    if delta > 180:
        raise BBoxError('The buffer of %d km is too large, the bounding '
                        'box is larger than half the globe: %d degrees' %
                        (maxdist, delta))
    return bbox[0] - a2, bbox[1] - a1, bbox[2] + a2, bbox[3] + a1


# NB: returns (west, east, north, south) which is DIFFERENT from
# get_bounding_box return (west, south, east, north)
@compile(["(f8[:],f8[:])", "(f4[:],f4[:])"])
def get_spherical_bounding_box(lons, lats):
    """
    Given a collection of points find and return the bounding box,
    as a pair of longitudes and a pair of latitudes.

    Parameters define longitudes and latitudes of a point collection
    respectively in a form of lists or numpy arrays.

    :return:
        A tuple of four items. These items represent western, eastern,
        northern and southern borders of the bounding box respectively.
        Values are floats in decimal degrees.
    :raises ValueError:
        If points collection has the longitudinal extent of more than
        180 degrees (it is impossible to define a single hemisphere
        bound to poles that would contain the whole collection).
    """
    ok = numpy.isfinite(lons)
    if not ok.all():
        lons = lons[ok]
        lats = lats[ok]

    north, south = lats.max(), lats.min()
    west, east = lons.min(), lons.max()
    if get_longitudinal_extent(west, east) < 0:
        # points are lying on both sides of the international date line
        # (meridian 180). the actual west longitude is the lowest positive
        # longitude and east one is the highest negative.
        west = lons[lons > 0].min()
        east = lons[lons < 0].max()
        ext0 = get_longitudinal_extent(west, lons)
        ext1 = get_longitudinal_extent(lons, east)
        if not ((ext0 >= 0) & (ext1 >= 0)).all():
            raise ValueError('points collection has longitudinal extent '
                             'wider than 180 degrees')
    return west, east, north, south


@compile(['(f8,f8,f8[:],f8[:])', '(f8,f8,f4[:],f4[:])'])
def project_reverse(lambda0, phi0, lons, lats):
    sin_phi0, cos_phi0 = math.sin(phi0), math.cos(phi0)
    # "reverse" mode, arguments are actually abscissae
    # and ordinates in 2d space
    xx, yy = lons / EARTH_RADIUS, lats / EARTH_RADIUS
    cos_c = numpy.sqrt(1. - (xx ** 2 + yy ** 2))
    phis = numpy.arcsin(cos_c * sin_phi0 + yy * cos_phi0)
    lambdas = numpy.arctan2(xx, cos_phi0 * cos_c - yy * sin_phi0)
    xx = numpy.degrees(lambda0 + lambdas)
    yy = numpy.degrees(phis)
    # shift longitudes greater than 180 back into the western
    # hemisphere, that is in range [0, -180], and longitudes
    # smaller than -180, to the heastern emisphere [0, 180]
    idx = xx >= 180.
    xx[idx] = xx[idx] - 360.
    idx = xx <= -180.
    xx[idx] = xx[idx] + 360.
    return xx, yy


@compile(['(f8,f8,f8,f8)', '(f8,f8,f8[:],f8[:])', '(f8,f8,f8[:,:],f8[:,:])',
          '(f8,f8,f4,f4)', '(f8,f8,f4[:],f4[:])', '(f8,f8,f4[:,:],f4[:,:])'])
def project_direct(lambda0, phi0, lons, lats):
    lambdas, phis = numpy.radians(lons), numpy.radians(lats)
    cos_phis = numpy.cos(phis)
    cos_phi0 = math.cos(phi0)
    lambdas -= lambda0
    xx = numpy.cos(phis) * numpy.sin(lambdas) * EARTH_RADIUS
    yy = (cos_phi0 * numpy.sin(phis) - math.sin(phi0) * cos_phis
          * numpy.cos(lambdas)) * EARTH_RADIUS
    return xx, yy


class OrthographicProjection(object):
    """
    Callable OrthographicProjection object that can perform both forward
    and reverse projection (converting from longitudes and latitudes to x
    and y values on 2d-space and vice versa). The call takes three
    arguments: first two are numpy arrays of longitudes and latitudes *or*
    abscissae and ordinates of points to project and the third one
    is a boolean that allows to choose what operation is requested --
    is it forward or reverse one. ``True`` value given to third
    positional argument (or keyword argument "reverse") indicates
    that the projection of points in 2d space back to earth surface
    is needed. The default value for "reverse" argument is ``False``,
    which means forward projection (degrees to kilometers).

    Raises ``ValueError`` in forward projection
    mode if any of the target points is further than 90 degree
    (along the great circle arc) from the projection center.

    Parameters are given as floats, representing decimal degrees (first two
    are longitudes and last two are latitudes). They define a bounding box
    in a spherical coordinates of the collection of points that is about
    to be projected. The center point of the projection (coordinates (0, 0)
    in Cartesian space) is set to the middle point of that bounding box.
    The resulting projection is defined for spherical coordinates that are
    not further from the bounding box center than 90 degree on the great
    circle arc.

    The result projection is of type `Orthographic
    <http://mathworld.wolfram.com/OrthographicProjection.html>`_.
    This projection is prone to distance, area and angle distortions
    everywhere outside of the center point, but still can be used for
    checking shapes: verifying if line intersects itself (like in
    :func:`line_intersects_itself`) or if point is inside of a polygon
    (like in :meth:`openquake.hazardlib.geo.polygon.Polygon.discretize`). It
    can be also used for measuring distance to an extent of around 700
    kilometers (error doesn't exceed 1 km up until then).
    """
    @classmethod
    def from_(cls, lons, lats):
        idx = numpy.isfinite(lons)
        return cls(*get_spherical_bounding_box(lons[idx], lats[idx]))

    def __init__(self, west, east, north, south):
        self.west = west
        self.east = east
        self.north = north
        self.south = south
        self.lam0, self.phi0 = numpy.radians(
            get_middle_point(west, north, east, south))

    def __call__(self, lons, lats, deps=None, reverse=False):
        if reverse:
            xx, yy = project_reverse(self.lam0, self.phi0, lons, lats)
        else:  # fast lane
            xx, yy = project_direct(self.lam0, self.phi0, lons, lats)
        if deps is None:
            return numpy.array([xx, yy])
        else:
            return numpy.array([xx, yy, deps])


def get_middle_point(lon1, lat1, lon2, lat2):
    """
    Given two points return the point exactly in the middle lying on the same
    great circle arc.

    Parameters are point coordinates in degrees.

    :returns:
        Tuple of longitude and latitude of the point in the middle.
    """
    if lon1 == lon2 and lat1 == lat2:
        return lon1, lat1
    dist = geo.geodetic.geodetic_distance(lon1, lat1, lon2, lat2)
    azimuth = geo.geodetic.azimuth(lon1, lat1, lon2, lat2)
    return geo.geodetic.point_at(lon1, lat1, azimuth, dist / 2.0)


@compile("f8[:,:](f8[:,:])")
def cartesian_to_spherical(arrayN3):
    """
    Return the spherical coordinates for coordinates in Cartesian space.

    This function does an opposite to :func:`spherical_to_cartesian`.

    :param arrayN3:
        Array of cartesian coordinates of shape (N, 3)
    :returns:
        Array of shape (3, N) representing longitude (decimal degrees),
        latitude (decimal degrees) and depth (km) in specified order.
    """
    out = numpy.zeros_like(arrayN3)
    rr = numpy.sqrt(numpy.sum(arrayN3 * arrayN3, axis=-1))
    xx, yy, zz = arrayN3.T
    out[:, 0] = numpy.degrees(numpy.arctan2(yy, xx))
    out[:, 1] = numpy.degrees(numpy.arcsin(numpy.clip(zz / rr, -1., 1.)))
    out[:, 2] = EARTH_RADIUS - rr
    return out.T  # shape (3, N)


@compile("f8(f8[:], f8[:, :])")
def min_distance(xyz, xyzs):
    """
    :param xyz: an array of shape (3,)
    :param xyzs: an array of shape (N, 3)
    :returns: the minimum euclidean distance between the point and the points
    """
    x, y, z = xyz
    xs, ys, zs = xyzs.T
    d2 = (xs-x)**2 + (ys-y)**2 + (zs-z)**2
    return math.sqrt(d2.min())


def triangle_area(e1, e2, e3):
    """
    Get the area of triangle formed by three vectors.

    Parameters are three three-dimensional numpy arrays representing
    vectors of triangle's edges in Cartesian space.

    :returns:
        Float number, the area of the triangle in squared units of coordinates,
        or numpy array of shape of edges with one dimension less.

    Uses Heron formula, see http://mathworld.wolfram.com/HeronsFormula.html.
    """
    # calculating edges length
    e1_length = numpy.sqrt(numpy.sum(e1 * e1, axis=-1))
    e2_length = numpy.sqrt(numpy.sum(e2 * e2, axis=-1))
    e3_length = numpy.sqrt(numpy.sum(e3 * e3, axis=-1))
    # calculating half perimeter
    s = (e1_length + e2_length + e3_length) / 2.0
    # applying Heron's formula
    return numpy.sqrt(s * (s - e1_length) * (s - e2_length) * (s - e3_length))


def normalized(vector):
    """
    Get unit vector for a given one.

    :param vector:
        Numpy vector as coordinates in Cartesian space, or an array of such.
    :returns:
        Numpy array of the same shape and structure where all vectors are
        normalized. That is, each coordinate component is divided by its
        vector's length.
    """
    length = numpy.sum(vector * vector, axis=-1)
    length = numpy.sqrt(length.reshape(length.shape + (1, )))
    return vector / length


def point_to_polygon_distance(polygon, pxx, pyy):
    """
    Calculate the distance to polygon for each point of the collection
    on the 2d Cartesian plane.

    :param polygon:
        Shapely "Polygon" geometry object.
    :param pxx:
        List or numpy array of abscissae values of points to calculate
        the distance from.
    :param pyy:
        Same structure as ``pxx``, but with ordinate values.
    :returns:
        Numpy array of distances in units of coordinate system. Points
        that lie inside the polygon have zero distance.
    """
    pxx = numpy.array(pxx)
    pyy = numpy.array(pyy)
    assert pxx.shape == pyy.shape
    if pxx.ndim == 0:
        pxx = pxx.reshape((1, ))
        pyy = pyy.reshape((1, ))
    result = numpy.array([
        polygon.distance(geometry.Point(pxx.item(i), pyy.item(i)))
        for i in range(pxx.size)
    ])
    return result.reshape(pxx.shape)


def fix_lon(lon):
    """
    :returns: a valid longitude in the range -180 <= lon < 180

    >>> fix_lon(11)
    11
    >>> fix_lon(181)
    -179
    >>> fix_lon(-182)
    178
    """
    return (lon + 180) % 360 - 180


def cross_idl(lon1, lon2, *lons):
    """
    Return True if two longitude values define line crossing international date
    line.

    >>> cross_idl(-45, 45)
    False
    >>> cross_idl(-180, -179)
    False
    >>> cross_idl(180, 179)
    False
    >>> cross_idl(45, -45)
    False
    >>> cross_idl(0, 0)
    False
    >>> cross_idl(-170, 170)
    True
    >>> cross_idl(170, -170)
    True
    >>> cross_idl(-180, 180)
    True
    """
    lons = (lon1, lon2) + lons
    l1, l2 = min(lons), max(lons)
    # a line crosses the international date line if the end positions
    # have different sign and they are more than 180 degrees longitude apart
    return l1 * l2 < 0 and abs(l1 - l2) > 180


def plane_fit(points):
    """
    This fits an n-dimensional plane to a set of points. See
    http://stackoverflow.com/questions/12299540/plane-fitting-to-4-or-more-xyz-points

    :parameter points:
        An instance of :class:~numpy.ndarray. The number of columns must be
        equal to three.
    :return:
         A point on the plane and the normal to the plane.
    """
    points = numpy.transpose(points)
    points = numpy.reshape(points, (numpy.shape(points)[0], -1))
    assert points.shape[0] < points.shape[1], points.shape
    ctr = points.mean(axis=1)
    x = points - ctr[:, None]
    M = numpy.dot(x, x.T)
    return ctr, numpy.linalg.svd(M)[0][:, -1]


def bbox2poly(bbox):
    """
    :param bbox: a geographic bounding box West-East-North-South
    :returns: a list of pairs corrisponding to the bbox polygon
    """
    x1, x2, y2, y1 = bbox  # west, east, north, south
    return (x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)


# geohash code adapted from Leonard Norrgard's implementation
# https://github.com/vinsci/geohash/blob/master/Geohash/geohash.py
# see also https://en.wikipedia.org/wiki/Geohash
# length 6 = .61 km  resolution, length 5 = 2.4 km resolution,
# length 4 = 20 km, length 3 = 78 km
# used in SiteCollection.geohash
@compile(['(f8[:],f8[:],u1)', '(f4[:],f4[:],u1)'])
def geohash(lons, lats, length):
    """
    Encode a position given in lon, lat into a geohash of the given lenght

    >>> arr = CODE32[geohash(F64([10., 10.]), F64([45., 46.]), length=5)]
    >>> [row.tobytes() for row in arr]
    [b'spzpg', b'u0pje']
    """
    l1 = len(lons)
    l2 = len(lats)
    if l1 != l2:
        raise ValueError('lons, lats of different lenghts')
    chars = numpy.zeros((l1, length), U8)
    for p in range(l1):
        lon = lons[p]
        lat = lats[p]
        lat_interval = [-90.0, 90.0]
        lon_interval = [-180.0, 180.0]
        bits = [16, 8, 4, 2, 1]
        bit = 0
        ch = 0
        even = True
        i = 0
        while i < length:
            if even:
                mid = (lon_interval[0] + lon_interval[1]) / 2
                if lon > mid:
                    ch |= bits[bit]
                    lon_interval[:] = [mid, lon_interval[1]]
                else:
                    lon_interval[:] = [lon_interval[0], mid]
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2
                if lat > mid:
                    ch |= bits[bit]
                    lat_interval[:] = [mid, lat_interval[1]]
                else:
                    lat_interval[:] = [lat_interval[0], mid]
            even = not even
            if bit < 4:
                bit += 1
            else:
                chars[p, i] = ch
                bit = 0
                ch = 0
                i += 1
    return chars


# corresponds to blocks of 2.4 km
def geohash5(coords):
    """
    :returns: a geohash of length 5*len(points) as a string

    >>> coords = numpy.array([[10., 45.], [11., 45.]])
    >>> geohash5(coords)
    'spzpg_spzzf'
    """
    arr = CODE32[geohash(coords[:, 0], coords[:, 1], 5)]
    return b'_'.join(row.tobytes() for row in arr).decode('ascii')


# corresponds to blocks of 78 km
def geohash3(lons, lats):
    """
    :returns: a geohash of length 3 as a 16 bit integer

    >>> geohash3(F64([10., 10.]), F64([45., 46.]))
    array([24767, 26645], dtype=uint16)
    """
    arr = geohash(lons, lats, 3)
    return arr[:, 0] * 1024 + arr[:, 1] * 32 + arr[:, 2]


def geolocate(lonlats, geom_df, exclude=()):
    """
    :param lonlats: array of shape (N, 2) of (lon, lat)
    :param geom_df: DataFrame of geometries with a "code" field
    :param exclude: List of codes to exclude from the results
    :returns: codes associated to the points

    NB: if the "code" field is not a primary key, i.e. there are
    different geometries with the same code, performs an "or", i.e.
    associates the code if at least one of the geometries matches
    """
    codes = numpy.array(['???'] * len(lonlats))
    filtered_geom_df = geom_df[~geom_df['code'].isin(exclude)]
    for code, df in filtered_geom_df.groupby('code'):
        ok = numpy.zeros(len(lonlats), bool)
        for geom in df.geom:
            ok |= contains_xy(geom, lonlats)
        codes[ok] = code
    return codes


def geolocate_geometries(geometries, geom_df, exclude=()):
    """
    :param geometries: NumPy array of Shapely geometries to check
    :param geom_df: DataFrame of geometries with a "code" field
    :param exclude: List of codes to exclude from the results
    :returns: NumPy array where each element contains a list of codes
        of geometries that intersect each input geometry
    """
    result_codes = numpy.empty(len(geometries), dtype=object)
    filtered_geom_df = geom_df[~geom_df['code'].isin(exclude)]
    for i, input_geom in enumerate(geometries):
        intersecting_codes = set()  # to store intersecting codes for current geometry
        for code, df in filtered_geom_df.groupby('code'):
            target_geoms = df['geom'].values  # geometries associated with this code
            if any(target_geom.intersects(input_geom) for target_geom in target_geoms):
                intersecting_codes.add(code)
        result_codes[i] = sorted(intersecting_codes)
    return result_codes
