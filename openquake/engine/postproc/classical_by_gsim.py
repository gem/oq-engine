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
from openquake.baselib import sap, hdf5, parallel
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
    pnemap.start = cmaker.start
    return result


def store_poes(dstore, pnemap):
    """
    Store the pnemap of the given group inside the _poes dataset
    """
    arr = 1. - pnemap.array
    # Physically, an extremely small intensity measure level can have an
    # extremely large probability of exceedence, however that probability
    # cannot be exactly 1 unless the level is exactly 0. Numerically, the
    # PoE can be 1 and this give issues when calculating the damage (there
    # is a log(0) in
    # :class:`openquake.risklib.scientific.annual_frequency_of_exceedence`).
    # Here we solve the issue by replacing the unphysical probabilities 1
    # with .9999999999999999 (the float64 closest to 1).
    arr[arr == 1.] = .9999999999999999
    idxs, lids, gids = arr.nonzero()
    sids = pnemap.sids[idxs]
    hdf5.extend(dstore['_poes/sid'], sids)
    hdf5.extend(dstore['_poes/gid'], gids + pnemap.start)
    hdf5.extend(dstore['_poes/lid'], lids)
    hdf5.extend(dstore['_poes/poe'], arr[idxs, lids, gids])


def classical_by_gsim(calc_id: int, concurrent_tasks: int=0):
    """
    Classical calculator as postprocessor; works only for independent
    sources and ruptures.
    """
    parent = None if calc_id is None else datastore.read(calc_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    with dstore, log:
        oq = dstore.parent['oqparam']
        if concurrent_tasks:
            oq.concurrent_tasks = concurrent_tasks
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
        dstore.create_df('_poes', probability_map.poes_dt.items())
        dstore.swmr_on()
        smap = parallel.Starmap(classical_task, h5=dstore)
        csm = dstore['_csm']
        maxw = csm.get_max_weight(oq) * len(tiles)
        logging.info('num_tiles=%d, maxw=%d', len(tiles), int(maxw))
        groups = []
        for grp_id, sg in enumerate(csm.src_groups):
            sg.grp_id = grp_id
            groups.append(sg)
        for grp in sorted(groups, key=lambda grp: grp.weight, reverse=True):
            cmaker = cmakers[grp.grp_id]
            if grp.weight <= maxw:
                logging.info('Sending %s', grp)
                for tile in tiles:
                    smap.submit((grp, tile, cmaker))
            else:
                logging.info('Sending [%s] %s', len(cmaker.gsims), grp)
                for cm in cmaker.split_by_gsim():
                    for tile in tiles:
                        smap.submit((grp, tile, cm))
        for res in smap:
            store_poes(dstore, res.pop('pnemap'))


classical_by_gsim.calc_id = 'parent calculation'

if __name__ == '__main__':
    sap.run(classical_by_gsim)
