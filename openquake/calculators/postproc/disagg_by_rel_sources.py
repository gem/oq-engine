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
import pandas
from openquake.baselib import sap, hdf5, python3compat, parallel, general
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.valid import basename
from openquake.hazardlib.logictree import FullLogicTree
from openquake.hazardlib.calc import disagg
from openquake.calculators import extract


def get_mag_dist_eps_df(mean_disagg_by_src, src_mutex, src_info):
    """
    Compute mag, dist, eps, sig for each (src, imt) combination.

    :param mean_disagg_by_src:
        ArrayWrapper of rates (sid, src, mag, dst, eps, imt)
    :param src_mutex: array grp_id -> boolean
    :param src_info: source_info dataset
    :returns: a DataFrame with columns src, imt, mag, dst, eps, sig
    """
    mag = mean_disagg_by_src.mag
    dst = mean_disagg_by_src.dist
    eps = mean_disagg_by_src.eps
    dic = dict(src=[], imt=[], mag=[], dst=[], eps=[])
    grp = {}
    for src_id, grp_id in zip(src_info['source_id'], src_info['grp_id']):
        src = basename(src_id.decode('utf8'), ':;').split('!')[0]
        grp[src] = grp_id
    for s, src in enumerate(mean_disagg_by_src.source_id):
        for m, imt in enumerate(mean_disagg_by_src.imt):
            rates = mean_disagg_by_src[s, :, :, :, m]
            dic['src'].append(src)
            dic['imt'].append(imt)
            if (rates == 0).all():
                dic['mag'].append(numpy.nan)
                dic['dst'].append(numpy.nan)
                dic['eps'].append(numpy.nan)
                continue  # no contribution from this imt
            rates_mag = rates.sum((1, 2))
            rates_dst = rates.sum((0, 2))
            rates_eps = rates.sum((0, 1))
            # NB: 0=mag, 1=dist, 2=eps are the dimensions of the array
            if not src_mutex[grp[src.split('!')[0]]]:  # compute the mean
                mmag = numpy.average(mag, weights=rates_mag)
                mdst = numpy.average(dst, weights=rates_dst)
                meps = numpy.average(eps, weights=rates_eps)
            else:  # compute the mode
                mmag = mag[rates_mag.argmax()]
                mdst = dst[rates_dst.argmax()]
                meps = eps[rates_eps.argmax()]
            dic['mag'].append(mmag)
            dic['dst'].append(mdst)
            dic['eps'].append(meps)
    return pandas.DataFrame(dic)


def get_rel_source_ids(dstore, imts, imls, site_id, threshold):
    """
    :param dstore: a DataStore instance with a dataset `mean_rates_by_src`
    :param imts: a list of IMTs
    :param imls: a list of IMLs
    :param site_id: site index
    :param threshold: fraction of the max rate, used to discard sources
    :returns: dictionary IMT -> relevant source IDs
    """
    source_ids = general.AccumDict(accum=set())  # IMT -> src_ids
    for imt, iml in zip(imts, imls):
        aw = extract.extract(
            dstore, f'mean_rates_by_src?imt={imt}&iml={iml}&site_id={site_id}')
        rates = aw.array['rate']  # for each source in decreasing order
        max_rate = rates[0]
        rel = aw.array[rates > threshold * max_rate]
        srcids = numpy.unique([s.split(b'!')[0] for s in rel['src_id']])
        source_ids[imt].update(srcids)
    return source_ids


def middle(arr):
    """
    :returns: middle values of an array (length N -> N-1)
    """
    return [(m1 + m2) / 2 for m1, m2 in zip(arr[:-1], arr[1:])]


def submit_sources(dstore, csm, edges, shp, imts, imls_by_sid, oq, sites):
    smap = parallel.Starmap(disagg.disagg_source, h5=dstore.hdf5)
    rel_ids_by_imt = general.AccumDict(accum={})
    src2idx = {}  # sid, src_id -> src
    weights = {}  # sid, src_id -> weights
    for site in sites:
        sid = site.id
        lon = site.location.x
        lat = site.location.y
        imls = imls_by_sid[sid]
        dic = get_rel_source_ids(dstore, imts, imls, sid, threshold=.1)
        for imt, ids in dic.items():
            rel_ids_by_imt[sid][imt] = ids = python3compat.decode(sorted(ids))
            logging.info('(%.1f,%.1f) relevant source for %s: %s',
                         lon, lat, imt, ' '.join(ids))
        rel_ids = sorted(set.union(*map(set, rel_ids_by_imt[sid].values())))
        imldic = dict(zip(imts, imls))
        oq.hazard_imtls = {imt: [iml] for imt, iml in imldic.items()}
        for idx, source_id in enumerate(rel_ids):
            src2idx[source_id, sid] = idx
            smlt = csm.full_lt.source_model_lt.reduce(source_id, num_samples=0)
            gslt = csm.full_lt.gsim_lt.reduce(smlt.tectonic_region_types)
            weights[source_id, sid] = [rlz.weight[-1] for rlz in gslt]
            relt = FullLogicTree(smlt, gslt)
            Z = relt.get_num_paths()
            assert Z, relt  # sanity check
            groups = relt.reduce_groups(csm.src_groups)
            assert groups, 'No groups for %s' % source_id
            rupts = sum(src.num_ruptures for g in groups for src in g)
            logging.info('(%.1f,%.1f) source %s (%d rlzs, %d rupts)',
                         lon, lat, source_id, Z, rupts)
            for args in disagg.gen_disagg_source(
                    groups, site, relt, (edges, shp), oq):
                smap.submit(args)
    return smap, rel_ids_by_imt, src2idx, weights


