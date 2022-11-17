#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2022 GEM Foundation
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
from openquake.baselib import sap, parallel
from openquake.hazardlib import contexts, probability_map
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.commonlib import datastore


def classical_task(srcs, sitecol, cmaker, monitor):
    """
    Read the sitecol and call the classical calculator in hazardlib
    """
    cmaker.init_monitoring(monitor)
    rup_indep = getattr(srcs, 'rup_interdep', None) != 'mutex'
    pmap = probability_map.ProbabilityMap(
        sitecol.sids, cmaker.imtls.size, len(cmaker.gsims))
    pmap.fill(rup_indep)
    result = classical(srcs, sitecol, cmaker, pmap)
    result['pnemap'] = pnemap = ~pmap.remove_zeros()
    try:
        pnemap.g = cmaker.gsim_idx
    except AttributeError:  # cmaker does not come from a split
        pass
    return result


def classical_by_gsim(calc_id: int):
    """
    Classical calculator as postprocessor; works only for independent
    sources and ruptures.
    """
    parent = None if calc_id is None else datastore.read(calc_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    with dstore, log:
        oq = dstore.parent['oqparam']
        sitecol = dstore.parent['sitecol']
        N, L = len(sitecol), oq.imtls.size
        cmakers = contexts.read_cmakers(dstore.parent)
        max_gs = max(len(cm.gsims) for cm in cmakers)
        # maximum size of the pmap array in GB
        max_gb = max_gs * L * N * 8 / 1024**3
        if max_gb > oq.pmap_max_gb:  # split in tiles
            max_sites = min(numpy.ceil(N / max_gb * oq.pmap_max_gb),
                            oq.max_sites_per_tile)
            tiles = sitecol.split_max(max_sites)
        else:
            tiles = [sitecol]
        dstore.swmr_on()
        smap = parallel.Starmap(classical_task, h5=dstore)
        csm = dstore['_csm']
        maxw = int(csm.get_max_weight(oq) * max_gs)
        for grp_id, sg in enumerate(csm.src_groups):
            print(grp_id, int(sg.weight), maxw)
            if sg.weight <= maxw:
                logging.info('Sending light group %d', grp_id)
                for tile in tiles:
                    smap.submit((sg, tile, cmakers[grp_id]))
            else:
                logging.info('Sending heavy group %d', grp_id)
                for tile in tiles:
                    for cm in cmakers[grp_id].split_by_gsim():
                        smap.submit((sg, tile, cm))
        for res in smap:
            pass

classical_by_gsim.calc_id = 'parent calculation'

if __name__ == '__main__':
    sap.run(classical_by_gsim)
