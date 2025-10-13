# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

import logging
from openquake.baselib import parallel, python3compat
from openquake.baselib.general import groupby
from openquake.hazardlib.contexts import read_cmakers
from openquake.hazardlib.calc.gmf import exp
from openquake.hazardlib.valid import basename


def calc_med_gmv(src_frags, sitecol, cmaker, monitor):
    cmaker.init_monitoring(monitor)
    ctxs = cmaker.from_srcs(src_frags, sitecol)
    if ctxs:
        mean = cmaker.get_mean_stds(ctxs)[0]  # shape (G, M, N)
        for m, imt in enumerate(cmaker.imtls):
            mean[:, m] = exp(mean[:, m], imt!='MMI')
        gsims = [str(gsim) for gsim in cmaker.gsims]
        yield basename(src_frags[0]), mean, gsims


def main(dstore, csm):
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    cmakers = read_cmakers(dstore, csm.full_lt).to_array()
    oq.mags_by_trt = {
        trt: python3compat.decode(dset[:])
        for trt, dset in dstore['source_mags'].items()}

    # send one task per source
    allargs = []
    for grp_id, cm in enumerate(cmakers):
        sg = csm.src_groups[grp_id]
        for src_frags in groupby(sg, basename).values():
            allargs.append((src_frags, sitecol, cm))
    dstore.swmr_on()  # must come before the Starmap
    smap = parallel.Starmap(calc_med_gmv, allargs, h5=dstore.hdf5)
    n = 0
    for src_id, gmvs, gsims in smap:
        dset = dstore.create_dset(f'med_gmv/{src_id}', float, gmvs.shape)
        dset.attrs['gsims'] = gsims
        dset[:] = gmvs
        n += 1
    logging.info('Stored %d sources', n)
