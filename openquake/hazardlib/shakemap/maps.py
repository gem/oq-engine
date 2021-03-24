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

from openquake.hazardlib import geo, site
from openquake.hazardlib.shakemap.parsers import get_array

F32 = numpy.float32


def get_sitecol_shakemap(uridict, imts, sitecol=None,
                         assoc_dist=None):
    """
    :param uridict: a dictionary specifying the ShakeMap resource
    :param imts: required IMTs as a list of strings
    :param sitecol: SiteCollection used to reduce the shakemap
    :param assoc_dist: association distance
    :returns: filtered site collection, filtered shakemap, discarded
    """
    array = get_array(uridict.pop('kind'), **uridict)
    available_imts = set(array['val'].dtype.names)
    missing = set(imts) - available_imts
    if missing:
        msg = ('The IMT %s is required but not in the available set %s, '
               'please change the risk model otherwise you will have '
               'incorrect zero losses for the associated taxonomies' %
               (missing.pop(), ', '.join(available_imts)))
        raise RuntimeError(msg)

    # build a copy of the ShakeMap with only the relevant IMTs
    dt = [(imt, F32) for imt in sorted(imts)]
    dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
              ('val', dt), ('std', dt)]
    data = numpy.zeros(len(array), dtlist)
    for name in ('lon', 'lat', 'vs30'):
        data[name] = array[name]
    for name in ('val', 'std'):
        for im in imts:
            data[name][im] = array[name][im]

    if sitecol is None:  # extract the sites from the shakemap
        return site.SiteCollection.from_shakemap(data), data, []

    # associate the shakemap to the (filtered) site collection
    bbox = (data['lon'].min(), data['lat'].min(),
            data['lon'].max(), data['lat'].max())
    indices = sitecol.within_bbox(bbox)
    if len(indices) == 0:
        raise RuntimeError('There are no sites within the boundind box %s'
                           % str(bbox))
    sites = sitecol.filtered(indices)
    logging.info('Associating %d GMVs to %d sites', len(data), len(sites))
    return geo.utils.assoc(data, sites, assoc_dist, 'warn')


# Here is the explanation of USGS for the units they are using:
# PGA = peak ground acceleration (percent-g)
# PSA03 = spectral acceleration at 0.3 s period, 5% damping (percent-g)
# PSA10 = spectral acceleration at 1.0 s period, 5% damping (percent-g)
# PSA30 = spectral acceleration at 3.0 s period, 5% damping (percent-g)
# STDPGA = the standard deviation of PGA (natural log of percent-g)
