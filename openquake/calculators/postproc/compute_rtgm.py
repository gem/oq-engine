# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
from openquake.baselib import parallel


def get_hazdic(hcurves, imtls, invtime, sitecol):
    """
    Convert an array of mean hazard curves into a dictionary suitable
    for the rtgmpy library

    :param hcurves: array of PoEs of shape (N, M, L1)
    """
    [site] = sitecol
    hazdic = {
        'site': {'name': 'site',
                 'lon': site.location.x,
                 'lat': site.location.y,
                 'Vs30': site.vs30},
        'hazCurves': {imt: {'iml': imtls[imt],
                            'afe': -numpy.log(1-hcurves[0, m]) / invtime}
                      for m, imt in enumerate(imtls)}}
    return hazdic


def main(dstore):
    """
    :param dstore: datastore with the classical calculation
    """
    try:
        import rtgmpy
    except ImportError:
        logging.warning('Missing module rtgmpy: skipping AELO calculation')
    logging.info('Computing Risk Targeted Ground Motion')
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    full_lt = dstore['full_lt'].init()
    assert list(oq.hazard_stats()) == ['mean'], oq.hazard_stats()
    L1 = oq.imtls.size // len(oq.imtls)
    hcurves = dstore['hcurves-stats'][:, :, :, 0]  # shape NML1
    print(get_hazdic(hcurves, oq.imtls, oq.investigation_time, sitecol))
