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
from openquake.baselib import sap, general
from openquake.hazardlib import contexts, calc
from openquake.commonlib import datastore
from openquake.calculators.extract import extract


def get_srcids(dstore, rel_source_ids):
    """
    :param rel_source_ids: relevant source IDs
    :returns: a dictionary source_id -> [source indices]
    """
    all_source_ids = dstore['source_info']['source_id']
    out = general.AccumDict(accum=[])  # source_id -> src_ids
    for src_id, source in enumerate(all_source_ids):
        for source_id in rel_source_ids:
            if source_id == source or (source.startswith(source_id)
                                       and source[len(source_id)] in ':;'):
                out[source_id].append(src_id)
    return out

def get_rel_source_ids(dstore, imts, poe):
    """
    :returns: sorted list of relevant source IDs
    """
    source_ids = set()
    for imt in imts:
        aw = extract(dstore, f'disagg_by_src?imt={imt}&poe={poe}')        
        poes = aw.array['poe']  # for each source in decreasing order
        max_poe = poes[0]
        source_ids.update(aw.array[poes > .1 * max_poe]['source_id'])
    return sorted(source_ids)

            
def main(parent_id, *imts):
    """
    :param parent_id: filename or ID of the parent calculation
    :param imts: list of IMTs to consider
    """
    parent = datastore.read(parent_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    with dstore, log:
        oq = parent['oqparam']
        sitecol = parent['sitecol']
        assert len(sitecol) == 1, sitecol
        for imt in imts:
            assert imt in oq.imtls, imt
        cmakers = contexts.read_cmakers(parent)
        ctx_by_grp = contexts.read_ctx_by_grp(dstore)
        n = sum(len(ctx) for ctx in ctx_by_grp.values())
        logging.info('Read {:_d} contexts'.format(n))
        rel_source_ids = get_rel_source_ids(dstore, imts, poe)
        srcids = get_srcids(dstore, rel_source_ids)
        bin_edges, shapedic = calc.disagg.get_edges_shapedic(oq, sitecol)
        for rel_id in rel_source_ids:
            for grp_id, ctx in ctx_by_grp.items():
                cmaker = cmakers[grp_id]
                ctxt = ctx[numpy.isin(ctx.src_id, srcids[rel_id])]
                if len(ctxt):
                    continue
                dis = calc.disagg.Disaggregator(ctxt, sitecol, cmaker,
                                                bin_edges, imts)
                dis.disagg_mag_dist_eps(iml3)
                

if __name__ == '__main__':
    sap.run(main)
