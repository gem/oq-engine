# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2022, GEM Foundation
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

import toml
import logging
import numpy
from openquake.baselib import sap, parallel, performance, general
from openquake.hazardlib.calc.mrd import calc_mean_rate_dist
from openquake.hazardlib import contexts, cross_correlation
from openquake.commonlib import datastore


def compute_mrd(dstore, slc, cmaker, crosscorr, imt1, imt2,
                meabins, sigbins, monitor):
    """
    :param dstore: parent datastore
    :param slc: a slice object referring to a slice of contexts
    :param cmaker: a ContextMaker instance
    :param crosscorr: cross correlation model
    :param str imt1: the first Intensity Measure Type
    :param str imt1: the second Intensity Measure Type
    :param meabins: bins for the means
    :param sigbins: bins for the sigmas
    :returns: 4D-matrix with shape (L1, L1, N, G)
    """
    with dstore:
        [ctx] = cmaker.read_ctxs(dstore, slc)
    mrd = calc_mean_rate_dist(ctx, cmaker, crosscorr,
                              imt1, imt2, meabins, sigbins)
    return {g: mrd[:, :, :, g - cmaker.start]
            for g in range(cmaker.start, cmaker.stop)}


def combine_mrds(acc, rlzs_by_g, rlz_weight):
    g = next(iter(acc))  # first key
    out = numpy.zeros(acc[g].shape)  # shape (L1, L1, N)
    for g in acc:
        value = acc[g]
        for rlz in rlzs_by_g[g]:
            out += rlz_weight[rlz] * value
    return out


def main(parent_id:int, config):
    """
    :param parent_id: ID of the parent calculation with the contexts
    :param config: name of a .toml file with parameters imt1, imt2, crosscorr

    NB: this is meant to work only for parametric ruptures!
    """
    parent = datastore.read(parent_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    with open(config) as f:
        dic = toml.load(f)
    imt1 = dic['imt1']
    imt2 = dic['imt2']
    crosscorr = getattr(cross_correlation, dic['cross_correlation'])()
    meabins = dic['meabins']
    sigbins = dic['sigbins']
    with dstore, log:
        oq = parent['oqparam']
        N = len(parent['sitecol'])
        L1 = oq.imtls.size // len(oq.imtls) - 1
        assert L1 <= 24, 'Too many levels: %d' % L1
        assert N <= 10, 'Too many sites: %d' % N
        cmakers = contexts.read_cmakers(parent)
        grp_ids = dstore.parent['rup/grp_id'][:]
        logging.info('Read {:_d} contexts'.format(len(grp_ids)))
        blocksize = numpy.ceil(len(grp_ids) / oq.concurrent_tasks)
        dstore.swmr_on()
        smap = parallel.Starmap(compute_mrd, h5=dstore)
        for grp_id, slices in performance.get_slices(grp_ids).items():
            cmaker = cmakers[grp_id]
            for s0, s1 in slices:
                for slc in general.gen_slices(s0, s1, blocksize):
                    smap.submit((parent, slc, cmaker, crosscorr, imt1, imt2,
                                 meabins, sigbins))
        acc = smap.reduce()
        mrd = dstore.create_dset('_mrd', float, (L1, L1, N))
        mrd[:] = combine_mrds(
            acc, dstore['rlzs_by_g'][:], dstore['weights'][:])


if __name__ == '__main__':
    sap.run(main)
