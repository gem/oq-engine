# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
Experimental command to run a partial disaggregation calculation. It will be
removed soon.
"""
from __future__ import print_function
import logging
import math
from openquake.baselib import sap, datastore, parallel, performance
from openquake.baselib.general import split_in_blocks
from openquake.commonlib import readinput
from openquake.hazardlib import sourceconverter, gsim
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.disagg import collect_bins_data, build_ql


def save_bin_data(dstore, bdata):
    trt = bdata.trt
    for key in ('mags', 'dists', 'lons', 'lats', 'eps'):
        dskey = 'bindata/%s/%s' % (trt, key)
        data = getattr(bdata, key)
        if len(data):
            dstore.extend(dskey, data)
    return dstore


@sap.Script
def collect_bins(job_ini):
    """
    Run the first part of a disaggregation calculation
    """
    logging.basicConfig(level=logging.INFO)
    oq = readinput.get_oqparam(job_ini)
    assert oq.iml_disagg, 'Not implemented'
    dstore = datastore.DataStore()
    dstore['oqparam'] = oq
    tl = oq.truncation_level
    sitecol = readinput.get_site_collection(oq)

    all_args = []
    src_filter = SourceFilter(sitecol, oq.maximum_distance)
    csm = readinput.get_composite_source_model(oq).filter(src_filter)
    num_grps = sum(1 for sg in csm.src_groups)
    nblocks = math.ceil(oq.concurrent_tasks / num_grps)

    # build trt_edges
    trts = tuple(sorted(set(sg.trt for smodel in csm.source_models
                            for sg in smodel.src_groups)))
    trt_num = dict((trt, i) for i, trt in enumerate(trts))

    mon = performance.Monitor('disaggregation', dstore.hdf5path)

    # collect arguments
    for smodel in csm.source_models:
        for sg in smodel.src_groups:
            split_sources = []
            for src in sg:
                for split, _sites in src_filter(
                        sourceconverter.split_source(src), sitecol):
                    split_sources.append(split)
            if not split_sources:
                continue

            gsims = csm.info.gsim_lt.values[sg.trt]
            cmaker = gsim.base.ContextMaker(
                gsims, src_filter.integration_distance)
            quartets, levels = build_ql({gs: [0] for gs in gsims}, oq.imtls)
            for srcs in split_in_blocks(split_sources, nblocks):
                all_args.append(
                    (trt_num, srcs, sitecol, cmaker, quartets, levels,
                     tl, oq.num_epsilon_bins, mon))

    parallel.Starmap(collect_bins_data, all_args).reduce(
        save_bin_data, dstore)
    # setting nbytes
    for trt in dstore['bindata']:
        key = 'bindata/' + trt
        for k in dstore[key]:
            dstore.set_nbytes('%s/%s' % (key, k))
        dstore.set_nbytes(key)
    dstore.set_nbytes('bindata')
    print('See hdfview %s' % dstore.hdf5path)

collect_bins.arg('job_ini', 'calculation configuration file')