def collect_results(smap, src2idx, weights, edges, shp,
                    rel_ids_by_imt, imts, imls_by_imt):
    """
    :returns: sid -> (mean_disagg_by_src, sigma_by_src)
    """
    out = {}
    mags, dists, _lons, _lats, eps, _trts = edges
    mag, dist, ep = middle(mags), middle(dists), middle(eps)
    for sid in sorted(rel_ids_by_imt):
        rel_ids = sorted(set.union(*map(set, rel_ids_by_imt[sid].values())))
        Ns, M = len(rel_ids), len(imts)
        zrates = numpy.zeros((Ns, shp['mag'], shp['dist'], shp['eps'], M))
        zstd = numpy.zeros((Ns, shp['mag'], shp['dist'], M))
        dic = dict(
            shape_descr=['source_id', 'mag', 'dist', 'eps', 'imt'],
            source_id=rel_ids, mag=mag, dist=dist,
            eps=ep, imt=imts, iml=imls_by_imt[sid])
        mean_disagg_by_src = hdf5.ArrayWrapper(zrates, dic)
        dic2 = dict(
            shape_descr=['source_id', 'mag', 'dist', 'imt'],
            source_id=rel_ids, imt=imts, mag=mag, dist=dist)
        sigma_by_src = hdf5.ArrayWrapper(zstd, dic2)
        out[sid] = (mean_disagg_by_src, sigma_by_src)
    disaggs = general.AccumDict(accum=[])
    for dic in smap:
        disaggs[dic['source_id'], dic['sid']].append(dic)
    for (source_id, sid), dics in disaggs.items():
        idx = src2idx[source_id, sid]
        mean_disagg_by_src, sigma_by_src = out[sid]
        for dic in dics:
            mean_disagg_by_src[idx] += dic['rates4D']
        G = len(weights[source_id, sid])  # gsim weights
        std4D = disagg.collect_std(dics, shp['mag'], shp['dist'], M, G)
        sigma_by_src[idx] += std4D @ weights[source_id, sid]
        # the dot product change the shape from (Ma, D, M, G) -> (Ma, D, M)
    return out


# tested in LogicTreeTestCase::test_case_05, case_07, case_12
def main(dstore, csm, imts, imls_by_sid):
    """
    Compute and store the mean disaggregation by Mag_Dist_Eps for
    each relevant source in the source model. Assume there is a single site.

    :param dstore: a DataStore instance
    :param csm: a CompositeSourceModel instance
    :param imts: a list of IMTs (subset of the IMTs in the job.ini)
    :param imls_by_sid: a dictionary site ID -> IMLs
    """
    oq = dstore['oqparam']
    for imt in imts:
        if imt not in oq.imtls:
            raise InvalidFile('%s: %s is not a known IMT' %
                              (oq.inputs['job_ini'], imt))

    parent = dstore.parent or dstore
    oq.mags_by_trt = {trt: python3compat.decode(dset[:])
                      for trt, dset in parent['source_mags'].items()}
    sitecol = parent['sitecol']
    sites = [site for site in sitecol if site.id in imls_by_sid]
    src_mutex = [sg.src_interdep == 'mutex' for sg in csm.src_groups]
    edges, shp = disagg.get_edges_shapedic(oq, sitecol)
    smap, rel_ids_by_imt, src2idx, weights = submit_sources(
        dstore, csm, edges, shp, imts, imls_by_sid, oq, sites)
    out = collect_results(
        smap, src2idx, weights, edges, shp, rel_ids_by_imt, imts, imls_by_sid)
    dstore.close()
    dstore.open('r+')
    # replace mean_disagg_by_src with mag_dist_eps in the output
    for site in sites:
        mean_disagg_by_src, sigma_by_src = out[site.id]
        dstore[f'mean_disagg_by_src/{site.id}'] = mean_disagg_by_src
        dstore[f'sigma_by_src/{site.id}'] = sigma_by_src
        mag_dist_eps = get_mag_dist_eps_df(
            mean_disagg_by_src, src_mutex, dstore['source_info'])
        dfs = []
        for imt, src_ids in rel_ids_by_imt[site.id].items():
            df = mag_dist_eps[mag_dist_eps.imt == imt]
            dfs.append(df[numpy.isin(df.src, src_ids)])
        mag_dist_eps_df = pandas.concat(dfs)
        logging.info('(%.1f,%.1f) mag_dist_eps=\n%s',
                     site.location.x, site.location.y, mag_dist_eps_df)
        out[site.id] = mag_dist_eps_df.to_numpy(), sigma_by_src
    return out


if __name__ == '__main__':
    sap.run(main)
