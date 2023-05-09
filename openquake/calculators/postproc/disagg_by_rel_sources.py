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
from openquake.baselib import sap, hdf5, python3compat, parallel
from openquake.hazardlib.contexts import basename
from openquake.hazardlib.logictree import FullLogicTree
from openquake.hazardlib.calc import disagg
from openquake.calculators import extract


def get_rel_source_ids(dstore, imts, poes, threshold=.1):
    """
    :returns: sorted list of relevant source IDs
    """
    source_ids = set()
    for im in imts:
        for poe in poes:
            aw = extract.extract(dstore,
                                 f'mean_rates_by_src?imt={im}&poe={poe}')
            poe_array = aw.array['poe']  # for each source in decreasing order
            max_poe = poe_array[0]
            rel = aw.array[poe_array > threshold * max_poe]
            source_ids.update(rel['src_id'])
    return python3compat.decode(sorted(source_ids))


def middle(arr):
    """
    :returns: middle values of an array (length N -> N-1)
    """
    return [(m1 + m2) / 2 for m1, m2 in zip(arr[:-1], arr[1:])]


def main(dstore, csm):
    """
    Compute and store the mean disaggregatiob by Mag_Dist_Eps for
    each relevant source in the source model
    """
    oq = dstore['oqparam']
    if len(oq.poes) == 0:
        return
    # oq.cachedir = datastore.get_datadir()
    parent = dstore.parent or dstore
    oq.mags_by_trt = {
                trt: python3compat.decode(dset[:])
                for trt, dset in parent['source_mags'].items()}
    sitecol = parent['sitecol']
    assert len(sitecol) == 1, sitecol
    edges, shp = disagg.get_edges_shapedic(oq, sitecol)
    if 'mean_rates_by_src' in parent:
        rel_ids = get_rel_source_ids(parent, oq.imtls, oq.poes, threshold=.1)
    else:
        rel_ids = get_rel_source_ids(dstore, oq.imtls, oq.poes, threshold=.1)
    logging.info('There are %d relevant sources: %s',
                 len(rel_ids), ' '.join(rel_ids))

    smap = parallel.Starmap(disagg.disagg_source, h5=dstore.hdf5)
    src2idx = {}
    for idx, source_id in enumerate(rel_ids):
        src2idx[source_id] = idx
        smlt = csm.full_lt.source_model_lt.reduce(source_id, num_samples=0)
        gslt = csm.full_lt.gsim_lt.reduce(smlt.tectonic_region_types)
        relt = FullLogicTree(smlt, gslt)
        Z = relt.get_num_paths()
        assert Z, relt  # sanity check
        logging.info('Considering source %s (%d realizations)',
                     source_id, Z)
        groups = relt.reduce_groups(csm.src_groups, source_id)
        assert groups, 'No groups for %s' % source_id
        smap.submit((groups, sitecol, relt, (edges, shp), oq))
    mags, dists, lons, lats, eps, trts = edges
    arr = numpy.zeros(
        (len(rel_ids), shp['mag'], shp['dist'], shp['eps'], shp['M'], shp['P']))
    for srcid, rates5D, rates2D in smap:
        idx = src2idx[basename(srcid, '!;')]
        arr[idx] = disagg.to_probs(rates5D)
    dic = dict(
        shape_descr=['source_id', 'mag', 'dist', 'eps', 'imt', 'poe'],
        source_id=rel_ids, imt=list(oq.imtls), poe=oq.poes,
        mag=middle(mags), dist=middle(dists), eps=middle(eps))
    dstore['mean_disagg_bysrc'] = hdf5.ArrayWrapper(arr, dic)


if __name__ == '__main__':
    sap.run(main)
