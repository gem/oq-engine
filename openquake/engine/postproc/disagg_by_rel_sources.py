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

import re
import logging
import numpy
from openquake.baselib import sap, general, python3compat
from openquake.hazardlib import contexts, calc, imt
from openquake.commonlib import datastore
from openquake.calculators.extract import extract

U32 = numpy.uint32


def get_sources(dstore, rel_source_ids):
    """
    :param rel_source_ids: relevant source IDs
    :returns: a list of sources
    """
    acc = general.AccumDict(accum=[])  # source_id -> sources
    for src in dstore['_csm'].get_sources():
        source_id = re.split('[:;.]', src.source_id)[0]
        if source_id in rel_source_ids:
            acc[source_id].append(src)
    return acc


def get_rel_source_ids(dstore, imts, poes):
    """
    :returns: sorted list of relevant source IDs
    """
    source_ids = set()
    for im in imts:
        for poe in poes:
            aw = extract(dstore, f'disagg_by_src?imt={im}&poe={poe}')
            poe_array = aw.array['poe']  # for each source in decreasing order
            max_poe = poe_array[0]
            source_ids.update(aw.array[poe_array > .1 * max_poe]['src_id'])
    return python3compat.decode(sorted(source_ids))


def compute_disagg(source_id, dis, gsim_weights):
    pmap = dis.cmaker.get_pmap([dis.fullctx])
    [iml3] = pmap.interp4D(dis.cmaker.imtls, dis.cmaker.poes)
    mat5D = dis.disagg_mag_dist_eps(iml3) @ gsim_weights
    return {source_id: mat5D}  # shape (Ma, D, E, M, P)


def main(parent_id, imts=['PGA']):
    """
    :param parent_id: filename or ID of the parent calculation
    :param imts: list of IMTs to consider
    """
    try:
        parent_id = int(parent_id)
    except ValueError:
        pass
    parent = datastore.read(parent_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    with dstore, log:
        oq = parent['oqparam']
        oq.mags_by_trt = parent['source_mags']
        sitecol = parent['sitecol']
        assert len(sitecol) == 1, sitecol
        gsim_lt = parent['full_lt/gsim_lt']
        gsim_weights = [br.weight['weight'] for br in gsim_lt.branches]
        assert len(sitecol) == 1, sitecol
        for im in imts:
            assert im in oq.imtls, im
        imtls = general.DictArray({im: oq.imtls[im] for im in imts})

        logging.info('Reading CompositeSourceModel')
        rel_source_ids = get_rel_source_ids(parent, imts, oq.poes)
        bin_edges, shapedic = calc.disagg.get_edges_shapedic(oq, sitecol)
        mat_by_src = {}
        for source_id, srcs in get_sources(parent, rel_source_ids).items():
            trt = srcs[0].tectonic_region_type
            rlzs_by_gsim = {
                gsim: [g] for g, gsim in enumerate(gsim_lt.values[trt])}
            cmaker = contexts.ContextMaker(trt, rlzs_by_gsim, oq)
            cmaker.imtls = imtls
            ctxs = cmaker.from_srcs(srcs, sitecol)
            dis = calc.disagg.Disaggregator(
                ctxs, sitecol, cmaker, bin_edges, imts)
            mat_by_src.update(compute_disagg(source_id, dis, gsim_weights))



if __name__ == '__main__':
    sap.run(main)
