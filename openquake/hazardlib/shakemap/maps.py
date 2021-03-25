# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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

import logging
import numpy

from openquake.baselib.general import CallableDict
from openquake.hazardlib import geo, site
from openquake.hazardlib.shakemap.parsers import get_array

F32 = numpy.float32

# Here is the explanation of USGS for the units they are using:
# PGA = peak ground acceleration (percent-g)
# PSA03 = spectral acceleration at 0.3 s period, 5% damping (percent-g)
# PSA10 = spectral acceleration at 1.0 s period, 5% damping (percent-g)
# PSA30 = spectral acceleration at 3.0 s period, 5% damping (percent-g)
# STDPGA = the standard deviation of PGA (natural log of percent-g)


def get_sitecol_shakemap(uridict, required_imts, sitecol=None,
                         assoc_dist=None, mode='warn'):
    """
    :param uridict: a dictionary specifying the ShakeMap resource
    :param imts: required IMTs as a list of strings
    :param sitecol: SiteCollection used to reduce the shakemap
    :param assoc_dist: the maximum distance for association
    :param mode: 'strict', 'warn' or 'filter'
    :returns: filtered site collection, filtered shakemap, discarded
    """
    kind = uridict.pop('kind')
    array = get_array(kind, **uridict)

    imts, bbox, shakemap = \
        read_shakemap(kind, required_imts, array)

    missing = set(required_imts) - imts
    if missing:
        msg = ('The IMT %s is required but not in the available set %s, '
               'please change the risk model otherwise you will have '
               'incorrect zero losses for the associated taxonomies' %
               (missing.pop(), ', '.join(imts)))
        raise RuntimeError(msg)

    if sitecol is None:  # extract the sites from the shakemap
        return create_site_collection(kind, shakemap), shakemap, []

    indices = sitecol.within_bbox(bbox)

    if len(indices) == 0:
        raise RuntimeError('There are no sites within '
                           'the bounding box %s' % str(bbox))
    sitecol = sitecol.filtered(indices)
    logging.info('Associating %d GMVs to %d sites',
                 len(shakemap), len(sitecol))

    return associate_to_usgs_shakemap(
        kind, shakemap, sitecol, assoc_dist, mode)


# read and filter parsed shakemap depending on type
read_shakemap = CallableDict()


@read_shakemap.add('usgs_xml', 'usgs_id', 'file_npy')
def read_shakemap_usgs(kind, imts, shakemap):
    available_imts = set(shakemap['val'].dtype.names)

    bbox = (shakemap['lon'].min(), shakemap['lat'].min(),
            shakemap['lon'].max(), shakemap['lat'].max())

    # build a copy of the ShakeMap with only the relevant IMTs
    dt = [(imt, F32) for imt in sorted(imts)]
    dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
              ('val', dt), ('std', dt)]
    data = numpy.zeros(len(shakemap), dtlist)
    for name in ('lon', 'lat', 'vs30'):
        data[name] = shakemap[name]
    for name in ('val', 'std'):
        for im in imts:
            data[name][im] = shakemap[name][im]

    return available_imts, bbox, data


# if no site collection was passed generate one from the shakemap
create_site_collection = CallableDict()


@create_site_collection.add('usgs_xml')
def from_usgs_shakemap(kind, shakemap):
    return site.SiteCollection.from_usgs_shakemap(shakemap)


# associate shakemap to site collection
associate_sites = CallableDict()


@associate_sites.add('usgs_xml')
def associate_to_usgs_shakemap(kind, shakemap, sitecol, assoc_dist, mode):
    return geo.utils.assoc(shakemap, sitecol, assoc_dist, mode)
