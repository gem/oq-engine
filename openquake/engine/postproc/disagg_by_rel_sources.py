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
from openquake.baselib import sap, performance
from openquake.hazardlib import logictree, calc
from openquake.commonlib import datastore, readinput
from openquake.calculators.classical import get_rel_source_ids

U32 = numpy.uint32


def compute_disagg(source_id, disaggs, gsim_weights):
    for dis in disaggs:
        pmap = dis.cmaker.get_pmap([dis.fullctx])
        [iml3] = pmap.interp4D(dis.cmaker.imtls, dis.cmaker.poes)
        mat5D = dis.disagg_mag_dist_eps(iml3) @ gsim_weights
    return {source_id: mat5D}  # shape (Ma, D, E, M, P)


def main(parent_id):
    """
    :param parent_id: filename or ID of the parent calculation
    """
    try:
        parent_id = int(parent_id)
    except ValueError:
        pass
    parent = datastore.read(parent_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    with dstore, log:
        oq = parent['oqparam']
        oq.cachedir = datastore.get_datadir()
        oq.mags_by_trt = parent['source_mags']
        sitecol = parent['sitecol']
        assert len(sitecol) == 1, sitecol
        full_lt = readinput.get_full_lt(oq)
        csm = parent['_csm']
        csm.init(full_lt)
        mon = performance.Monitor(
            'building disaggs', measuremem=True, h5=dstore.hdf5)
        bin_edges, shapedic = calc.disagg.get_edges_shapedic(oq, sitecol)
        rel_ids = get_rel_source_ids(
            parent, oq.imtls, oq.poes, threshold=.1)
        for source_id in rel_ids:
            logging.info('Disaggregating source %s', source_id)
            smlt = full_lt.source_model_lt.reduce(source_id)
            gslt = full_lt.gsim_lt.reduce(smlt.tectonic_region_types)
            relt = logictree.FullLogicTree(smlt, gslt, 'reduce-rlzs')
            groups = calc.disagg.reduce_groups(csm.src_groups, source_id)
            with mon:
                disaggs = calc.disagg.by_source(
                    relt, groups, sitecol, bin_edges, oq)


if __name__ == '__main__':
    sap.run(main)
