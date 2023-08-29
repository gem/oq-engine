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
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.contexts import basename
from openquake.hazardlib.logictree import FullLogicTree
from openquake.hazardlib.calc import disagg
from openquake.calculators import extract


def get_rel_source_ids(dstore, imts, imls, threshold=.1):
    """
    :returns: sorted list of relevant source IDs
    """
    source_ids = set()
    for imt, iml in zip(imts, imls):
        aw = extract.extract(
            dstore, f'mean_rates_by_src?imt={imt}&iml={iml}')
        rates = aw.array['rate']  # for each source in decreasing order
        max_rate = rates[0]
        rel = aw.array[rates > threshold * max_rate]
        source_ids.update(rel['src_id'])
    return python3compat.decode(sorted(source_ids))


def middle(arr):
    """
    :returns: middle values of an array (length N -> N-1)
    """
    return [(m1 + m2) / 2 for m1, m2 in zip(arr[:-1], arr[1:])]


def main(dstore, csm, imts, imls):
    """
    Compute and store the mean disaggregation by Mag_Dist_Eps for
    each relevant source in the source model
    """
    oq = dstore['oqparam']
    for imt in imts:
        if imt not in oq.imtls:
            raise InvalidFile('%s: %s is not a known IMT' %
                              (oq.inputs['job_ini'], imt))
    # oq.cachedir = datastore.get_datadir()
    parent = dstore.parent or dstore
    oq.mags_by_trt = {
                trt: python3compat.decode(dset[:])
                for trt, dset in parent['source_mags'].items()}
    sitecol = parent['sitecol']
    assert len(sitecol) == 1, sitecol
    edges, shp = disagg.get_edges_shapedic(oq, sitecol)
    if 'mean_rates_by_src' in parent:
        rel_ids = get_rel_source_ids(parent, imts, imls, threshold=.1)
    else:
        rel_ids = get_rel_source_ids(dstore, imts, imls, threshold=.1)
    logging.info('There are %d relevant sources: %s',
                 len(rel_ids), ' '.join(rel_ids))
    imls = numpy.array(imls)

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
        smap.submit((groups, sitecol, relt, (edges, shp), oq, imts, imls))
    mags, dists, lons, lats, eps, trts = edges
    arr = numpy.zeros(
        (len(rel_ids), shp['mag'], shp['dist'], shp['eps'], shp['M']))
    for srcid, rates4D, rates2D in smap:
        idx = src2idx[basename(srcid, '!;')]
        arr[idx] = disagg.to_probs(rates4D)
    dic = dict(
        shape_descr=['source_id', 'mag', 'dist', 'eps', 'imt'],
        source_id=rel_ids, imt=imts, iml=imls,
        mag=middle(mags), dist=middle(dists), eps=middle(eps))
    dstore['mean_disagg_by_src'] = hdf5.ArrayWrapper(arr, dic)


if __name__ == '__main__':
    sap.run(main)
