# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy

from openquake.baselib.general import CallableDict
from openquake.hazardlib import geo, site
from openquake.hazardlib.shakemap.parsers import get_array

F32 = numpy.float32

get_sitecol_shakemap = CallableDict(keyfunc=lambda dic: dic['kind'])


@get_sitecol_shakemap.add('shapefile')
def get_sitecol_shapefile(uridict, required_imts, sitecol=None,
                          assoc_dist=None, mode='filter'):
    """
    :param uridict: a dictionary specifying the ShakeMap resource
    :param imts: required IMTs as a list of strings
    :param sitecol: SiteCollection used to reduce the shakemap
    :param assoc_dist: unused for shapefiles
    :param mode: 'strict', 'warn' or 'filter'
    :returns: filtered site collection, filtered shakemap, discarded
    """
    polygons, shakemap = get_array(**uridict)

    available_imts = set(shakemap['val'].dtype.names)

    check_required_imts(required_imts, available_imts)

    # build a copy of the ShakeMap with only the relevant IMTs
    shakemap = filter_unused_imts(
        shakemap, required_imts, site_fields=['vs30'])

    if sitecol is None:
        # use centroids of polygons to generate sitecol
        centroids = numpy.array([tuple(*p.centroid.coords)
                                 for p in polygons],
                                dtype=[('lon', numpy.float32),
                                       ('lat', numpy.float32)])
        for name in ('lon', 'lat'):
            shakemap[name] = centroids[name]
        return site.SiteCollection.from_usgs_shakemap(shakemap), shakemap, []

    return geo.utils.assoc_to_polygons(polygons, shakemap, sitecol, mode)


@get_sitecol_shakemap.add('usgs_xml', 'usgs_id', 'file_npy')
def get_sitecol_usgs(uridict, required_imts, sitecol=None,
                     assoc_dist=None, mode='warn'):
    """
    :param uridict: a dictionary specifying the ShakeMap resource
    :param imts: required IMTs as a list of strings
    :param sitecol: SiteCollection used to reduce the shakemap
    :param assoc_dist: the maximum distance for association
    :param mode: 'strict', 'warn' or 'filter'
    :returns: filtered site collection, filtered shakemap, discarded
    """
    shakemap = get_array(**uridict)

    available_imts = set(shakemap['val'].dtype.names)

    check_required_imts(required_imts, available_imts)

    # build a copy of the ShakeMap with only the relevant IMTs
    shakemap = filter_unused_imts(shakemap, required_imts)

    if sitecol is None:
        return site.SiteCollection.from_usgs_shakemap(shakemap), shakemap, []

    return geo.utils.assoc(shakemap, sitecol, assoc_dist, mode)


def filter_unused_imts(shakemap, required_imts,
                       site_fields=('lon', 'lat', 'vs30')):
    """
    build a copy of the ShakeMap with only the relevant IMTs

    :param shakemap: shakemap array which should be filtered
    :param required_imts: imts to keep in shakemap array
    :param site_fields: single columns which are copied over
    """
    if 'SA(0.6)' in required_imts and (shakemap['val']['SA(0.6)'] == 0).all():
        raise ValueError('The downloaded ShakeMap is missing SA(0.6)!')

    dt = [(imt, F32) for imt in sorted(required_imts)]
    dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
              ('val', dt), ('std', dt)]
    data = numpy.zeros(len(shakemap), dtlist)
    for name in site_fields:
        data[name] = shakemap[name]
    for name in ('val', 'std'):
        for im in required_imts:
            data[name][im] = shakemap[name][im]
    return data


def check_required_imts(required_imts, available_imts):
    """
    Check if the list of required imts is present in the list of available imts

    :param required_imts: list of strings of required imts
    :param available_imts: set of available imts
    :raises RuntimeError: if required imts are not present
    """
    missing = set(required_imts) - available_imts
    if missing:
        msg = ('The IMT %s is required but not in the available set %s, '
               'please change the risk model otherwise you will have '
               'incorrect zero losses for the associated taxonomy strings' %
               (missing.pop(), ', '.join(available_imts)))
        raise RuntimeError(msg)


def apply_bounding_box(sitecol, bbox):
    """
    Filter out sites which are not in the bounding box.

    :param sitecol: SiteCollection of sites from exposed assets
    :param bbox: Bounding Box (lon.min, lat.min, lon.max, lat.max)
    :raises RuntimeError: if no sites are found within the Bounding Box
    """
    indices = sitecol.within_bbox(bbox)

    if len(indices) == 0:
        raise RuntimeError('There are no sites within '
                           'the bounding box %s' % str(bbox))
    return sitecol.filtered(indices)
